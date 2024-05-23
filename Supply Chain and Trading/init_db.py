import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import pandas as pd
from datetime import datetime


# Firebase Admin SDK Initialization
#cred = credentials.Certificate("/Users/elissamskog/JupyterProjects/alginnova/Firebase/alginnova-f177f-firebase-adminsdk-1hr5k-b3cac9ea17.json")
cred = credentials.Certificate('firebase_auth_token/alginnova-f177f-firebase-adminsdk-1hr5k-b3cac9ea17.json')
firebase_admin.initialize_app(cred)

# Firestore client instance
db = firestore.client()

###Functions to upload data###

#Function to upload locations
def upload_locations(locations_data):
    for location in locations_data["Locations"]:
        try:
            # Add each location to the 'Locations' collection
            doc_ref = db.collection('Locations').add({
                'address': location['address'],
                'type': location['type'],
                'island': location['island'],
            })
            print(f"Location added with ID: {doc_ref[1].id}")
        except Exception as e:
            print(f"Failed to add location: {e}")

#Function to upload routes
def upload_routes(routes_data):
    # Assuming routes_data is a dictionary with a "Routes" key holding a list of routes
    for route in routes_data["Routes"]:
        try:
            # Add each route to the 'Routes' collection
            # Firestore will automatically generate a unique document ID
            doc_ref = db.collection('Routes').add({
                'from': route['from'],
                'to': route['to'],
                'type': route['type'],
                'costs': route['costs']
            })
            print(f"Route added with ID: {doc_ref[1].id}")
        except Exception as e:
            print(f"Failed to add route: {e}")

#Function to upload customer information
def upload_customers(customers_data):
    # Assuming customers_data is a dictionary with a "Customers" key holding a list of customer dicts
    for customer in customers_data["Customers"]:
        try:
            # Add each customer to the 'Customers' collection
            # Firestore will automatically generate a unique document ID for each customer
            doc_ref = db.collection('Customers').add({
                'location_id': customer['location_id'],
                'name': customer['name']
            })
            print(f"Customer added with ID: {doc_ref[1].id}")
        except Exception as e:
            print(f"Failed to add customer: {e}")

#Functino to upload order infromation
def upload_orders(orders_data):
    for order in orders_data["Orders"]:
        customer_id = order["customer_id"]
        # Directly parse the ISO format string to a datetime object, assuming the 'Z' timezone designator is present
        datetime_obj = datetime.fromisoformat(order["timestamp"].rstrip("Z"))
        
        order_data = {
            "quantity": order["quantity"],
            "species": order["species"],
            "timestamp": datetime_obj,  # Use the datetime object directly
            "active": order["active"]
        }
        try:
            # Add each order to the 'Orders' subcollection under the specific customer
            doc_ref = db.collection('Customers').document(customer_id).collection('Orders').add(order_data)
            print(f"Order added to customer {customer_id} with ID: {doc_ref[1].id}")
        except Exception as e:
            print(f"Failed to add order for customer {customer_id}: {e}")

#Function to upload seller information
def upload_sellers(sellers_data):
    for seller in sellers_data["Sellers"]:
        try:
            # Add each seller to the 'Sellers' collection
            doc_ref = db.collection('Sellers').add({
                'location_id': seller['location_id'],
                'name': seller['name']
            })
            print(f"Seller added with ID: {doc_ref[1].id}")
        except Exception as e:
            print(f"Failed to add seller: {e}")

#Function to upload batch information
def upload_batches(batches_data):
    for batch in batches_data["Batches"]:
        seller_id = batch["seller_id"]
        # Convert ISO format string to datetime, assuming 'Z' for UTC
        timestamp = datetime.fromisoformat(batch["timestamp"].rstrip("Z"))
        
        batch_data = {
            "location_id": batch["location_id"],
            "quantity": batch["quantity"],
            "weight": batch["weight"],
            "volume": batch["volume"],
            "species": batch["species"],
            "cost": batch["cost"],
            "timestamp": timestamp,  # Firestore handles datetime conversion
            "active": batch["active"]
        }
        try:
            # Add the batch to the 'Batches' subcollection under the specific seller
            doc_ref = db.collection('Sellers').document(seller_id).collection('Batches').add(batch_data)
            print(f"Batch added under seller {seller_id} with ID: {doc_ref[1].id}")
        except Exception as e:
            print(f"Failed to add batch for seller {seller_id}: {e}")


### Test Data ###
            
