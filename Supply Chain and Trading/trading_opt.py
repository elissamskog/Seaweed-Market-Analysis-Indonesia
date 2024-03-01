import pulp
import networkx as nx


def optimize(SCN, batches, location_id, weight_required):
    results = optimize_transportation_costs(SCN, batches, location_id, weight_required)

    batches_to_send = {}
    remaining_weight = weight_required

    for batch_id, data in results.items():
        if data['send'] == 1:  # If the batch is to be sent
            weight_to_send = min(batches[batch_id]['weight'], remaining_weight)
            batches_to_send[batch_id] = {'path': data['path'], 'weight': weight_to_send, 'cost': data['cost']}
            remaining_weight -= weight_to_send
            if remaining_weight <= 0:
                break

    return batches_to_send


def optimize_transportation_costs(SCN, batches, location_id, weight_required):
    # Initialize the linear programming problem
    problem = pulp.LpProblem("Minimize_Transportation_Costs", pulp.LpMinimize)

    # Calculate transportation cost for each batch and store paths
    batch_costs = {}
    batch_paths = {}
    for i in batches:
        weight = batches[i]['weight']
        volume = batches[i]['volume']
        path = find_optimal_path(SCN, batches[i]['location'], location_id, weight, volume)
        cost = compute_total_cost(SCN, path, weight, volume)
        batch_costs[i] = cost
        batch_paths[i] = path

    # Sort batches by transportation cost
    sorted_batches = sorted(batch_costs, key=batch_costs.get)

    # Binary decision variables for each batch (1 = send, 0 = do not send)
    send_batch = pulp.LpVariable.dicts("send_batch", sorted_batches, cat='Binary')

    # Objective Function: Minimize the total transportation cost
    problem += pulp.lpSum([send_batch[i] * batch_costs[i] for i in sorted_batches])

    # Weight Requirement Constraint: Total weight sent must meet the required weight
    problem += pulp.lpSum([send_batch[i] * batches[i]['weight'] for i in sorted_batches]) >= weight_required, "Weight_Requirement"

    # Solve the problem
    problem.solve()

    # Extract results for batches to be sent
    results = {}
    for batch_id in batches:
        send_decision = pulp.value(send_batch[batch_id])
        results[batch_id] = {'send': send_decision, 'cost': batch_costs[batch_id], 'path': find_optimal_path(SCN, batches[batch_id]['location'], location_id, batches[batch_id]['weight'], batches[batch_id]['volume'])}
    return results

def compute_total_cost(SCN, path, weight, volume):
    """
    Compute the total cost for a given path, weight, and volume.
    """
    if not path:
        return float('inf')

    total_cost = 0
    for i in range(len(path) - 1):
        edge_data = SCN.get_edge_data(path[i], path[i + 1])
        edge_cost = compute_edge_cost(edge_data, weight, volume)
        total_cost += edge_cost

    return total_cost

def find_optimal_path(SCN, from_loc, to_loc, weight, volume):
    """
    Find the optimal path in the SCN based on weight.
    """

    # Update edge weights in the graph based on the given weight and volume
    for u, v in SCN.edges():
        edge_data = SCN.get_edge_data(u, v)
        cost = compute_edge_cost(edge_data, weight, volume)
        SCN[u][v]['weight'] = cost

    # Find the shortest path using the updated edge weights
    try:
        shortest_path = nx.shortest_path(SCN, source=from_loc, target=to_loc, weight='weight')
        return shortest_path
    except nx.NetworkXNoPath:
        print(f"No path found from {from_loc} to {to_loc}.")
        return None

def compute_edge_cost(edge_data, weight, batch_volume):
    """
    Compute the cost of an edge based on weight and volume, considering the route type in edge_data.
    """

    route_type = edge_data.get('type')
    tiers = edge_data.get('costs', {})

    if route_type == 'weight':
        return calculate_tier_cost(tiers, weight)
    elif route_type == 'volume':
        return calculate_tier_cost(tiers, batch_volume)
    else:
        return float('inf')  # Route type not found or unsupported

def calculate_tier_cost(tiers, amount):
    """
    Calculate cost based on a given set of tiers and an amount.
    """
    sorted_tiers = sorted([(float(k), v) for k, v in tiers.items()], key=lambda x: x[0])
    total_cost = 0
    remaining_amount = amount

    for tier_capacity, tier_cost in sorted_tiers:
        if remaining_amount > 0:
            if remaining_amount <= tier_capacity:
                total_cost += tier_cost
                break
            else:
                total_cost += tier_cost
                remaining_amount -= tier_capacity

    return total_cost


'''# Mock Supply Chain Network (SCN) setup
SCN = nx.Graph()

# Add mock locations
SCN.add_node("Location_A")
SCN.add_node("Location_B")
SCN.add_node("Customer_Location")

# Add mock routes with tiered costs
SCN.add_edge("Location_A", "Location_B", type='weight', costs={'100': 150, '200': 250})
SCN.add_edge("Location_B", "Customer_Location", type='volume', costs={'50': 100, '100': 180})

# Mock batch data
batches = {
    "Batch_1": {'location': 'Location_A', 'weight': 50, 'volume': 20, 'quantity': 10},
    "Batch_2": {'location': 'Location_A', 'weight': 40, 'volume': 25, 'quantity': 15},
    "Batch_3": {'location': 'Location_B', 'weight': 20, 'volume': 15, 'quantity': 5}
}

# Mock customer requirement
weight_required = 100

# Function calls
results = optimize(SCN, batches, "Customer_Location", weight_required)
print("Optimization Results:", results)'''