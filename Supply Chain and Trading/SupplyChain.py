import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import networkx as nx
from networkx.readwrite import json_graph
from google_distance import compute_distance
from trading_opt import optimize
import json


# Firebase Admin SDK Initialization
#cred = credentials.Certificate('firebase_auth_token/alginnova-f177f-firebase-adminsdk-1hr5k-b3cac9ea17.json')
cred = credentials.Certificate("C:/Users/August/alginnova_jobb/firebaseAPI/firebase_auth_token/alginnova-f177f-firebase-adminsdk-1hr5k-b3cac9ea17.json")
firebase_admin.initialize_app(cred)

# Firestore client instance
db = firestore.client()

class SupplyChain():
    def __init__(self):
        self.db = db

    def update_shelf_life(self):
        batches_ref = self.db.collection('batches')
        batches = batches_ref.stream()
        batch = self.db.batch()

        for batch_doc in batches:
            shelf_life = batch_doc.get('shelf_life')
            if shelf_life and shelf_life > 0:
                new_shelf_life = shelf_life - 1
                batch.update(batch_doc.reference, {'shelf_life': new_shelf_life})

        batch.commit()
        print("Shelf life updated for all batches in batch write")

    def add_location(self, location_id, address, id, type): # Spara med bättre Document ID?
        # Add a new location to the Firestore database, type is either port, farm or warehouse
        location_ref = self.db.collection('locations').document(id)
        location_ref.set({'address': address, 'location_id': location_id, 'type': type})
        print(f"Location {location_id} added with address: {address}")

         # Rebuild the SCN object with the new location included
        self.build_network_graph()

        # Store the updated SCN object in Firestore
        self.store_network()

    def add_route(self, from_location, to_location, quantity_tiers, type):
        # Add a new route to the Firestore database, quantity_tiers is a dictionary with tiers of cost for each quantity tier
        # type is the type of quantity tier being used, either volume or weight
        route_id = f"{from_location}-{to_location}"
        route_doc = {
            'from': from_location,
            'to': to_location,
            'type': type,
            'cost': quantity_tiers
        }
        self.db.collection('routes').document(route_id).set(route_doc)
        print(f"Route from {from_location} to {to_location} added")

        # Rebuild the SCN object with the new route included
        self.build_network_graph()

        # Store the updated SCN object in Firestore
        self.store_network()

    def add_batch(self, batch_id, batch_data):
        # Add a new batch to the 'batches' collection
        batch_ref = self.db.collection('batches').document(batch_id)
        batch_ref.set(batch_data)
        print(f"Batch {batch_id} added")

    def move_batch(self, batch_id, to_location_id):
        # Move a batch to a new location
        batch_ref = self.db.collection('batches').document(batch_id)
        batch_data = batch_ref.get().to_dict()
        if batch_data:
            batch_data['location'] = to_location_id
            batch_ref.set(batch_data)
            print(f"Batch {batch_id} moved to {to_location_id}")
        else:
            print(f"Batch {batch_id} not found")

    def update_route(self, from_location, to_location, new_cost_tiers):
        # Update an existing route with new cost and volume data
        route_id = f"{from_location}-{to_location}"
        route_ref = self.db.collection('routes').document(route_id)
        route_ref.update({'cost': new_cost_tiers})
        print(f"Route from {from_location} to {to_location} updated")

    def add_customer(self, customer_id, quantity_required, address, species, location_id):
        # Add a new customer to the Firestore database with the required details
        customer_data = {
            'quantity_required': quantity_required,
            'address': address,
            'location_id': location_id,
            'species': species
        }
        customer_ref = self.db.collection('customers').document(customer_id)
        customer_ref.set(customer_data)
        print(f"Customer {customer_id} added with quantity required: {quantity_required} and address: {address}")

        # Connect the customer to the networkX object
        self.connect_customer_to_network(address, location_id, customer_id)

    def build_network_graph(self):
        G = nx.Graph()

        # Fetch locations and their addresses
        locations_ref = self.db.collection('locations')
        locations = locations_ref.stream()
        for location in locations:
            location_data = location.to_dict()
            city_island = location_data.get('location_id', '')  # city.island format
            address = location_data.get('address', '')

            # Add a node for each unique city.island, using the first instance's data
            if city_island not in G:
                G.add_node(city_island, address=address)

        # Process routes
        routes = self.db.collection('routes').stream()
        for route in routes:
            route_data = route.to_dict()
            from_loc = route_data['from']  # These should also be in city.island format
            to_loc = route_data['to']
            route_type = route_data.get('type', 'volume')
            edge_data = {'type': route_type, 'costs': route_data['costs']}
            G.add_edge(from_loc, to_loc, **edge_data)

        # Add intra-island transportation costs
        for loc1 in G.nodes:
            addr1 = G.nodes[loc1]['address']
            for loc2 in G.nodes:
                if loc1 != loc2 and loc1.split('.')[-1] == loc2.split('.')[-1]:
                    addr2 = G.nodes[loc2]['address']
                    distance = compute_distance(addr1, addr2)
                    costs = {}
                    for weight in [10, 30]:
                        cost = (distance * 0.48 + 121) * weight / 10
                        costs[f"{weight}kg"] = cost
                    edge_data = {'type': 'weight', 'costs': costs}
                    G.add_edge(loc1, loc2, **edge_data)
                    G.add_edge(loc2, loc1, **edge_data)

        self.SCN = G
       
        
    def fill_demand(self, customer_id, weight_required):
        # Load the most current state of the SCN
        self.read_network()

        # Now the SCN is updated, connect the customer to the network
        # Assuming the method signature of connect_customer_to_network is (self, address, location_id, customer_id)
        # And assuming you have the customer's address and location_id available
        # You might need to fetch these details from Firestore if not already available in the method call
        customer_ref = self.db.collection('customers').document(customer_id)
        customer_doc = customer_ref.get()
        if customer_doc.exists:
            customer_data = customer_doc.to_dict()
            self.connect_customer_to_network(customer_data['address'], customer_data['location_id'], customer_id)
        else:
            print(f"No customer found with ID {customer_id}")
            return

        customer_data = customer_doc.to_dict()
        demanded_species = customer_data.get('demand_species')
        location_id = customer_doc.get("location_id")

        # Fetch batches that match the demanded species
        demanded_batches = {}
        batches_ref = self.db.collection('batches')
        matching_batches = batches_ref.where('species', '==', demanded_species).stream()

        for batch in matching_batches:
            batch_data = batch.to_dict()
            if batch_data['quantity'] > 0:  # Ensure the batch has available quantity
                demanded_batches[batch.id] = {
                    'location': batch_data['location'],
                    'weight': batch_data['weight'],
                    'volume': batch_data['volume'],
                    'quantity': batch_data['quantity']
                }

        # Optimize transportation costs
        results = optimize(self.SCN, demanded_batches, location_id, weight_required)

        return results

    def connect_customer_to_network(self, address, location_id):
        # Logic to connect the customer location to other relevant nodes in the SCN

        existing_node = None
        for node in self.SCN.nodes:
            if node == location_id.endswith(node):
                existing_node = node
                break

        # If an existing node is found, use it; otherwise, add a new node for the customer
        if existing_node:
            customer_node = existing_node
        else:
            customer_node = location_id
            self.SCN.add_node(location_id)
            # Connect the customer node to other nodes on the same island
            for location in self.SCN.nodes:
                if location != customer_node and location.split('.')[-1] == location_id.split('.')[-1]:
                    # Calculate transportation cost between locations
                    location_data = self.SCN.nodes[location]
                    location_address = location_data.get('address')
                    cost = self.compute_cost(address, location_address) # Change to tiers!!
                    self.SCN.add_edge(customer_node, location, weight=cost)
                    self.SCN.add_edge(location, customer_node, weight=cost)

    def store_network(self):
        # Reference to the 'networks' collection
        collection_ref = self.db.collection('networks')
        
        # Attempt to delete the existing document, assuming a single document management strategy
        for doc in collection_ref.stream():
            doc.reference.delete()
            print(f"Deleted existing document: {doc.id}")

        # Serialize the NetworkX graph to a JSON-serializable dict
        stored_SCN = nx.readwrite.json_graph.node_link_data(self.SCN)
        graph_json = json.dumps(stored_SCN)

        # Since we're assuming a single document strategy, we can use a fixed document name
        # If you want to make it dynamic or based on some attribute, adjust accordingly
        doc_name = "current_network"
        doc_ref = collection_ref.document(doc_name)  # Use a consistent document name
        doc_ref.set({'network_': graph_json})

        print(f"Graph stored in Firestore collection networks with document name {doc_name}")


    def read_network(self):
        # Fetch all documents in the 'networks' collection
        docs = self.db.collection('networks').limit(1).stream()

        # Attempt to get the first document from the iterator
        doc = next(docs, None)

        if doc:
            # Deserialize the graph data from JSON back to a dictionary
            graph_data = json.loads(doc.to_dict()['network_'])

            # Use the dictionary to recreate the NetworkX graph
            self.SCN = json_graph.node_link_graph(graph_data)

            print(f"Graph successfully read and reconstructed from document {doc.id}.")
        else:
            print("No document found in the 'networks' collection.")
            self.SCN = None




