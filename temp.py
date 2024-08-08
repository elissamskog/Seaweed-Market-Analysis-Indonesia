import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate('firebase_auth_token/alginnova-f177f-firebase-adminsdk-1hr5k-b3cac9ea17.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

# Function to update documents in the Locations subcollection
def update_locations_with_country():
    # Get all documents in the Organizations collection
    organizations = db.collection('Organizations').stream()

    for org in organizations:
        org_ref = db.collection('Organizations').document(org.id)
        locations = org_ref.collection('Locations').stream()

        for location in locations:
            location_ref = org_ref.collection('Locations').document(location.id)
            location_ref.update({"country": "Indonesia"})

    print("Updated 'country' field for all documents in Locations subcollection.")

if __name__ == "__main__":
    update_locations_with_country()