import requests
import firebase_admin
from firebase_admin import credentials, storage
import io
from datetime import datetime, timedelta

def get_access_token(client_id, client_secret):
    url = "https://services.sentinel-hub.com/oauth/token"
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.post(url, data=payload, headers=headers)
    if response.ok:
        return response.json().get('access_token')
    else:
        raise Exception(f"Error obtaining token: {response.text}")

def upload_to_firebase(bucket, image_content, destination_blob_name):
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_string(image_content, content_type='image/png')
    print(f"File uploaded to {destination_blob_name}.")

def fetch_image(access_token, collection_id, time_from, time_to, geometry, bucket_name, destination_blob_name):
    url = "https://services.sentinel-hub.com/api/v1/process"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "input": {
            "bounds": {
                "properties": {
                    "crs": "http://www.opengis.net/def/crs/EPSG/0/4326"
                },
                "geometry": geometry
            },
            "data": [{
                "type": f"byoc-{collection_id}",
                "dataFilter": {
                    "timeRange": {
                        "from": time_from,
                        "to": time_to
                    }
                }
            }]
        },
        "output": {
            "width": 2000,
            "height": 2000
        },
        "evalscript": """
            //VERSION=3
            //True Color

            function setup() {
            return {
                input: ["red", "green", "blue", "dataMask"],
                output: { bands: 4 }
            };
            }

            function evaluatePixel(sample) {
            return [sample.red/3000, 
                    sample.green/3000, 
                    sample.blue/3000,
                    sample.dataMask];
            }
        """
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        # Use in-memory storage
        image_content = response.content
        print(f"Image fetched successfully.")
        
        # Upload the image to Firebase Storage
        upload_to_firebase(bucket, image_content, destination_blob_name)
    else:
        print(f"Failed to fetch image: {response.status_code} - {response.text}")

def main(event, context):
    # Initialize Firebase Admin SDK
    cred = credentials.Certificate('/path/to/serviceAccountKey.json')
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'your-bucket-name.appspot.com'
    })

    bucket = storage.bucket()
    client_id = '9a5c8df7-077a-4d3c-8705-65c9019d75ed'
    client_secret = '7yq74fjN7uIe0lq9cIuUcmQrwdfQBkVR'
    access_token = get_access_token(client_id, client_secret)

    collection_id = 'b88c67ae-a815-4854-8f87-99dd1bd01c16'

    geometry = {
      "type": "Polygon",
      "coordinates": [
        [
          [
            118.226624,
            -8.658627
          ],
          [
            118.227353,
            -8.658987
          ],
          [
            118.228168,
            -8.658966
          ],
          [
            118.228898,
            -8.659709
          ],
          [
            118.229949,
            -8.659963
          ],
          [
            118.230314,
            -8.661406
          ],
          [
            118.229928,
            -8.662912
          ],
          [
            118.228984,
            -8.665606
          ],
          [
            118.227718,
            -8.6662
          ],
          [
            118.225744,
            -8.666157
          ],
          [
            118.223877,
            -8.665988
          ],
          [
            118.222611,
            -8.665266
          ],
          [
            118.223062,
            -8.663591
          ],
          [
            118.222203,
            -8.662975
          ],
          [
            118.221796,
            -8.663251
          ],
          [
            118.221195,
            -8.662997
          ],
          [
            118.220057,
            -8.663739
          ],
          [
            118.218899,
            -8.663548
          ],
          [
            118.21774,
            -8.663803
          ],
          [
            118.217397,
            -8.660621
          ],
          [
            118.217311,
            -8.657481
          ],
          [
            118.217826,
            -8.654469
          ],
          [
            118.219221,
            -8.652051
          ],
          [
            118.219886,
            -8.652475
          ],
          [
            118.220873,
            -8.652454
          ],
          [
            118.221946,
            -8.652602
          ],
          [
            118.222632,
            -8.653111
          ],
          [
            118.221903,
            -8.655508
          ],
          [
            118.222396,
            -8.657184
          ],
          [
            118.223512,
            -8.658415
          ],
          [
            118.225057,
            -8.658754
          ],
          [
            118.226624,
            -8.658627
          ]
        ]
      ]
    } # Should be fetched from firebase
    now = datetime.utcnow()

    # Calculate the time one day ago
    time_from = now - timedelta(days=1)

    # Format the times as required by the API
    time_from = time_from.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    time_to = now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    destination_blob_name = "gs://alginnova-f177f.appspot.com/remote/sites/3/satellite_images"

    fetch_image(access_token, collection_id, time_from, time_to, geometry, bucket.name, destination_blob_name)