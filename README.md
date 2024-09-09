
### Database Schema

Organizations Collection:
Document ID: Unique identifier for each organization in our app, Firebase naming conventions
Fields:
name: String, name of organization
permissions: Map/Object, which modules the organization has access to 


# All of the following collections are subcollections of organizations

Users Collection:
Document ID: Unique identifier for each user, Firebase naming conventions
Fields:

Products Collection:
Document ID: Unique identifier for each product, Firebase naming conventions
Fields:
name: String, name of the product
code: String, internal identifier of product
price: Number, price in USD
MOQ: Number, the minimum order quantity in weight or amount
notes: String, any additional relevant information
Biological: Boolean, true if a biological product

Warehouse Collection:
Document ID: Unique identifier for each warehouse, Firebase naming conventions
Fields:
location: String, the firebase identifier of the location in the Locations Collection

    Inventory Subcollection:
    Document ID: Unique identifier for each type of product, Firebase naming conventions
    Fields:
    product_id: String, the firebase identifier of the product in the Products Collection
    quantity: Number, the quantity of product in the batch
    timestamp: Timestamp, the creation or update time of the batch

Customers Collection:
Document ID: customer_id, a unique identifier for each customer
Fields:
location_id: String, location id of the customer
name: String, internal name for the customer

    Orders Subcollection:
    Fields:
    order data: Map/Object, the firebase identifier of the product(s) in the Products Collection with associated quantity
    e.g {product1: 2, product2, 1}
    timestamp: Timestamp, the creation or update time of the order
    status: String, indicating the order status

Locations Collection:
Document ID: Unique identifier for each location, Firebase naming conventions
Fields:
address: String, the physical address of the location.
country: String
island: String, island name (only applicable in Indonesia)
type: String, the type of location (e.g., port, warehouse, farm, customer, seller)

Routes Collection:
Document ID: Unique identifier for each route
Fields:
from: String, the starting location's location_id
to: String, the destination location's location_id
type: String, indicates if the route is based on volume (m3) or weight (metric tonnes)
costs: Map/Object, containing costs for different tiers of volume (e.g., {32: 230, 67: 250})

Sellers Collection:
Document ID: Unique identifier for each seller
Fields:
location_id: String, location of the seller
name: String, internal name for the seller

    Batches Subcollection:
    Document ID: Unique identifier for each batch
    Fields:
    quantity: Number, the quantity of product in the batch
    weight: Number, the weight of the batch (metric tonnes)
    volume: Number, the volume of the batch (m3)
    type: String, the type of the product in the batch
    cost: Number, the cost of the entire batch, which is zero if it's already owned
    timestamp: Timestamp, the creation or update time of the batch
    active: Boolean, indicating if the batch is active

Ongoing Routes Collection:
Document ID: A unique identifier for each trade permutation
Fields:
path: Array of Strings, ordered list of location_ids representing the route taken
batch_assignments: Map/Object, mapping each batch to its destination location_id
cost: Number, the total cost associated with the permutation

Internal Sink Collection:
Document ID:
Fields:
location_id: the id of the location document
name: Internal name for the place

Subcollection: Sink
    Fields:
    quantity: Number, the required quantity of product
    type: String, the type of product required
    

### Back-End Logic

Supply Chain Management: The system uses the network graph to optimize routes and manage supply chain logistics based on the current state of batches, customer orders, and available routes.

Construct a Network Graph: Each batch forms bidirectional connections with other batches if they reside on the same island, ensuring no links are established with batches on different islands. Additionally, each batch directs connections towards all locations within the same island. Customers are interconnected through bidirectional links. Ports, in a similar manner, establish bidirectional connections with all other ports and extend connections towards customers.

port <--> port
warehouse --> customer
warehouse <--> warehouse (if on the same island)
customer <--> customer (if on the same island)
farm <--> batches (if on the same island)
farm --> customer (if on the same island)
farm --> port
farm --> warehouse

Edges: Represent routes between locations. Edges are created based on the from and to fields in the Routes collection, with costs and other details from the route's data. 
If this data is unavailable, googlemaps calculates the cost, e.g. {type: volume, {30: 200, 60:300}} means 30m3 costs 200 euros, and 60m3 costs 300 euros


Satellite Logic:

1. Create a subscription and confirm it. Confirmation takes up to one day.
2. Update the image daily and store it in google storage and the path to the asset under site collection