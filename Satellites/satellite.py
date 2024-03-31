import requests
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


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

def create_AOI_subscription(name, access_token, bbox, planetApiKey, max_cloud_coverage=20):
    url = "https://services.sentinel-hub.com/api/v1/dataimport/tiledeliveries"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    start_date = datetime.now() - timedelta(days=1)
    end_date = datetime.now() + relativedelta(years=1)

    start_date_str = start_date.strftime('%Y-%m-%dT00:00:00Z')
    end_date_str = end_date.strftime('%Y-%m-%dT23:59:59Z')

    data_filter = {
        "timeRange": {
            "from": start_date_str,
            "to": end_date_str
        },
        "maxCloudCoverage": max_cloud_coverage
    }

    payload = {
        "name": name,
        "input": {
            "provider": "PLANET",
            "planetApiKey": planetApiKey,
            "bounds": {
                "bbox": bbox
            },
            "data": [{
                "productBundle": "analytic_sr_udm2",
                "type": "PSScene",
                "dataFilter": data_filter
            }]
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    return response.json()

def confirm_subscription(access_token, subscription_id):
    url = f"https://services.sentinel-hub.com/api/v1/dataimport/subscriptions/{subscription_id}/confirm"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers)

    if response.ok:
        return response.json()  # Confirmation successful
    else:
        raise Exception(f"Error confirming subscription: {response.text}")


def fetch_latest_delivery(access_token, subscription_id):
    url = f"https://services.sentinel-hub.com/api/v1/dataimport/subscriptions/{subscription_id}/deliveries"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    # Fetch the list of deliveries for the subscription
    response = requests.get(url, headers=headers)
    if response.ok:
        deliveries = response.json()

        # Assuming the deliveries are sorted by date, or you can sort them
        latest_delivery = deliveries[0]  # Assuming the first one is the latest

        return latest_delivery
    else:
        raise Exception(f"Error fetching deliveries: {response.text}")


def fetch_latest_image(access_token, subscription_id):
    latest_delivery = fetch_latest_delivery(access_token, subscription_id)
    delivery_id = latest_delivery['id']

    url = f"https://services.sentinel-hub.com/api/v1/dataimport/subscriptions/{subscription_id}/deliveries/{delivery_id}/files"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.get(url, headers=headers)
    if response.ok:
        return response.content
    else:
        raise Exception(f"Error retrieving file: {response.text}")


def main():
    # From Sentinelhub under user settings, admin credentials
    client_id = '9a5c8df7-077a-4d3c-8705-65c9019d75ed'
    client_secret = '7yq74fjN7uIe0lq9cIuUcmQrwdfQBkVR'
    access_token = get_access_token(client_id, client_secret)

    # bbox is the longitude, latitude coordinates for the corner vertices of the desired area
    planetApiKey = 'PLAK7b3c47495b4e48a4848b0aed067d8fae'
    bbox = [13.822174072265625, 45.85080395917834, 
            14.55963134765625, 46.29191774991382]
    name = 'UserXCollection'

    # Creates a subscription
    subscription_response = create_AOI_subscription(access_token, bbox, planetApiKey)
    subscription_id = subscription_response['id']

    # There should be a manual response to confirm the subscription from an admin
    confirmation_response = confirm_subscription(access_token, subscription_id)

    # Every 24 hours the latest image is found
    image_data = fetch_latest_image(access_token, subscription_id)

if __name__ == '__main__':
    main()