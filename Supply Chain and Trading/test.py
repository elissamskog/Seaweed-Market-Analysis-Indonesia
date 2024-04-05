import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from SupplyChain import SupplyChain
import networkx as nx
import unittest



class TestSupplyChain(unittest.TestCase):
    def setUp(self):
        # Initialize your SupplyChain class here. This ensures 'sc' is available as 'self.sc' in every test method.
        self.sc = SupplyChain()

        # Define test destinations based on your Firestore setup
        destinations = ['c1ZsKpkEBskPRTqBvYXP', 'ZjPwjkZiS4U1ZUnwG3sX']  # Adjust accordingly

        # Execute the method under test to build the graph for each test method
        self.sc.build_network_graph(destinations)

    def test_build_network_graph(self):
        print("\nNodes in the graph:")
        for node, attrs in self.sc.SCN.nodes(data=True):
            node_type = attrs.get('type')
            print(f"Node ID: {node}, Type: {node_type}")
        
        print("\nEdges in the graph (pointing information):")
        for from_node, to_node, attributes in self.sc.SCN.edges(data=True):
            # Optionally, include edge attributes in the print statement if needed
            edge_attributes = ', '.join([f"{key}: {value}" for key, value in attributes.items()])
            from_node_type = self.sc.SCN.nodes[from_node].get('type')
            to_node_type = self.sc.SCN.nodes[to_node].get('type')
            print(f"{from_node} ({from_node_type}) -> {to_node} ({to_node_type})")

if __name__ == '__main__':
    unittest.main()
