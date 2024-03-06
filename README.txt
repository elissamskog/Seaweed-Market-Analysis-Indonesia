**NOTE:

Database Schema in firestore:

    Locations Collection:
    Document ID: Unique identifier for each location, Firebase naming conventions
    Fields:
    customers: Map/object, Customer object
    address: String, the physical address of the location.
    island: String, island name
    type: String, the type of location (e.g., port, warehouse, farm).

    Routes Collection:
    Document ID: Unique identifier for each route
    Fields:
    from: String, the starting location's location_id.
    to: String, the destination location's location_id.
    type: String, indicates if the route is based on volume (m3) or weight (metric tonnes).
    costs: Map/Object, containing costs for different tiers (e.g., {"32": 230, "67": 250}).

    Customers Collection:
    Document ID: customer_id, a unique identifier for each customer
    Fields:
    location_id: Map/Object, location object.
    quantity_required: Number, the required quantity of product.
    species: String, the species of product required.

    Batches Collection:
    Document ID: Unique identifier for each batch
    Fields:
    location_id: Map/object, Location object
    quantity: Number, the quantity of product in the batch.
    weight: Number, the weight of the batch (m3).
    volume: Number, the volume of the batch (volume).
    species: String, the species of the product in the batch.
    cost: Number, the cost of the entire batch, which is zero if it's already owned.

    Network Collection:
    Serialized Supply Chain Network Graph object
    Is updated whenever a location is added.


    Ongoing Trades Collection: 
    Document ID: A unique identifier for each trade permutation
    Fields:
    path: Array of Strings. Ordered list of location_ids representing the route taken.
    batch_assignments: Map/Object. Mapping each batch to its destination location_id.
    cost: Number. The total cost associated with the permutation
    

Network Graph (Supply Chain Network)
This is a simplified Network of our supply_chain which only looks at unique location id's (type.city.island id's)

Nodes: Represent locations. 
Edges: Represent routes between locations. Edges are created based on the from and to fields in the Routes collection, with costs and other details from the route's data. 
If this data is unavailable, googlemaps calculates the cost, e.g. {type: volume, {30: 200, 60:300}} means 30m3 costs 200 euros, and 60m3 costs 300 euros
Logic for Handling Shared Locations
When adding a new location, read the serialized NetworkX object from db, update the graph based on the new location.
Filling the demand of a customer, reads the serialized NetworkX object from db. It adds the customer to the network object and returns batches that optimize profit.

Operational Flow
Adding a Locations: Add a document/documents in the Locations collection. Input:
{
  "Locations": [
    {
      "address": "Warehouse Road 123, 112 45 Stockholm, Sweden",
      "type": "warehouse",
      "island": "Java"
    },
    {
      "address": "Warehouse Road 123, 112 45 Stockholm, Sweden",
      "type": "warehouse",
      "island": "Java"
    }
  ]
}

Adding a Routes: Add a document/documents in the Routes collection, specifying the start and end points using location object. 
Input: 
{
  "Routes": [
    {
      "from": "Document ID for location",
      "to": "Document ID for location",
      "type": "weight",
      "cost_tiers": {
        "up_to_100kg": 200,
        "101_to_500kg": 800,
        "501kg_and_above": 1500
      }
    },
    {
      "from": "Document ID for location",
      "to": "Document ID for location",
      "type": "volume",
      "cost_tiers": {
        "up_to_100kg": 200,
        "101_to_500kg": 800,
        "501kg_and_above": 1500
      }
    }
  ]
}

Adding a Customers: Add a document/documents in the Customers collection. The system checks if a node with the customer's location exists in the network graph and connects the customer to this node.
Input:
{
  "Customers": [
    {
      "Document ID for location": {
        "address": "Warehouse Road 123, 112 45 Stockholm, Sweden",
        "type": "warehouse",
        "island": "Java"
      },
      "quantity_required": 100,
      "species": "alg"
    },
    {
      "Document ID for location": {
        "address": "Warehouse Road 123, 112 45 Stockholm, Sweden",
        "type": "warehouse",
        "island": "Java"
      },
      "quantity_required": 100,
      "species": "alg"
    }
  ]
}

Adding a Batches: Add a document/documents in the Batches collection, associated with a location object. 
Input:
{
  "Batches": [
    {
      "Document ID for location": {
        "address": "Warehouse Road 123, 112 45 Stockholm, Sweden",
        "type": "warehouse",
        "island": "Java"
      },
      "quantity": 500,
      "weight": 100,
      "volume": 100,
      "species": "alg",
      "cost": 100
    },
    {
      "Document ID for location": {
        "address": "Warehouse Road 123, 112 45 Stockholm, Sweden",
        "type": "warehouse",
        "island": "Java"
      },
      "quantity": 500,
      "weight": 100,
      "volume": 100,
      "species": "alg",
      "cost": 100
    }
  ]
}

Supply Chain Management: The system uses the network graph to optimize routes and manage supply chain logistics based on the current state of batches, customer orders, and available routes.