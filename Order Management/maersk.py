import requests
import base64


def get_maersk_token(secret, key):
    url = "https://api.maersk.com/oauth/token"
    credentials = f"{key}:{secret}"
    encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "client_credentials"
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        token_info = response.json()
        return token_info['access_token']
    else:
        response.raise_for_status()

def get_price_quote(access_token, quote_details):
    url = "https://api.maersk.com/price/v1/quotes"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.post(url, headers=headers, json=quote_details)
    return response.json()

# Example quote details
quote_details = {
    # Fill in the required details as per API documentation
}

def structure_orders(orders):
    
    return orders

def create_booking(token, booking_details, key):
    url = "https://api.maersk.com/booking/v1/bookings"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}"
    }
    
    response = requests.post(url, headers=headers, json=booking_details)
    
    if response.status_code == 200:
        return response.json()
    else:
        return {
            "status_code": response.status_code,
            "error": response.text
        }



if __name__ == '__main__':
    secret = 'gBc0yxuQQlo2M4Dr'
    key = 'NZoDXyiPvQPQo9TtTOKHv2nAkOZNkDpY'
    token = get_maersk_token(secret, key)
    booking_details = structure_orders(orders)
    create_booking(token, booking_details, key)


