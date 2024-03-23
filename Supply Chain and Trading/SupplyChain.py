import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import networkx as nx
from networkx.readwrite import json_graph
from google_distance import compute_distance
from trading_opt import Optimize
import json

class SupplyChain:
    def __init__(self):
        # Firebase Admin SDK Initialization
        cred = credentials.Certificate('firebase_auth_token/alginnova-f177f-firebase-adminsdk-1hr5k-b3cac9ea17.json')
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()

    def build_network_graph(self, destinations):
        # Initialize directed graph
        G = nx.DiGraph()

        # Fetch all locations and filter for transport locations
        locations = list(self.db.collection('Locations').stream())  # Convert to list for multiple iterations
        def is_transport_location(location):
            return location.get('type') not in ['customer', 'seller', 'farm']

        transport_locations = {}
        for location in locations:
            if is_transport_location(location):
                location_id = location.id
                G.add_node(location_id, type=location.get('type'), island=location.get('island'))
                island = location.get('island')
                transport_locations.setdefault(island, []).append(location_id)

        # Add customer and sink nodes from destinations
        for destination_id in destinations:
            destination_doc = self.db.collection('Locations').document(destination_id).get()
            destination_data = destination_doc.to_dict()
            destination_type = destination_data.get('type')

            if destination_type == 'customer':
                # Add customer node
                G.add_node(destination_id, type='sink', island=destination_data.get('island'))
            else:
                # Add sink node
                G.add_node(destination_id, type='sink', island=destination_data.get('island'))

        # Fetch and add batches as nodes
        batches = self.db.collection('Batches').stream()
        for batch in batches:
            G.add_node(batch.id, type='batch')

        # Create directed edges
        # Ports to ports
        ports = [loc.id for loc in locations if loc.get('type') == 'port']
        for port1 in ports:
            for port2 in ports:
                if port1 != port2:
                    G.add_edge(port1, port2)

        # Transport locations on the same island
        for island, locs in transport_locations.items():
            for loc1 in locs:
                for loc2 in locs:
                    if loc1 != loc2:
                        G.add_edge(loc1, loc2)

        # Batches to each other and to transport locations on the same island
        for batch in batches:
            for other_batch in batches:
                if batch.id != other_batch.id:
                    G.add_edge(batch.id, other_batch.id)
            for location in locations:
                if location.get('type') in ['warehouse', 'port'] and batch.get('island') == location.get('island'):
                    G.add_edge(batch.id, location.id)

        # Customers to each other and from transport locations
        for customer in customers:
            for other_customer in customers:
                if customer.id != other_customer.id:
                    G.add_edge(customer.id, other_customer.id)
            for location in locations:
                if location.get('type') in ['warehouse', 'port'] and customer.get('location_id') == location.id:
                    G.add_edge(location.id, customer.id)

        self.SCN = G
        self.build_edges()

    def build_edges(self):
        # Fetch routes from Firestore
        routes = self.db.collection('Routes').stream()

        # Process each route and update edges in the graph
        for route in routes:
            from_location = route.get('from')
            to_location = route.get('to')

            # Check if the edge exists in the graph
            if self.SCN.has_edge(from_location, to_location):
                route_type = route.get('type')
                costs = route.get('costs')

                # Update edge with route data
                self.SCN[from_location][to_location]['type'] = route_type
                self.SCN[from_location][to_location]['costs'] = costs

            # Check if reverse route exists in the graph
            elif self.SCN.has_edge(to_location, from_location):
                # Use reverse route's properties for this edge
                reverse_edge_data = G[to_location][from_location]
                self.SCN[from_location][to_location]['type'] = reverse_edge_data['type']
                self.SCN[from_location][to_location]['costs'] = reverse_edge_data['costs']

            # If no direct or reverse route exists, calculate estimated costs
            else:
                # Fetch addresses of locations
                addr1 = self.db.collection('Locations').document(from_location).get().to_dict().get('address')
                addr2 = self.db.collection('Locations').document(to_location).get().to_dict().get('address')

                # Compute distance, this logic is according to 
                distance = compute_distance(addr1, addr2)
                estimated_costs = {}
                for weight in [10, 30]:
                    cost = (distance * 0.48 + 121) * weight / 10
                    estimated_costs[f"{weight}kg"] = cost

                # Update edge with estimated costs
                self.SCN[from_location][to_location]['type'] = 'weight'
                self.SCN[from_location][to_location]['costs'] = estimated_costs
        
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