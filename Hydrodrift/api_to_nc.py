import requests
import xarray as xr
import numpy as np
from opendrift.readers import reader_netCDF_CF_generic
import cftime


hasura_url = "http://localhost:8080/v1/graphql"
headers = {
    "Content-Type": "application/json",
    "x-hasura-admin-secret": "mylongsecretkey"
   
}

# Your specific GraphQL query
graphql_query = """
query Salinity {
    salinity (limit: 10) { 
      record_time
      temperature
      conductivity
      location
    }
  }
"""

try:
    # Make a POST request to the Hasura GraphQL endpoint
    response = requests.post(hasura_url, json={"query": graphql_query}, headers=headers)


    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the GraphQL response
        graphql_data = response.json()["data"]["salinity"]
        if graphql_data:
            print("Response successful")

        # Extract relevant data from GraphQL response
        time = [entry["record_time"] for entry in graphql_data]

        depth = np.full(len(time), -40)

        # Extract latitude and longitude from the "location" field
        sensor_lats = np.array([entry["location"]["coordinates"][0] for entry in graphql_data])
        sensor_lons = np.array([entry["location"]["coordinates"][1] for entry in graphql_data])

        num_points_lat = 10  
        num_points_lon = 10  

        # Determine global min and max lat, lon
        min_lat, max_lat = np.min(sensor_lats) - 0.1, np.max(sensor_lats) + 0.1
        min_lon, max_lon = np.min(sensor_lons) - 0.1, np.max(sensor_lons) + 0.1

        # Generate the regular grid
        lat = np.linspace(min_lat, max_lat, num_points_lat)
        lon = np.linspace(min_lon, max_lon, num_points_lon)

        # Extract sea water salinity and temperature data from the API
        sea_water_salinity_data = np.array([entry["conductivity"] for entry in graphql_data])
        sea_water_temperature_data = np.array([entry["temperature"] for entry in graphql_data])

        # Make sure the data is finite, otherwise set to 0.0
        is_finite_salinity = np.isfinite(sea_water_salinity_data)
        is_finite_temperature = np.isfinite(sea_water_temperature_data)

        sea_water_salinity_data[~is_finite_salinity] = 0.0
        sea_water_temperature_data[~is_finite_temperature] = 0.0

        # Repeat the salinity and temperature data along the depth, lat, and lon dimensions
        sea_water_salinity = np.repeat(sea_water_salinity_data[:, np.newaxis, np.newaxis, np.newaxis], len(depth), axis=1)
        sea_water_salinity = np.repeat(sea_water_salinity, len(lat), axis=2)
        sea_water_salinity = np.repeat(sea_water_salinity, len(lon), axis=3)

        sea_water_temperature = np.repeat(sea_water_temperature_data[:, np.newaxis, np.newaxis, np.newaxis], len(depth), axis=1)
        sea_water_temperature = np.repeat(sea_water_temperature, len(lat), axis=2)
        sea_water_temperature = np.repeat(sea_water_temperature, len(lon), axis=3)

        # Check your time parsing operations:
        time_datetime = [cftime.datetime.strptime(t, '%Y-%m-%dT%H:%M:%S%z') for t in time]

        # Create xarray DataArray for sea_water_salinity and sea_water_temperature
        ds = xr.Dataset(
            {"sea_water_salinity": (["time", "depth", "lat", "lon"], sea_water_salinity.astype(np.float64)),
             "sea_water_temperature": (["time", "depth", "lat", "lon"], sea_water_temperature.astype(np.float64))},
            coords={"time": time_datetime, "depth": depth, "lat": lat, "lon": lon},
        )

        ds.attrs['Conventions'] = 'CF-1.8'
        ds.attrs['standard_name_vocabulary'] = 'CF-1.8'

        # Add the standard_name attribute to the salinity and temperature variables
        ds.sea_water_salinity.attrs['standard_name'] = 'sea_water_salinity'
        ds.sea_water_temperature.attrs['standard_name'] = 'sea_water_temperature'

        # Add units to the sea_water_temperature variable
        ds.sea_water_temperature.attrs['units'] = 'Celsius'

        # Save the data to a NetCDF file
        ds.to_netcdf("hasura_thermo_salinity_data.nc", format="NETCDF4_CLASSIC")

        # Open the saved NetCDF file as a reader and check the variable attributes
        reader_salinity = reader_netCDF_CF_generic.Reader('hasura_thermo_salinity_data.nc')
        print("Creation of netCDF file successful with variables: " + str(reader_salinity.variables))

    else:
        # Print an error message if the request was not successful
        print(f"Error: {response.status_code} - {response.text}")

except requests.ConnectionError:
    print("Error: Unable to connect to the Hasura API. Please check the server.")
except Exception as e:
    print(f"An error occurred: {e}")
