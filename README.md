
Database Schema

Locations Collection:
Document ID: Unique identifier for each location, Firebase naming conventions
Fields:
address: String, the physical address of the location.
island: String, island name
type: String, the type of location (e.g., port, warehouse, farm, customer, seller).

Routes Collection:
Document ID: Unique identifier for each route
Fields:
from: String, the starting location's location_id.
to: String, the destination location's location_id.
type: String, indicates if the route is based on volume (m3) or weight (metric tonnes).
costs: Map/Object, containing costs for different tiers (e.g., {"32": 230, "67": 250}).

Sellers Collection:
Document ID: Unique identifier for each seller
Fields:
location_id: String, location of the seller.
name: String, internal name for the seller.

    Subcollection: Batches
    Document ID: Unique identifier for each batch
    Fields:
    quantity: Number, the quantity of product in the batch.
    weight: Number, the weight of the batch (m3).
    volume: Number, the volume of the batch (volume).
    type: String, the type of the product in the batch.
    cost: Number, the cost of the entire batch, which is zero if it's already owned.
    timestamp: Timestamp, the creation or update time of the batch.
    active: Boolean, indicating if the batch is active.

Customers Collection:
Document ID: customer_id, a unique identifier for each customer
Fields:
location_id: String, location of the customer.
name: String, internal name for the customer.

    Subcollection: Orders
    Fields:
    quantity: Number, the required quantity of product.
    type: String, the type of product required.
    timestamp: Timestamp, the creation or update time of the order.
    active: Boolean, indicating if the order is active.

Ongoing Routes Collection:
Document ID: A unique identifier for each trade permutation
Fields:
path: Array of Strings, ordered list of location_ids representing the route taken.
batch_assignments: Map/Object, mapping each batch to its destination location_id.
cost: Number, the total cost associated with the permutation.

Internal Sink Collection:
Document ID:
Fields:
location_id: the id of the location document
name: Internal name for the place

Subcollection: Sink
    Fields:
    quantity: Number, the required quantity of product.
    type: String, the type of product required.
    

Back-End Logic

Supply Chain Management: The system uses the network graph to optimize routes and manage supply chain logistics based on the current state of batches, customer orders, and available routes.

Construct a Network Graph: Each batch forms bidirectional connections with other batches if they reside on the same island, ensuring no links are established with batches on different islands. Additionally, each batch directs connections towards all locations within the same island. Customers are interconnected through bidirectional links. Ports, in a similar manner, establish bidirectional connections with all other ports and extend connections towards customers. wharehouses 

port <--> port
wharehouse --> Customer
wharehouse <--> wharehouse
Customer <--> Customer
batches <--> batches 
batches --> port
batches --> wharehouse



Network Graph (Supply Chain Network)
This is a simplified Network of our supply_chain

Nodes: Represent locations. 
Edges: Represent routes between locations. Edges are created based on the from and to fields in the Routes collection, with costs and other details from the route's data. 
If this data is unavailable, googlemaps calculates the cost, e.g. {type: volume, {30: 200, 60:300}} means 30m3 costs 200 euros, and 60m3 costs 300 euros
Logic for Handling Shared Locations
When adding a new location, read the serialized NetworkX object from db, update the graph based on the new location.
Filling the demand of a customer, reads the serialized NetworkX object from db. It adds the customer to the network object and returns batches that optimize profit.


Satellite Logic:

1. Create a subscription and confirm it. Confirmation takes up to one day.
2. Update the image daily and store it in google storage and the path to the asset under site collection