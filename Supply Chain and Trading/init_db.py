import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import pandas as pd


# Firebase Admin SDK Initialization
#cred = credentials.Certificate("/Users/elissamskog/JupyterProjects/alginnova/Firebase/alginnova-f177f-firebase-adminsdk-1hr5k-b3cac9ea17.json")
cred = credentials.Certificate("C:/Users/August/alginnova_jobb/firebaseAPI/firebase_auth_token/alginnova-f177f-firebase-adminsdk-1hr5k-b3cac9ea17.json")
firebase_admin.initialize_app(cred)

# Firestore client instance
db = firestore.client()

'''# Function to set up the initial database structure
def setup_database(locations):
    for location_id, address in locations.items():
        location_ref = db.collection('locations').document(location_id)
        # Set the address for the location document
        location_ref.set({'address': address}) 
        # Initialize the 'batches' sub-collection with a placeholder if needed
        # location_ref.collection('batches').document('placeholder').set({})'''

###Functions to upload data###

#Function to upload locations
def upload_locations(locations):
    counter = 1
    for location_id, address in locations.items():
        # Generate a unique identifier in the format "location_001"
        unique_id = f"location_{counter:03}"

        # Extract the type from location_id or another logic if applicable
        # Assuming the type is the first part of the location_id before the first '.'
        location_type = location_id.split('.')[0] if '.' in location_id else "unknown"
       
        # Prepare the document data
        doc_data = {
            'address': address,
            'location_id': location_id,  # Optional, if you still want to keep track of the original location ID
            'type': location_type,  # Add the type to the document
        }
        try:
            # Use unique_id as the document ID
            db.collection('locations').document(unique_id).set(doc_data)
            print(f"Added document with unique identifier {unique_id} and type {location_type}")
        except Exception as e:
            print(f"Failed to add document with unique identifier {unique_id}: {e}")

        counter += 1  # Increment the counter for the next unique identifier


'''def upload_routes(shipping_info):
    for route, volumes in shipping_info.items():
        # Split the route string into 'from' and 'to' locations
        from_location, to_location = route.split('-')
        # Create a document for each route
        route_doc = {
            'from': from_location,
            'to': to_location,
            'volumes': volumes
        }
        # Add the document to Firestore
        db.collection('routes').document(route).set(route_doc)'''

#Function to upload routes
def upload_routes(shipping_info):
    counter = 1  # Counter for unique route identifiers/ måste hitta ett nytt sätt att göra unique identifiers senare

    for route, volumes in shipping_info.items():
        # Generate a unique identifier for the route
        unique_route_id = f"route_{counter:03}"

        # Split the route string into 'from' and 'to' locations, removing type part
        from_location, to_location = route.split('-')
        from_location_cleaned = '.'.join(from_location.split('.')[1:])
        to_location_cleaned = '.'.join(to_location.split('.')[1:])

        # Determine the type (assuming volume if 'm3' is present)
        route_type = 'volume' if any('m3' in key for key in volumes.keys()) else 'weight'

        # Prepare the route document
        route_doc = {
            'from': from_location_cleaned,
            'to': to_location_cleaned,
            'type': route_type,
            'costs': volumes
        }
        try:
            # Use unique_route_id as the document ID
            db.collection('routes').document(unique_route_id).set(route_doc)
            print(f"Added route document with ID {unique_route_id}")
        except Exception as e:
            print(f"Failed to add route document {unique_route_id}: {e}")

        counter += 1  # Increment for the next route

#Function to upload customer information
def upload_customer_info(customer_info):
     for customer_id, info in customer_info.items():
        try:
            # Use customer_id as the document ID and set the fields for the customer
            db.collection('customers').document(customer_id).set({
                'address': info['address'],
                'location_id': info['location_id'],
                'quantity_required': info['quantity_required'],
                'species': info['species']
            })
            print(f"Added customer document with ID {customer_id}")
        except Exception as e:
            print(f"Failed to add customer document {customer_id}: {e}")

#Function to upload batch information
def upload_batch_info(batch_info):
    for batch_id, info in batch_info.items():
        try:
            # Use batch_id as the document ID and set the fields for the batch
            db.collection('batches').document(batch_id).set({
                'location_id': info['location_id'],
                'quantity': info['quantity'],
                'weight': info['weight'],
                'volume': info['volume'],
                'species': info['species']
            })
            print(f"Added batch document with ID {batch_id}")
        except Exception as e:
            print(f"Failed to add batch document {batch_id}: {e}")

