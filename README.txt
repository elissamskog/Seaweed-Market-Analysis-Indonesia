**NOTE: location_id is an internal id that we use for locations in the form city.island, the identifier for a location
in the location collection is not the same.


Database Schema in firestore:

    Locations Collection:
    Document ID: Unique identifier for each location (e.g., location_001).
    Fields:
    address: String, the physical address of the location.
    location_id: String, city.island format identifier (e.g., "type.city.island"), where type is the unique identifier to that city and island
    type: String, the type of location (e.g., port, warehouse, farm).

    Routes Collection:
    Document ID: Unique identifier for each route (e.g., route_001).
    Fields:
    from: String, the starting location's location_id.
    to: String, the destination location's location_id.
    type: String, indicates if the route is based on volume (m3) or weight (metric tonnes).
    costs: Map/Object, containing costs for different tiers (e.g., {"32": 230, "67": 250}).

    Customers Collection:
    Document ID: customer_id, a unique identifier for each customer.
    Fields:
    address: String, the address of the customer.
    location_id: String, city.island format for the customer's location.
    quantity_required: Number, the required quantity of product.
    species: String, the species of product required.

    Batches Collection:
    Document ID: Unique identifier for each batch (e.g., batch_001).
    Fields:
    location_id: String, the type.city.island identifier of a location
    quantity: Number, the quantity of product in the batch.
    weight: Number, the weight of the batch (m3).
    volume: Number, the volume of the batch (volume).
    species: String, the species of the product in the batch.
    cost: Number, the cost of the entire batch, which is zero if it's already owned.

    Network Collection:
    Serialized Supply Chain Network Graph object
    Is updated whenever a location is added.

Network Graph (Supply Chain Network)
This is a simplified Network of our supply_chain which only looks at unique location id's (type.city.island id's)

Nodes: Represent locations (based on location_id).
Edges: Represent routes between locations. Edges are created based on the from and to fields in the Routes collection, with costs and other details from the route's data. 
If this data is unavailable, googlemaps calculates the cost, e.g. {type: volume, {30: 200, 60:300}} means 30m3 costs 200 euros, and 60m3 costs 300 euros
Logic for Handling Shared Locations
When adding a new location, read the serialized NetworkX object from db, update the graph based on the new location.
Filling the demand of a customer, reads the serialized NetworkX object from db. It adds the customer to the network object and returns batches that optimize profit.

Operational Flow
Adding a Location: Add a document in the Locations collection.
Adding a Route: Add a document in the Routes collection, specifying the start and end points using location_ids.
Adding a Customer: Add a document in the Customers collection. The system checks if a node with the customer's location_id exists in the network graph and connects the customer to this node.
Adding a Batch: Add a document in the Batches collection, associated with a location.id.
Supply Chain Management: The system uses the network graph to optimize routes and manage supply chain logistics based on the current state of batches, customer orders, and available routes.