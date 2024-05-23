import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import networkx as nx
from networkx.readwrite import json_graph
from google_distance import compute_distance
#from trading_opt import Optimize
import json

cred = credentials.Certificate('firebase_auth_token/alginnova-f177f-firebase-adminsdk-1hr5k-b3cac9ea17.json')
firebase_admin.initialize_app(cred)

class SupplyChain:
    def __init__(self):
        # Firebase Admin SDK Initialization
        self.db = firestore.client()
    
    def on_same_island(self, loc_id1, loc_id2):
        # Fetch the document references from the Firestore database
        doc_ref1 = self.db.collection('Locations').document(loc_id1)
        doc_ref2 = self.db.collection('Locations').document(loc_id2)
        
        # Get the documents
        doc1 = doc_ref1.get()
        doc2 = doc_ref2.get()
        
        if not doc1.exists or not doc2.exists:
            raise ValueError("One or both location IDs do not exist in the database.")
        
        # Extract the 'island' fields from the documents
        island1 = doc1.to_dict().get('island')
        island2 = doc2.to_dict().get('island')
    
        return island1 == island2

    def calculate_estimated_costs(self, distance):
        # Placeholder calculation for extimating cost for transport by truck
        return distance * 10

    def build_network_graph(self):
        # Initialize directed graph
        self.G = nx.DiGraph()

        # Fetch all locations and store them in a dictionary for easy lookup
        locations = {doc.id: doc.to_dict() for doc in self.db.collection('Locations').stream()}

        # Fetch all routes (not directly used for the rules given but could be extended to use route data)
        # routes = {doc.id: doc.to_dict() for doc in self.db.collection('Routes').stream()}

        # Add nodes for locations except customers and sellers
        for loc_id, loc_data in locations.items():
            if loc_data['type'] not in ['customer', 'seller']:
                self.G.add_node(loc_id, **loc_data)

        # Process active orders or batches for customers and sellers
            if loc_type in ['customer', 'seller']:
                subcollection_name = 'orders' if loc_type == 'customer' else 'batches'
                subdocs = self.db.collection('Locations').document(loc_id).collection(subcollection_name).where('active', '==', True).stream()

                # Add nodes for active orders or batches
                active_found = False
                for subdoc in subdocs:
                    subdoc_data = subdoc.to_dict()
                    # Check if the subdoc is active
                    if subdoc_data.get('active', False):  # This will use False as default if 'active' is not present
                        active_found = True

                if active_found:
                    # Only add the customer or seller node if there are active subdocuments
                    self.G.add_node(loc_id, **loc_data)

        
        # Now iterate over each node to apply directional edge logic
        for loc_id in list(self.G.nodes):
            loc_data = self.G.nodes[loc_id]
            loc_type = loc_data.get('type')

            for other_id in list(self.G.nodes):
                if loc_id == other_id:
                    continue  # Avoid self-loops

                other_data = self.G.nodes[other_id]
                other_type = other_data.get('type')

                # Connecting warehouses to customers (unidirectional)
                if loc_type == 'warehouse' and other_type == 'customer' and self.on_same_island(loc_id, other_id):
                    self.G.add_edge(loc_id, other_id)

                # Connecting ports to each other (bidirectional)
                elif loc_type == 'port' and other_type == 'port':
                    self.G.add_edge(loc_id, other_id)
                    self.G.add_edge(other_id, loc_id)

                # Connecting warehouses on the same island (bidirectional)
                elif loc_type == 'warehouse' and other_type == 'warehouse' and self.on_same_island(loc_id, other_id):
                    self.G.add_edge(loc_id, other_id)
                    self.G.add_edge(other_id, loc_id)

                # Connecting customers on the same island (bidirectional)
                elif loc_type == 'customer' and other_type == 'customer' and self.on_same_island(loc_id, other_id):
                    self.G.add_edge(loc_id, other_id)
                    self.G.add_edge(other_id, loc_id)

                # Connecting farms to ports (unidirectional)
                if loc_type == 'farm' and other_type == 'port':
                    self.G.add_edge(loc_id, other_id)

                # Connecting farms to warehouses (unidirectional)
                if loc_type == 'farm' and other_type == 'warehouse':
                    self.G.add_edge(loc_id, other_id)

                # Connecting farms to customers on the same island (unidirectional)
                if loc_type == 'farm' and other_type == 'customer' and self.on_same_island(loc_id, other_id):
                    self.G.add_edge(loc_id, other_id)

                # Connecting farms to batches on the same island (bidirectional)
                # Assuming 'batches' are identifiable by a specific node attribute or type
                if loc_type == 'farm' and 'batch' in other_id and self.on_same_island(loc_id, other_id):
                    self.G.add_edge(loc_id, other_id)
                    self.G.add_edge(other_id, loc_id)

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
                if self.G.has_edge(from_location, to_location):
                    self.G[from_location][to_location]['type'] = route_type
                    self.G[from_location][to_location]['costs'] = costs
                # If no direct route exists, check for and use data from reverse route if it exists
                elif self.G.has_edge(to_location, from_location):
                    reverse_edge_data = self.G[to_location][from_location]
                    self.G.add_edge(from_location, to_location, type=reverse_edge_data['type'], costs=reverse_edge_data['costs'])
                # Calculate and add estimated costs if no direct or reverse route exists
                else:
                    # Placeholder for address retrieval and distance calculation
                    from_address_doc = self.db.collection('Locations').document(from_location).get()
                    to_address_doc = self.db.collection('Locations').document(to_location).get()
                    if from_address_doc.exists and to_address_doc.exists:
                        from_address = from_address_doc.to_dict().get('address')
                        to_address = to_address_doc.to_dict().get('address')
                        # Compute distance and estimated costs (assuming compute_distance is defined)
                        distance = compute_distance(from_address, to_address)
                        estimated_costs = self.calculate_estimated_costs(distance)  
                        # Update edge with estimated costs
                        self.G.add_edge(from_location, to_location, type='estimated', costs=estimated_costs)

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
        results = Optimize(self.G, batches, orders)
        optimized_results = results.results

        # Process and return results
        return optimized_results

sc = SupplyChain()
sc.build_network_graph()