### Test Data ###
# Define your locations
locations = {
            "port.smg.java": "Coaster, Tj. Mas, Kec. Semarang Utara, Kota Semarang, Jawa Tengah 50174",
            "wareh.smg.java": "Jl. Semboja, Petengan Selatan, Bintoro, Kec. Demak, Kabupaten Demak, Jawa Tengah 59511",
            "port.srbya.java": "North Perak, Pabean Cantikan, Kota Surabaya, Jawa Timur 60165",
            "port.bima.java": "Jl. RE Martadinata, Tanjung, Kec. Rasanae Bar., Kab. Bima, Nusa Tenggara Barat",
            "port.mksr.slwsi": "Jl. Moh. Hatta No.32, Tamalabba, Kec. Ujung Tanah, Kota Makassar, Sulawesi Selatan 90163",
            "port.smbwa.smbwa": "Jl. Labu Punti, Karang Dima, Labuhan Badas, Kabupaten Sumbawa, Nusa Tenggara Bar. 84316",
            "port.slwsi_east.slwsi": "Bungkutoko, Abeli, Kendari City, South East Sulawesi; Sulawesi Tenggara",
            "port.ambon.maluku": "Jl. Yos Sudarso No.16, Kel Wainitu, Kec. Nusaniwe, Kota Ambon, Maluku; Port Ambon",
            "port.belitung.maluku": "Air Kelik, Damar, East Belitung Regency, Bangka Belitung Islands 33571;",
            "farm.grc.brebes.java": "43WP+3GC, Jl. Perintis Kemerdekaan, Sawah, Kaligangsa Wetan, Kec. Brebes, Kabupaten Brebes, Jawa Tengah 52217",
            "farm.grc.bekasi.java": "Jl. Raya Narogong No.79, RT.005/RW.002, Bojong Rawalumbu, Kec. Rawalumbu, Kota Bks, Jawa Barat 17116",
            "farm.grc.sidoarjo.java": "Kecamatan Candi, Sidoarjo, Jawa Timur, Indonesien; Sidoarjo",
            "farm.ulva.ygya.java": "2857+XJH, Gadingharjo, Donotirto, Kretek, Bantul Regency, Special Region of Yogyakarta 55772; Yogyakarta port",
            "farm.ctni.smbwa.smbwa": ";CMP6+5HG, Labuan Kuris, Lape, Sumbawa Regency, West Nusa Tenggara",
            "farm.ctni.smbwa.smbwa": "Dusun Bukit Tinggi Rt.003/ Rw.002, Desa, Pidang, Kec. Tarano, Kabupaten Sumbawa, Nusa Tenggara Bar",
            "farm.ctni.ambon.maluku": ";9993+CM, Tial, Salahutu, Central Maluku Regency, Maluku",
            "farm.ctni.belitung.maluku": ";Jl. Tj. Ruu, Pegantungan, Badau, Kabupaten Belitung, Kepulauan Bangka Belitung 33452",
            "farm.grc_ulva.bima.smbwa": ";Jl. Lintas Sape - Wera, Lamere, Kec. Sape, Kabupaten Bima, Nusa Tenggara Bar. 84182; Bima Regency",
            "farm.grc_ulva_ctni.mksr.slwsi": "Dusun Sampulungan Caddi, Desa Sampulungan, Kec. Galesong Utara, Kabupaten Takalar, Sulawesi Selatan 92255"
        }

#Define Shipping information
shipping_info = {
    "port.bima.java-port.smg.java": {"32.6m3": 1242, "67m3": 1538},
    "port.mksr.slwsi-port.srbya.java": {"32.6m3": 710, "67m3": 1420},
    "port.srbya.java-port.slwsi_east.slwsi": {"32.6m3": 1301, "67m3": 2958}
}

#Define Customer information
customer_info = {
    "customer_001": {
        "address": "Jl. Semboja, Petengan Selatan, Bintoro, Kec. Demak, Kabupaten Demak, Jawa Tengah 59511",
        "location_id": "wareh.smg.java",
        "quantity_required": 500,
        "species": "Alg"
    },
    "customer_002": {
        "address": "Dusun Bukit Tinggi Rt.003/ Rw.002, Desa, Pidang, Kec. Tarano, Kabupaten Sumbawa, Nusa Tenggara Bar",
        "location_id": "farm.ctni.smbwa.smbwa",
        "quantity_required": 300,
        "species": "Älg"
    },
    "customer_003": {
        "address": ";Jl. Lintas Sape - Wera, Lamere, Kec. Sape, Kabupaten Bima, Nusa Tenggara Bar. 84182; Bima Regency",
        "location_id": "farm.grc_ulva.bima.smbwa",
        "quantity_required": 250,
        "species": "Elg"
    },
    "customer_004": {
        "address": "Bungkutoko, Abeli, Kendari City, South East Sulawesi; Sulawesi Tenggara",
        "location_id": "port.slwsi_east.slwsi",
        "quantity_required": 150,
        "species": "Aulg"
    }
}

batch_info = {"batch_001" : {
    "location_id": "wareh.smg.java",
     "quantity": 500,
     "weight": 100,
     "volume": 100,
     "species": "Alg"
     },
     "batch_002" : {
    "location_id": "farm.grc_ulva.bima.smbwa",
     "quantity": 500,
     "weight": 100,
     "volume": 100,
     "species": "Alg"
     },
     "batch_003" : {
    "location_id": "port.slwsi_east.slwsi",
     "quantity": 500,
     "weight": 100,
     "volume": 100,
     "species": "Alg"
     },
     "batch_004" : {
    "location_id": "farm.ctni.smbwa.smbwa",
     "quantity": 500,
     "weight": 100,
     "volume": 100,
     "species": "Alg"
     },
}




#Function to setup entire database  
def setup_database():
    upload_locations(locations)
    upload_routes(shipping_info)
    upload_customer_info(customer_info)
    upload_batch_info(batch_info)


# Call the setup function to initialize the database
setup_database()
#setup_locations(locations)
#upload_weather_data(weather_data)
#upload_routes(shipping_info)