#Define your locations
locations = {
  "Locations": [
    {
      "address": "Coaster, Tj. Mas, Kec. Semarang Utara, Kota Semarang, Jawa Tengah 50174",
      "type": "port",
      "island": "Java",
      
    },
    {
      "address": "Jl. Semboja, Petengan Selatan, Bintoro, Kec. Demak, Kabupaten Demak, Jawa Tengah 59511",
      "type": "warehouse",
      "island": "Java",
      
    },
    {
      "address": "North Perak, Pabean Cantikan, Kota Surabaya, Jawa Timur 60165",
      "type": "port",
      "island": "Java",
      
    },
    {
      "address": "Jl. RE Martadinata, Tanjung, Kec. Rasanae Bar., Kab. Bima, Nusa Tenggara Barat",
      "type": "port",
      "island": "Nusa Tenggara Barat",
      
    },
    {
      "address": "Jl. Moh. Hatta No.32, Tamalabba, Kec. Ujung Tanah, Kota Makassar, Sulawesi Selatan 90163",
      "type": "port",
      "island": "Sulawesi",
      
    },
    {
      "address": "Jl. Labu Punti, Karang Dima, Labuhan Badas, Kabupaten Sumbawa, Nusa Tenggara Bar. 84316",
      "type": "port",
      "island": "Nusa Tenggara Barat",
      
    },
    {
      "address": "Bungkutoko, Abeli, Kendari City, South East Sulawesi; Sulawesi Tenggara",
      "type": "port",
      "island": "Sulawesi",
      
    },
    {
      "address": "Jl. Yos Sudarso No.16, Kel Wainitu, Kec. Nusaniwe, Kota Ambon, Maluku; Port Ambon",
      "type": "port",
      "island": "Maluku",
      
    },
    {
      "address": "Air Kelik, Damar, East Belitung Regency, Bangka Belitung Islands 33571;",
      "type": "port",
      "island": "Bangka Belitung",
      
    },
    {
      "address": "43WP+3GC, Jl. Perintis Kemerdekaan, Sawah, Kaligangsa Wetan, Kec. Brebes, Kabupaten Brebes, Jawa Tengah 52217",
      "type": "farm",
      "island": "Java",
      
    },
    {
      "address": "Jl. Raya Narogong No.79, RT.005/RW.002, Bojong Rawalumbu, Kec. Rawalumbu, Kota Bks, Jawa Barat 17116",
      "type": "farm",
      "island": "Java",
      
    },
    {
      "address": "Kecamatan Candi, Sidoarjo, Jawa Timur, Indonesia; Sidoarjo",
      "type": "farm",
      "island": "Java",
      
    },
    {
      "address": "2857+XJH, Gadingharjo, Donotirto, Kretek, Bantul Regency, Special Region of Yogyakarta 55772; Yogyakarta port",
      "type": "farm",
      "island": "Java",
      
    },
    {
      "address": ";CMP6+5HG, Labuan Kuris, Lape, Sumbawa Regency, West Nusa Tenggara",
      "type": "farm",
      "island": "Nusa Tenggara Barat",
      
    },
    {
      "address": "Dusun Bukit Tinggi Rt.003/ Rw.002, Desa, Pidang, Kec. Tarano, Kabupaten Sumbawa, Nusa Tenggara Bar",
      "type": "farm",
      "island": "Nusa Tenggara Barat",
      
    },
  ]
}

#Define Shipping information
shipping_info = { #from och to vill vara locations IDs // ändra så att den tar in adress men sparas som location_id?
  "Routes": [
    {
      "from": "D3eXYyxwtMqkq1Wib5t9", 
      "to": "HHDecIcZAiIT4LxebYlZ",
      "type": "volume",
      "costs": {
        "32.6": 1242,
        "67": 1538
      }
    },
    {
      "from": "LXqSsMeIYZ74SJzXTB8X",
      "to": "MLEV3NA8b2OAdInfRmPx",
      "type": "volume",
      "costs": {
        "32.6": 710,
        "67": 1420
      }
    },
    {
      "from": "OAGG5Th2NF74eixoE2ET",
      "to": "UC7o1ehmJ5bqoRUteInI",
      "type": "volume",
      "costs": {
        "32.6": 1301,
        "67": 2958
      }
    }
  ]
}

#Define Customer information
customer_info = { #fixa location id
  "Customers": [
    {
      "location_id": "ZjPwjkZiS4U1ZUnwG3sX",
      "name": "Alpha Corp"
    },
    {
      "location_id": "c1ZsKpkEBskPRTqBvYXP",
      "name": "Beta Industries"
    },
    {
      "location_id": "f5ypAdwO15vtigo1S33s",
      "name": "Gamma Logistics"
    },
    {
      "location_id": "jFh0NQwvTTolyVwyNPBL",
      "name": "Delta Trading"
    },
    # Add more customers as needed
  ]
}

#Define Order information
order_info = {
  "Orders": [
    {
      "customer_id": "4gSJZZhEVJ7XZN5cRiGE",
      "quantity": 100,
      "species": "algae",
      "timestamp": "2023-03-06T12:00:00Z",
      "active": True
    },
    {
      "customer_id": "9OAJDambJIG4Sys10QYG",
      "quantity": 200,
      "species": "coral",
      "timestamp": "2023-04-15T09:30:00Z",
      "active": True
    }
    #Add more orders as needed
  ]
}

#Define Seller information
seller_info = {
  "Sellers": [
    {
      "location_id": "D3eXYyxwtMqkq1Wib5t9",
      "name": "Sunrise Supplies"
    },
    {
      "location_id": "HHDecIcZAiIT4LxebYlZ",
      "name": "Oceanic Products"
    },
    {
      "location_id": "c1ZsKpkEBskPRTqBvYXP",
      "name": "Mountain View Resources"
    }
    #Add more sellers as needed
  ]
}

#Define Batch information
batch_info = {
  "Batches": [
    {
      "seller_id": "2h1BzUvc6fP5uOjdH10f",
      "location_id": "c1ZsKpkEBskPRTqBvYXP",
      "quantity": 500,
      "weight": 100,
      "volume": 100,
      "species": "algae",
      "cost": 100,
      "timestamp": "2023-03-06T12:00:00Z",
      "active": True
    },
    {
      "seller_id": "KJ8TjtiBuEqHWwUvEBx0",
      "location_id": "lpS1tLJBcCu621Xleh59",
      "quantity": 300,
      "weight": 75,
      "volume": 80,
      "species": "coral",
      "cost": 150,
      "timestamp": "2023-04-15T09:30:00Z",
      "active": False
    }
    #Add more batches as needed
  ]
}




# Call the setup function to initialize the database
#upload_locations(locations)
#upload_routes(shipping_info)
#upload_customers(customer_info)
#upload_orders(order_info)
#upload_sellers(seller_info)
#upload_batches(batch_info)

