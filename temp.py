import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore


# Initialize Firebase Admin SDK
cred = credentials.Certificate('/Users/elissamskog/VSC/firebaseAPI/firebase_auth_token/alginnova-f177f-firebase-adminsdk-1hr5k-b3cac9ea17.json')  # Path to Firebase service account key
firebase_admin.initialize_app(cred)

# Initialize Firestore client
db = firestore.client()

# Get the single document in the Organizations collection
organizations_ref = db.collection('Organizations').limit(1).get()

if len(organizations_ref) == 0:
    raise Exception("No documents found in the Organizations collection")

# Get the document ID of the single Organization
organization_id = organizations_ref[0].id

# Read the Excel file
df = pd.read_excel('/Users/elissamskog/VSC/firebaseAPI/Alginnova Product Catalogue.xlsx')

# Process the data and insert it into Firebase
for index, row in df.iterrows():
    # Create the product dictionary based on the logic provided
    product_data = {
        'name': f"{row['Product Name']} ({row['Category']})",  # Combine Product Name and Category
        'code': row['Code Product'],                           # Code Product
        'price': row['Price USD'] if pd.notnull(row['Price USD']) else 0,  # Price USD, default to 0 if NaN
        'MOQ': row['MOQ'],                                     # Unit MOQ
        'notes': row['Company'],                               # Company as Notes
        'Biological': False                                    # Always False
    }
    
    # Add the product to the Products subcollection under the single Organization document
    db.collection('Organizations').document(organization_id).collection('Products').add(product_data)

print("Data successfully uploaded to Firebase.")