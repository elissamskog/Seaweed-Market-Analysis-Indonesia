
Database Schema

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
    species: String, the species of the product in the batch.
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
    species: String, the species of product required.
    timestamp: Timestamp, the creation or update time of the order.
    active: Boolean, indicating if the order is active.

Network Collection:
Serialized Supply Chain Network Graph object.
Updated if: a new transport location is added, a new customer order is submitted, a new batch is submitted.

Ongoing Trades Collection:
Document ID: A unique identifier for each trade permutation
Fields:
path: Array of Strings, ordered list of location_ids representing the route taken.
batch_assignments: Map/Object, mapping each batch to its destination location_id.
cost: Number, the total cost associated with the permutation.
    

Operational Flow

Adding Location(s): Add a document/documents in the Locations collection. 
Input Example:
{
{
  "Locations": [
    {
      "address": "Warehouse Road 123, 112 45 Stockholm, Sweden",
      "type": "warehouse",
      "island": "Java"
    }
    // More locations...
  ]
}

Adding Route(s): Add a document/documents in the Routes collection, specifying the start and end points using location object. 
Input Example: 
{
  "Routes": [
    {
      "from": "Document ID for location",
      "to": "Document ID for location",
      "type": "weight",
      "cost_tiers": {
        "10": 200,
        "20": 800,
        "50": 1500
      }
    }
    // More routes...
  ]
}

Adding Customer(s): Add a document/documents in the Customers collection.
Input Example:
{
  "Customers": [
    {
      "location_id": "Document ID for location",
      "name": "Internal Customer Name"
    }
    // More customers...
  ]
}

Adding an Order: Adds an order in the subcollection under customer
Input Example:
{
  "Orders": [
    {
      "location_id": "Document ID for location"
      "quantity": 100,
      "species": "alg",
      "timestamp": "2023-03-06T12:00:00Z",
      "active": true
    }
    // More orders...
  ]
}

Adding a Seller: Add a document in the Sellers collection.
Input Example:
{
  "Sellers": [
    {
      "location_id": "Document ID for location",
      "name": "Internal Seller Name"
    }
    // More sellers...
  ]
}

Adding a Batch

Input Example:
{
  "Batches": [
    {
      "location_id": "Document ID for location"
      "quantity": 500,
      "weight": 100,
      "volume": 100,
      "species": "alg",
      "cost": 100,
      "timestamp": "2023-03-06T12:00:00Z",
      "active": true
    }
    // More batches...
  ]
}


Back-End Logic

Supply Chain Management: The system uses the network graph to optimize routes and manage supply chain logistics based on the current state of batches, customer orders, and available routes.

Network Graph (Supply Chain Network)
This is a simplified Network of our supply_chain which only looks at unique location id's (type.city.island id's)

Nodes: Represent locations. 
Edges: Represent routes between locations. Edges are created based on the from and to fields in the Routes collection, with costs and other details from the route's data. 
If this data is unavailable, googlemaps calculates the cost, e.g. {type: volume, {30: 200, 60:300}} means 30m3 costs 200 euros, and 60m3 costs 300 euros
Logic for Handling Shared Locations
When adding a new location, read the serialized NetworkX object from db, update the graph based on the new location.
Filling the demand of a customer, reads the serialized NetworkX object from db. It adds the customer to the network object and returns batches that optimize profit.