### Tester ###
def test():
    supply_chain = SupplyChain()

    #supply_chain.build_network_graph()
    supply_chain.SCN = nx.Graph()

    SCN = nx.Graph()

    # Add mock locations
    supply_chain.SCN.add_node("Location_A")
    supply_chain.SCN.add_node("Location_B")
    supply_chain.SCN.add_node("Customer_Location")


    # Add mock routes with tiered costs
    supply_chain.SCN.add_edge("Location_A", "Location_B", type='weight', costs={'100': 150, '200': 250})
    supply_chain.SCN.add_edge("Location_B", "Customer_Location", type='volume', costs={'50': 100, '100': 180})

    # Add mock locations
    SCN.add_node("Location_A")
    SCN.add_node("Location_B")
    SCN.add_node("Customer_Location")

    # Add mock routes with tiered costs
    SCN.add_edge("Location_A", "Location_B", type='weight', costs={'100': 150, '200': 250})
    SCN.add_edge("Location_B", "Customer_Location", type='volume', costs={'50': 100, '100': 180})
    
    supply_chain.store_network()

    supply_chain.read_network()

    print(compare_graphs(supply_chain.SCN, SCN))

def compare_graphs(g1, g2):
    # Check for isomorphism
    if not nx.is_isomorphic(g1, g2):
        return False, "Graphs are not isomorphic."
    
    # Check node attributes
    for node in g1.nodes:
        if g1.nodes[node] != g2.nodes[node]:
            return False, f"Node attributes differ for node {node}."
    
    # Check edge attributes
    for edge in g1.edges:
        if g1.edges[edge] != g2.edges[edge]:
            return False, f"Edge attributes differ for edge {edge}."
    
    # If all checks passed
    return True, "Graphs are isomorphic and all attributes match."

# Example usage:
# g1 and g2 are your NetworkX graph objects
# is_equal, message = compare_graphs(g1, g2)
# print(message)


if __name__ == "__main__":
    test()
