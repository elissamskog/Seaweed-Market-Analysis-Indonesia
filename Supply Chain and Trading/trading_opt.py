import networkx as nx
import pulp
from itertools import combinations, chain

class Optimize:
    def __init__(self, SCN, batches, destinations):
        self.SCN = SCN
        self.batches = batches
        self.destinations = destinations
        self.permutation_costs = self.compute_cost_permutations()
        self.results = self.optimize_transportation_costs()

    def optimize_transportation_costs(self):
        # The key limitation of this optimaztion script lies in the first two constraints.
        problem = pulp.LpProblem("Minimize_Transportation_Costs", pulp.LpMinimize)
        x = pulp.LpVariable.dicts("permutation", self.permutation_costs.keys(), cat='Binary')

        problem += pulp.lpSum(x[perm] * self.permutation_costs[perm] for perm in self.permutation_costs)

        # Constraint: Each batch is involved in at most one selected permutation
        for batch in self.batches:
            problem += pulp.lpSum(x[(batch_combo, dest_combo)] for batch_combo, dest_combo in self.permutation_costs.keys() if batch in batch_combo) <= 1

        # Constraint: Each customer is involved in at most one selected permutation
        for customer in self.destinations:
            problem += pulp.lpSum(x[(batch_combo, dest_combo)] for batch_combo, dest_combo in self.permutation_costs.keys() if customer in dest_combo) <= 1

        # Add constraints for meeting weight requirements at each destination
        # These are not strict constraints - if not met, that customer's demand remains unfulfilled
        for dest in self.destinations:
            problem += (pulp.lpSum(x[(batch_combo, dest_combo)] * sum(self.batches[batch]['weight'] for batch in batch_combo) 
                        for batch_combo, dest_combo in self.permutation_costs.keys() if dest in dest_combo) 
                        >= self.destinations[dest]['weight'], f"WeightRequirement_{dest}")

        problem.solve()

        results = {}
        for perm in self.permutation_costs:
            if pulp.value(x[perm]) == 1:
                results[perm] = {'cost': self.permutation_costs[perm]}
        return results

    def compute_cost_permutations(self):
        all_destination_combinations = []
        for r in range(1, len(self.destinations) + 1):
            all_destination_combinations.extend(combinations(self.destinations.keys(), r))

        feasible_permutations = {}
        for destination_combo in all_destination_combinations:
            required_species = {self.destinations[dest]['species'] for dest in destination_combo}

            for batch_combo in self.powerset(self.batches.keys()):
                if self.matches_species(batch_combo, required_species):
                    if self.meets_optimal_weight(batch_combo, destination_combo):
                        cost, _ = self.calculate_cost_for_permutation(batch_combo, destination_combo)
                        feasible_permutations[(batch_combo, destination_combo)] = cost
        return feasible_permutations

    def matches_species(self, batch_combo, required_species):
        # Find the species present in the batch_combo
        combo_species = {self.batches[batch]['species'] for batch in batch_combo}

        # Check that all species in the combo are required by the destinations
        if not combo_species.issubset(required_species):
            return False

        # Check if there's at least one species in the combo that matches the destinations
        return bool(combo_species.intersection(required_species))

    def meets_optimal_weight(self, batch_combo, destination_combo):
        # Group batches and destinations by species
        batch_weights_by_species = self.group_by_species(self.batches, batch_combo)
        destination_weights_by_species = self.group_by_species(self.destinations, destination_combo)

        # For each species, check if the total weight of batches meets/exceeds the destination requirement
        for species in destination_weights_by_species:
            total_destination_weight = destination_weights_by_species[species]
            if species not in batch_weights_by_species:
                continue  # No batches available for this species

            combo_weight = batch_weights_by_species[species]

            if combo_weight >= total_destination_weight:
                # Check if removing any one batch falls below the requirement
                for batch in batch_combo:
                    if self.batches[batch]['species'] != species:
                        continue  # Skip batches of different species
                    weight_without_batch = combo_weight - self.batches[batch]['weight']
                    if weight_without_batch < total_destination_weight:
                        return True

        return False

    def group_by_species(self, entities, ids):
        weights_by_species = {}
        for id in ids:
            species = entities[id]['species']
            weight = entities[id]['weight']
            if species not in weights_by_species:
                weights_by_species[species] = 0
            weights_by_species[species] += weight
        return weights_by_species

    @staticmethod
    def powerset(iterable):
        s = list(iterable)
        return chain.from_iterable(combinations(s, r) for r in range(1, len(s)+1))

    def calculate_cost_for_permutation(self, batch_combo, destination_combo):

        temp_SCN = self.create_temp_SCN(batch_combo)

        # Initialize path list to store the order of batches and destinations
        path = []

        # Find starting batch with shortest path to any destination
        shortest_path_cost, starting_batch = self.find_starting_batch(batch_combo, destination_combo, temp_SCN)
        path.append(starting_batch)

        # Calculate the cost and path of collecting all batches
        collection_cost, collection_path = self.calculate_collection_cost(temp_SCN, batch_combo, starting_batch)
        path.extend(collection_path)

        # Calculate the cost and path of delivering to each destination
        delivery_cost, delivery_path = self.calculate_delivery_cost(temp_SCN, batch_combo, destination_combo)
        path.extend(delivery_path)

        total_cost = shortest_path_cost + collection_cost + delivery_cost
        return total_cost, path

    def find_starting_batch(self, batch_combo, destination_combo, SCN):
        min_cost = float('inf')
        starting_batch = None

        # Iterate over each batch and destination pair to find the shortest path
        for batch in batch_combo:
            for destination in destination_combo:
                cost = nx.shortest_path_length(SCN, source=self.batches[batch]['location'], target=self.destinations[destination]['location'], weight='cost')
                if cost < min_cost:
                    min_cost = cost
                    starting_batch = batch

        return min_cost, starting_batch

    def calculate_collection_cost(self, batch_combo, starting_batch, SCN):
        remaining_batches = set(batch_combo) - {starting_batch}
        total_cost = 0
        current_location = self.batches[starting_batch]['location']

        collection_path = [current_location]

        while remaining_batches:
            next_batch, next_cost = self.find_next_closest_batch(current_location, remaining_batches, SCN)
            total_cost += next_cost
            current_location = self.batches[next_batch]['location']
            collection_path.append(current_location)
            remaining_batches.remove(next_batch)

        return total_cost, collection_path

    def find_next_closest_batch(self, current_location, remaining_batches, SCN):
        min_cost = float('inf')
        closest_batch = None

        for batch in remaining_batches:
            cost = nx.shortest_path_length(SCN, source=current_location, target=self.batches[batch]['location'], weight='cost')
            if cost < min_cost:
                min_cost = cost
                closest_batch = batch

        return closest_batch, min_cost

    def calculate_delivery_cost(self, batch_combo, destination_combo, SCN):
        total_cost = 0
        current_location = self.batches[batch_combo[-1]]['location']

        delivery_path = []

        for destination in destination_combo:
            cost = nx.shortest_path_length(SCN, source=current_location, target=self.destinations[destination]['location'], weight='cost')
            total_cost += cost
            current_location = self.destinations[destination]['location']
            delivery_path.append(current_location)

        return total_cost, delivery_path

    def create_temp_SCN(self, batch_combo):
        temp_SCN = self.SCN.copy()
        total_weight = sum(self.batches[batch]['weight'] for batch in batch_combo)
        total_volume = sum(self.batches[batch]['volume'] for batch in batch_combo)

        for u, v, data in temp_SCN.edges(data=True):
            edge_cost = self.compute_edge_cost(data, total_weight, total_volume)
            temp_SCN[u][v]['cost'] = edge_cost

        return temp_SCN

    def compute_edge_cost(self, edge_data, weight, batch_volume):
        """
        Compute the cost of an edge based on weight and volume, considering the route type in edge_data.
        """

        route_type = edge_data.get('type')
        tiers = edge_data.get('costs', {})

        if route_type == 'weight':
            return self.calculate_tier_cost(tiers, weight)
        elif route_type == 'volume':
            return self.calculate_tier_cost(tiers, batch_volume)
        else:
            return float('inf')    

    def calculate_tier_cost(self, tiers, amount):
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


SCN = nx.DiGraph()
SCN.add_edge("A", "B", cost=10)
SCN.add_edge("B", "C", cost=15)
SCN.add_edge("A", "C", cost=20)

# Define sample batches and destinations
batches = {
    "batch1": {"location": "A", "weight": 20, "volume": 5, "species": "X"},
    "batch2": {"location": "B", "weight": 40, "volume": 10, "species": "Y"}
}

destinations = {
    "dest1": {"location": "C", "weight": 15, "species": "X"},
    "dest2": {"location": "C", "weight": 25, "species": "Y"}
}

# Create an instance of Optimize
optimize_instance = Optimize(SCN, batches, destinations)

# Print the results
print("Optimization Results:")
print(optimize_instance.results)