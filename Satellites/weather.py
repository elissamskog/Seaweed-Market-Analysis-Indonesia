import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
from datetime import timedelta
from datetime import datetime
import googlemaps
import time 

api_key = 'AIzaSyCxO722Ndy_YdzEz5n1REjkztSQl9vRQ18'
gmaps = googlemaps.Client(key=api_key)


def fetch_weather_data(latitude, longitude, start_date, end_date, region_name, timezone='Asia/Jakarta'):
    # Initialize caching and retry sessions
    cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # API URL
    url = "https://archive-api.open-meteo.com/v1/archive"
    
    # Parameters for the API call
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,sunshine_duration,shortwave_radiation_sum",
        "timezone": timezone
    }

    # Make the API call
    responses = openmeteo.weather_api(url, params=params)

    # Assuming a single response for simplicity, expand as needed
    response = responses[0]

    # Extracting and printing information - adjust as needed for your use
    print(f"Coordinates: {response.Latitude()}°E {response.Longitude()}°N")
    print(f"Elevation: {response.Elevation()} m asl")
    print(f"Timezone: {response.Timezone()} {response.TimezoneAbbreviation()}")
    print(f"UTC Offset: {response.UtcOffsetSeconds()} seconds")

    # Process daily data
    daily = response.Daily()
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    temperature_max = daily.Variables(0).ValuesAsNumpy()  # Assuming temperature_2m_max is the first variable requested
    temperature_min = daily.Variables(1).ValuesAsNumpy()  # Assuming temperature_2m_min is the second
    precipitation_sum = daily.Variables(2).ValuesAsNumpy()
    windspeed_max = daily.Variables(3).ValuesAsNumpy()
    sunshine_duration = daily.Variables(4).ValuesAsNumpy()
    radiation = daily.Variables(5).ValuesAsNumpy()

    # Compiling data into a DataFrame
    daily_data = pd.DataFrame({
        "Region": region_name,  # Assigning the region name to each row
        "Date": dates,
        "Temperature_Max": temperature_max,
        "Temperature_Min": temperature_min,
        "Precipitation_Sum": precipitation_sum,
        "Wind_Speed_Max": windspeed_max,
        "Sunshine_Duration": sunshine_duration,
        "Radiation (MJ/m2)": radiation
    })
    return daily_data


def fetch_forecast_data(latitude, longitude, region_name):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,sunshine_duration,shortwave_radiation_sum"
    }
    cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    # Process daily data
    daily = response.Daily()
    num_data_points = len(daily.Variables(0).ValuesAsNumpy())  # Assuming all variables have the same length

    dates = pd.date_range(
        start=datetime.now(), 
        periods=num_data_points, 
        freq='D'
    )

    # Fetching each variable
    temperature_max = daily.Variables(0).ValuesAsNumpy()
    temperature_min = daily.Variables(1).ValuesAsNumpy()
    precipitation_sum = daily.Variables(2).ValuesAsNumpy()
    windspeed_max = daily.Variables(3).ValuesAsNumpy()
    sunshine_duration = daily.Variables(4).ValuesAsNumpy()
    radiation = daily.Variables(5).ValuesAsNumpy()

    # Compile forecast data into a DataFrame
    forecast_data = pd.DataFrame({
        "Region": region_name,
        "Date": dates,
        "Temperature_Max": temperature_max,
        "Temperature_Min": temperature_min,
        "Precipitation_Sum": precipitation_sum,
        "Wind_Speed_Max": windspeed_max,
        "Sunshine_Duration": sunshine_duration,
        "Radiation (MJ/m2)": radiation
    })

    return forecast_data


def geocode_region(region):
    try:
        # Geocoding an address with region biasing to Indonesia
        geocode_result = gmaps.geocode(region, region="id")
        if geocode_result:
            latitude = geocode_result[0]["geometry"]["location"]["lat"]
            longitude = geocode_result[0]["geometry"]["location"]["lng"]
            return (latitude, longitude)
        else:
            return (None, None)
    except Exception as e:
        print("Error geocoding {}: {}".format(region, e))
        return (None, None)


def main(forecast=False):
    
    locations = pd.read_excel('Prices/Data/location_mapping.xlsx')
    regions = locations['Province'].unique()
    regions_df = pd.DataFrame(regions, columns=['Region'])
    regions_df = regions_df.dropna()
    regions_df['Latitude'], regions_df['Longitude'] = zip(*regions_df['Region'].map(geocode_region))
    print(regions_df)

    master_weather_df = pd.DataFrame()  # Initialize a master dataframe

    if forecast:
        for index, region in regions_df.iterrows():
            latitude = region['Latitude']
            longitude = region['Longitude']
            region_name = region['Region']

            # Fetch forecast data
            forecast_df = fetch_forecast_data(latitude, longitude, region_name)
            master_weather_df = pd.concat([master_weather_df, forecast_df])

        master_weather_df.to_excel("Prices/Data/forecast_data.xlsx", index=False)

    else:
        for index, region in regions_df.iterrows():
            # Assuming you have columns 'Latitude' and 'Longitude' in your regions_df
            latitude = region['Latitude']
            longitude = region['Longitude']
            region_name = region['Region']

            # Define your date range for each region
            start_date = datetime(2006, 9, 20)
            end_date = datetime.now() - timedelta(days=1)

            # Fetching weather data for the entire range might be too large a request, consider batching it
            current_date = start_date
            while current_date <= end_date:
                time.sleep(2)
                # Define batch end date, say fetching one year at a time
                batch_end_date = min(current_date + timedelta(days=365), end_date)

                # Fetch weather data for the current batch
                weather_df = fetch_weather_data(latitude, longitude, current_date.strftime('%Y-%m-%d'), batch_end_date.strftime('%Y-%m-%d'), region_name)
                master_weather_df = pd.concat([master_weather_df, weather_df])

                # Update current_date to the next batch
                current_date = batch_end_date + timedelta(days=1)


        master_weather_df['Date'] = master_weather_df['Date'].dt.strftime('%Y-%m-%d')

        master_weather_df.to_excel("Prices/Data/weather_data.xlsx", index=False, engine='xlsxwriter')



if __name__ == '__main__':
    main(forecast=False)
 