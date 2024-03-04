from SupplyChain import SupplyChain
import networkx as nx

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