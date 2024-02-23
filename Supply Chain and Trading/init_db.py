import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import pandas as pd


# Firebase Admin SDK Initialization
cred = credentials.Certificate("/Users/elissamskog/JupyterProjects/alginnova/Firebase/alginnova-f177f-firebase-adminsdk-1hr5k-b3cac9ea17.json")
firebase_admin.initialize_app(cred)

# Firestore client instance
db = firestore.client()

# Function to set up the initial database structure
def setup_database(locations):
    for location_id, address in locations.items():
        location_ref = db.collection('locations').document(location_id)
        # Set the address for the location document
        location_ref.set({'address': address})
        # Initialize the 'batches' sub-collection with a placeholder if needed
        # location_ref.collection('batches').document('placeholder').set({})

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

weather_data = pd.read_excel('/Users/elissamskog/JupyterProjects/alginnova/Prices/Data/weather_data.xlsx')

# Function to upload weather data to Firestore
def upload_weather_data(df):
    for index, row in df.iterrows():
        region = row['Region']
        date = row['Date'].strftime('%Y-%m-%d')  # Format the date as a string if necessary
        weather_doc = {
            'Temperature_Max': row['Temperature_Max'],
            'Temperature_Min': row['Temperature_Min'],
            'Precipitation_Sum': row['Precipitation_Sum'],
            'Wind_Speed_Max': row['Wind_Speed_Max'],
            'Sunshine_Duration': row['Sunshine_Duration'],
            'Radiation': row['Radiation (MJ/m2)']
        }
        # Add the document to Firestore
        db.collection('weather').document(region).collection('data').document(date).set(weather_doc)


shipping_info = {
    "port.bima.java-port.smg.java": {"32.6m3": 1242, "67m3": 1538},
    "port.mksr.slwsi-port.srbya.java": {"32.6m3": 710, "67m3": 1420},
    "port.srbya.java-port.slwsi_east.slwsi": {"32.6m3": 1301, "67m3": 2958}
}

def upload_routes(shipping_info):
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
        db.collection('routes').document(route).set(route_doc)

# Call the setup function to initialize the database
#setup_database(locations)
#upload_weather_data(weather_data)
upload_routes(shipping_info)
