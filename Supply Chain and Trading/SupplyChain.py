import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import networkx as nx
from google_distance import compute_distance
from trading_opt import optimize

# Firebase Admin SDK Initialization
cred = credentials.Certificate('firebase_auth_token/alginnova-f177f-firebase-adminsdk-1hr5k-b3cac9ea17.json')
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

    def add_location(self, location_id, address, id, type):
        # Add a new location to the Firestore database, type is either port, farm or warehouse
        location_ref = self.db.collection('locations').document(id)
        location_ref.set({'address': address, 'location_id': location_id, 'type': type})
        print(f"Location {location_id} added with address: {address}")

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
        
    def fill_demand(self, SCN, customer_id, weight_required):
        customer_ref = self.db.collection('customers').document(customer_id)
        customer = customer_ref.get()
        if not customer.exists:
            print(f"No customer found with ID {customer_id}")
            return

        customer_data = customer.to_dict()
        demanded_species = customer_data.get('demand_species')
        location_id = customer.get("location_id")

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
        results = optimize(SCN, demanded_batches, location_id, weight_required)

        return results

    def connect_customer_to_network(self, address, location_id):
        # Logic to connect the customer location to other relevant nodes in the SCN

        existing_node = None
        for node in self.SCN.nodes:
            if node == location_id:
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
                    cost = self.compute_cost(address, location_address)
                    self.SCN.add_edge(customer_node, location, weight=cost)
                    self.SCN.add_edge(location, customer_node, weight=cost)

    def store_network(self):
        return 0

    def read_network(self):
        self.SCN = stored_SCN
