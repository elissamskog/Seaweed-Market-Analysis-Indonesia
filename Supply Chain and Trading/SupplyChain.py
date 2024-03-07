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

    def add_location(self, location_id, address, id, type):
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
        # Initialize directed graph
        G = nx.DiGraph()

        # Fetch data from Firestore
        customers = self.db.collection('Customers').stream()
        batches = self.db.collection('Batches').stream()
        locations = list(self.db.collection('Locations').stream())  # Convert to list for multiple iterations
        
        # Helper function to filter transport locations
        def is_transport_location(location):
            return location.get('type') in ['warehouse', 'port']

        # Create nodes for batches, transport locations, and customers
        for batch in batches:
            G.add_node(batch.id, type='batch')
        transport_locations = {}  # Dictionary to group transport locations by island
        for location in locations:
            if is_transport_location(location):
                G.add_node(location.id, type='location', island=location.get('island'))
                island = location.get('island')
                transport_locations.setdefault(island, []).append(location.id)
        for customer in customers:
            G.add_node(customer.id, type='customer', island=customer.get('location_id'))

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
        
    def fill_demand(self):
        # Build the network
        self.build_network_graph()

        # Initialize a dictionary to hold all demanded batches
        demanded_batches = {}

        # Fetch all active orders from customers
        customers_ref = self.db.collection('customers')
        customers_docs = customers_ref.stream()

        orders = {}  # To store orders indexed by customer location

        for customer_doc in customers_docs:
            customer_data = customer_doc.to_dict()
            customer_location_id = customer_data.get("location_id")

            # Fetch active orders for each customer
            orders_ref = customer_doc.reference.collection('Orders')
            orders_docs = orders_ref.where('active', '==', True).stream()

            for order_doc in orders_docs:
                order_data = order_doc.to_dict()
                orders[customer_location_id] = order_data

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

                # Add batch data to demanded_batches
                demanded_batches[batch_id] = {
                    'weight': batch_weight,
                    'volume': batch_volume,
                    'location_id': seller_location_id,
                    'species': batch_data.get('species')  # Add species information
                }

        # Optimize transportation costs with all available batches and orders
        results = Optimize(self.SCN, demanded_batches, orders)
        optimized_results = results.results

        # Process and return results
        return optimized_results

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

    def accept_trades(self, trade_ids):
        '''This stores the trades permutations in the db'''
        return 0
    
    def complete_trades(self, trade_ids):
        '''This removes the trade from the db, updates the batches and updates the customers db'''
        return 0