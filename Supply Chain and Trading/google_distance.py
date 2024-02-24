import googlemaps
from datetime import datetime


def compute_distance(location, destination):
    arrival_time = datetime.now()
    gmaps = googlemaps.Client(key='AIzaSyCxO722Ndy_YdzEz5n1REjkztSQl9vRQ18')
    distance_result = gmaps.distance_matrix(location, destination, mode="driving", arrival_time=arrival_time)

    distance_info = distance_result['rows'][0]['elements'][0]['distance']
    distance_value_km = distance_info['value']/1000
    return distance_value_km