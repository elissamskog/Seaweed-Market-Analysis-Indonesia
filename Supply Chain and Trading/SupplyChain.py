import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import networkx as nx
from networkx.readwrite import json_graph
from google_distance import compute_distance
#from trading_opt import Optimize
import json

cred = credentials.Certificate("C:/Users/August/alginnova_jobb/firebaseAPI/firebase_auth_token/alginnova-f177f-firebase-adminsdk-1hr5k-b3cac9ea17.json")
firebase_admin.initialize_app(cred)

class SupplyChain:
    def __init__(self):
        # Firebase Admin SDK Initialization
        
        self.db = firestore.client()
        
    def build_network_graph(self, destinations):
        # Initialize directed graph
        G = nx.DiGraph()

        # Fetch all locations and filter for transport locations
        locations = list(self.db.collection('Locations').stream())  # Convert query to list
        transport_locations = []
        ports = []
        
        # Define a helper function to filter transport locations
        def is_transport_location(location):
            return location.get('type') not in ['customer', 'seller', 'farm']

        # Process locations
        for location in locations:
            if is_transport_location(location):
                location_id = location.id
                G.add_node(location_id, type=location.get('type'), island=location.get('island'))
                transport_locations.append(location)
                if location.get('type') == 'port':  # Check if the location is a port
                    ports.append(location)  # Add to the ports list
                

        # Add sink nodes from destinations
        for destination_id in destinations:
            destination_doc = self.db.collection('Locations').document(destination_id).get()
            destination_data = destination_doc.to_dict()
            G.add_node(destination_id, type='sink', island=destination_data.get('island'))

        # Connect all locations to each other, bidirectionally
        for i, loc1 in enumerate(transport_locations):
            for loc2 in transport_locations[i+1:]:
                # Check if both are ports, then connect them
                if loc1.get('type') == 'port' and loc2.get('type') == 'port':
                    G.add_edge(loc1.id, loc2.id)
                    G.add_edge(loc2.id, loc1.id)
                # If neither is a port, connect them bidirectionally
                elif loc1.get('type') != 'port' and loc2.get('type') != 'port':
                    G.add_edge(loc1.id, loc2.id)
                    G.add_edge(loc2.id, loc1.id)
                # If one is a port and the other is not, do not connect them

       # Process sellers to fetch batches
        sellers = list(self.db.collection('Sellers').stream())
        all_batches = []
        for seller in sellers:
            # Fetch batches from the 'Batches' subcollection for each seller
            batches = list(self.db.collection('Sellers').document(seller.id).collection('Batches').stream())
            for batch in batches:
                batch_id = batch.id
                batch_data = batch.to_dict()  # Convert to dict to access data

                # Fetch the location document using the location_id from the batch
                location_id = batch_data.get('location_id')
                if location_id:
                    location_doc = self.db.collection('Locations').document(location_id).get()
                    if location_doc.exists:
                        island = location_doc.to_dict().get('island')  # Extract the island information
                    
                        # Ensure island information is available before proceeding
                        if island:
                            # Now you have the island information; you can add the batch node with this info
                            all_batches.append({'id': batch.id, 'location_id': location_id, 'island': island})
                            G.add_node(batch_id, type='batch', island=island)
                            
                            for batch in all_batches:
                                for other_batch in [ob for ob in all_batches if ob['id'] != batch['id'] and ob['island'] == batch['island']]:
                                    G.add_edge(batch['id'], other_batch['id'] )
                                    G.add_edge(other_batch['id'], batch['id'])

                    
                # Connect batch to locations on the same island, unidirectionally
                for seller in sellers:
                    batches = list(self.db.collection('Sellers').document(seller.id).collection('Batches').stream())
                    for batch in batches:
                        batch_id = batch.id
                        batch_data = batch.to_dict()  # Convert to dict to access data

                        # Ensure island information is available before proceeding
                        location_id = batch_data.get('location_id')
                        if location_id:
                            location_doc = self.db.collection('Locations').document(location_id).get()
                            if location_doc.exists:
                                location_data = location_doc.to_dict()
                                island = location_data.get('island')  # Extract the island information
                                if island:
                                    # Only add edge from batch to location, not vice versa
                                    for loc in [loc for loc in transport_locations if loc.get('island') == island]:
                                        G.add_edge(batch_id, loc.id)


       # Fetch customers directly from the Customers collection and add them as nodes
        customers = list(self.db.collection('Customers').stream())
        for customer_snapshot in customers:
            customer_id = customer_snapshot.id
            customer_data = customer_snapshot.to_dict()
            # Assuming you have 'island' information for customers or you can omit it
            G.add_node(customer_id, type='customer', **customer_data)

        # After adding customer nodes, connect customers bidirectionally
        for customer_snapshot in customers:
            customer_id = customer_snapshot.id
            for other_customer_snapshot in customers:
                other_customer_id = other_customer_snapshot.id
                if customer_id != other_customer_id:
                    G.add_edge(customer_id, other_customer_id)
                    G.add_edge(other_customer_id, customer_id)

        # Connect transport locations to customers unidirectionally
        for loc in transport_locations:
            # Skip if the location is a port
            if loc.get('type') == 'port':
                continue
            
            for customer_snapshot in customers:
                customer_id = customer_snapshot.id
                # Add edge from location to customer, ensuring it's unidirectional
                G.add_edge(loc.id, customer_id)

        self.SCN = G
        self.build_edges()  # Ensure this method is updated for bidirectional and cost estimation logic
        
    def build_edges(self):
        # Fetch routes from Firestore
        routes = list(self.db.collection('Routes').stream())

        # Process each route and update edges in the graph
        for route_snapshot in routes:
            route = route_snapshot.to_dict()  # Convert document snapshot to dict
            from_location = route['from']
            to_location = route['to']

            # Ensure route data contains necessary fields
            if 'type' in route and 'costs' in route:
                route_type = route['type']
                costs = route['costs']

                # Update edge with route data if edge exists
                if self.SCN.has_edge(from_location, to_location):
                    self.SCN[from_location][to_location]['type'] = route_type
                    self.SCN[from_location][to_location]['costs'] = costs
                # If no direct route exists, check for and use data from reverse route if it exists
                elif self.SCN.has_edge(to_location, from_location):
                    reverse_edge_data = self.SCN[to_location][from_location]
                    self.SCN.add_edge(from_location, to_location, type=reverse_edge_data['type'], costs=reverse_edge_data['costs'])
                # Calculate and add estimated costs if no direct or reverse route exists
                else:
                    # Placeholder for address retrieval and distance calculation
                    from_address_doc = self.db.collection('Locations').document(from_location).get()
                    to_address_doc = self.db.collection('Locations').document(to_location).get()
                    if from_address_doc.exists and to_address_doc.exists:
                        from_address = from_address_doc.to_dict().get('address')
                        to_address = to_address_doc.to_dict().get('address')
                        # Compute distance and estimated costs (assuming compute_distance is defined)
                        distance = self.compute_distance(from_address, to_address)
                        estimated_costs = self.calculate_estimated_costs(distance)  
                        # Update edge with estimated costs
                        self.SCN.add_edge(from_location, to_location, type='estimated', costs=estimated_costs)

    def min_transport_cost(self, destinations):
        '''destinations contains the id of the location document'''

        # Build the network
        self.build_network_graph(destinations)

        # Initialize a dictionary to hold all demanded batches and orders
        batches = {}
        orders = {}  # To store orders indexed by customer location, only including species and quantity

        for destination_id in destinations:
            location_doc = self.db.collection('locations').document(destination_id).get()
            location_data = location_doc.to_dict()
            location_type = location_data.get('type')

            if location_type == 'customer':
                # Fetch active orders for this customer
                orders_ref = self.db.collection('customers').document(destination_id).collection('Orders')
                orders_docs = orders_ref.where('active', '==', True).stream()

                for order_doc in orders_docs:
                    order_data = order_doc.to_dict()
                    # Extract only species and quantity
                    orders[destination_id] = {
                        'species': order_data.get('species'),
                        'quantity': order_data.get('quantity'),
                        'location': destination_id
                    }

            else:
                # Fetch sink value for non-customer locations
                sink_ref = self.db.collection('Internal Sink Collection').document(destination_id).collection('Sink Values')
                sink_docs = sink_ref.stream()

                for sink_doc in sink_docs:
                    sink_data = sink_doc.to_dict()
                    # Extract only species and quantity
                    orders[destination_id] = {
                        'species': sink_data.get('species'),
                        'quantity': sink_data.get('quantity'),
                        'location': destination_id
                    }

        # Fetch active batches from all sellers
        sellers_ref = self.db.collection('sellers')
        sellers_docs = sellers_ref.stream()

        for seller_doc in sellers_docs:
            seller_data = seller_doc.to_dict()
            seller_location_id = seller_data.get('location_id')

            # Fetch active batches for each seller
            batches_ref = seller_doc.reference.collection('Batches')
            batches_docs = batches_ref.where('active', '==', True).stream()

            for batch_doc in batches_docs:
                batch_data = batch_doc.to_dict()
                batch_id = batch_doc.id
                batch_weight = batch_data.get('weight')
                batch_volume = batch_data.get('volume')

                # Add batch data to batches
                batches[batch_id] = {
                    'weight': batch_weight,
                    'volume': batch_volume,
                    'location': seller_location_id,
                    'species': batch_data.get('species')  # Add species information
                }

        # Optimize transportation costs with all available batches and orders
        results = Optimize(self.SCN, batches, orders)
        optimized_results = results.results

        # Process and return results
        return optimized_results

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



