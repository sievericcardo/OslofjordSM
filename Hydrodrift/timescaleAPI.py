import requests
import xarray as xr
import numpy as np
from opendrift.readers import reader_netCDF_CF_generic
import cftime
import psycopg2
import datetime

import pandas as pd

class QueryAPI():

    hasura_url = "http://localhost:8080/v1/graphql"
    headers = {
        "Content-Type": "application/json",
        "x-hasura-admin-secret": "mylongsecretkey"
    
    }

    # Your specific GraphQL query
    graphql_query = """
    query APIQuery {
        salinity(where: {record_time: {_gte: "2023-04-12T10:00:00+00:00", _lte: "2023-04-13T16:00:00+00:00'"}}) {
            record_time
            temperature
            conductivity
            location
        }
        turbidity(where: {record_time: {_gte: "2023-04-12T10:00:00+00:00", _lte: "2023-04-13T17:00:00+00:00'"}}) {
            record_time
            turbidity
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
            turbidity_data = response.json()["data"]["turbidity"]
            if graphql_data and turbidity_data:
                print("Response successful")

            #print(response.json())
            # Function to calculate hourly average
            def calculate_hourly_average(data, type):
                    hourly_average = {}

                    if type == "salinity":
                        for entry in data:
                            record_time = datetime.datetime.fromisoformat(entry["record_time"])
                            hour_key = record_time.replace(minute=0, second=0, microsecond=0).isoformat()

                            if hour_key not in hourly_average:
                                hourly_average[hour_key] = {
                                    "temperature_sum": 0,
                                    "conductivity_sum": 0,
                                    "count": 0
                                }

                            hourly_average[hour_key]["temperature_sum"] += entry["temperature"]
                            hourly_average[hour_key]["conductivity_sum"] += entry["conductivity"]
                            hourly_average[hour_key]["count"] += 1

                        for key, value in hourly_average.items():
                            value["temperature"] = value["temperature_sum"] / value["count"]
                            value["conductivity"] = value["conductivity_sum"] / value["count"]
                            del value["temperature_sum"]
                            del value["conductivity_sum"]
                            del value["count"]

                        return hourly_average
                    
                    else:
                        for entry in data:
                            record_time = datetime.datetime.fromisoformat(entry["record_time"])
                            hour_key = record_time.replace(minute=0, second=0, microsecond=0).isoformat()

                            if hour_key not in hourly_average:
                                hourly_average[hour_key] = {
                                    "turbidity_sum": 0,
                                    "count": 0
                                }

                            hourly_average[hour_key]["turbidity_sum"] += entry["turbidity"]
                            hourly_average[hour_key]["count"] += 1

                        for key, value in hourly_average.items():
                            value["turbidity"] = value["turbidity_sum"] / value["count"]
                            del value["turbidity_sum"]
                            del value["count"]

                        return hourly_average
                    
                # Calculate hourly average for salinity and turbidity
            salinity_hourly_avg = calculate_hourly_average(graphql_data, "salinity")
            turbidity_hourly_avg = calculate_hourly_average(turbidity_data, "turbidity")
                
            #print("Salinity Hourly Average:", salinity_hourly_avg)
            #print("Turbidity Hourly Average:", turbidity_hourly_avg)

            # Extract relevant data from GraphQL response
            
            #time = [entry["record_time"] for entry in graphql_data]
            time = [key for key, value in salinity_hourly_avg.items()]
            time2 = [key for key, value in turbidity_hourly_avg.items()]
            #print(time)
            #print(time2)

            #depth = np.full(len(time), -40)
            depth = np.linspace(0, 100, 10,  dtype=np.float64)

            # Extract latitude and longitude from the "location" field
            sensor_lats = np.array([entry["location"]["coordinates"][0] for entry in graphql_data])
            sensor_lons = np.array([entry["location"]["coordinates"][1] for entry in graphql_data])

            num_points_lat = 100  
            num_points_lon = 100  

            # Determine global min and max lat, lon
            min_lat, max_lat = np.min(sensor_lats) - 0.1, np.max(sensor_lats) + 0.1
            min_lon, max_lon = np.min(sensor_lons) - 0.1, np.max(sensor_lons) + 0.1

            # Generate the regular grid
            lat = np.linspace(min_lat, max_lat, num_points_lat)
            lon = np.linspace(min_lon, max_lon, num_points_lon)

            # Extract sea water salinity, temperature and tubidity data from the API
            sea_water_salinity_data = np.array([(value["conductivity"]) for value in salinity_hourly_avg.values()]) 
            sea_water_temperature_data = np.array([(value["temperature"]) for value in salinity_hourly_avg.values()])
            sea_water_turbidity_data = np.array([(value["turbidity"]) for value in turbidity_hourly_avg.values()])
        

            # Make sure the data is finite, otherwise set to 0.0
            is_finite_salinity = np.isfinite(sea_water_salinity_data)
            is_finite_temperature = np.isfinite(sea_water_temperature_data)
            is_finite_turbidity = np.isfinite(sea_water_turbidity_data)

            sea_water_salinity_data[~is_finite_salinity] = 0.0
            sea_water_temperature_data[~is_finite_temperature] = 0.0
            sea_water_turbidity_data[~is_finite_turbidity] = 0.0

            # Repeat the salinity, temperature and tubidity data along the depth, lat, and lon dimensions
            sea_water_salinity = np.repeat(sea_water_salinity_data[:, np.newaxis, np.newaxis, np.newaxis], len(depth), axis=1)
            sea_water_salinity = np.repeat(sea_water_salinity, len(lat), axis=2)
            sea_water_salinity = np.repeat(sea_water_salinity, len(lon), axis=3)

            sea_water_temperature = np.repeat(sea_water_temperature_data[:, np.newaxis, np.newaxis, np.newaxis], len(depth), axis=1)
            sea_water_temperature = np.repeat(sea_water_temperature, len(lat), axis=2)
            sea_water_temperature = np.repeat(sea_water_temperature, len(lon), axis=3)

            sea_water_turbidity = np.repeat(sea_water_turbidity_data[:, np.newaxis, np.newaxis, np.newaxis], len(depth), axis=1)
            sea_water_turbidity = np.repeat(sea_water_turbidity, len(lat), axis=2)
            sea_water_turbidity = np.repeat(sea_water_turbidity, len(lon), axis=3)

            # Check your time parsing operations:
            time_datetime = [cftime.datetime.strptime(t, '%Y-%m-%dT%H:%M:%S%z') for t in time]
            time_pandas = pd.date_range(start=min(time), end=max(time), freq='H')
            #print("time_pandas values:", time_pandas)

            time_units = "hours since 1970-01-01T00:00:00"
            time_float64 = cftime.date2num(time_pandas, units=time_units, calendar="gregorian")

            # Create xarray DataArray for sea_water_salinity and sea_water_temperature
            ds = xr.Dataset(
                {"sea_water_salinity": (["time", "depth", "lat", "lon"], sea_water_salinity.astype(np.float64)),
                "sea_water_temperature": (["time", "depth", "lat", "lon"], sea_water_temperature.astype(np.float64)),
                "sea_water_turbidity": (["time", "depth", "lat", "lon"], sea_water_turbidity.astype(np.float64))},
                coords={ "lat": lat, "lon": lon, "depth": depth.astype(np.float64), "time": time_float64},
            )


            ds.attrs['Conventions'] = 'CF-1.8'
            ds.attrs['standard_name_vocabulary'] = 'CF-1.8'

            # Add the standard_name attribute to the salinity and temperature variables
            ds.sea_water_salinity.attrs['standard_name'] = 'sea_water_salinity'
            ds.sea_water_temperature.attrs['standard_name'] = 'sea_water_temperature'
            ds.sea_water_turbidity.attrs['standard_name'] = 'sea_water_turbidity'

            # Add units to the sea_water_temperature variable
            ds.sea_water_temperature.attrs['units'] = 'Celsius'
            #ds["time"].attrs["units"] = "hours since 1970-01-01T00:00:00"


            # Group by hour and take the mean
            #ds_hourly_mean = ds.groupby(ds.time.dt.hour).mean(dim="time")
            #ds_hourly = ds.resample(time="1H").mean()
            ds["time"].attrs["units"] = time_units

            # Save the data to a NetCDF file
            ds.to_netcdf("hasura_data_hourly.nc")

            # Open the saved NetCDF file as a reader and check the variable attributes
            reader_salinity = reader_netCDF_CF_generic.Reader('hasura_data_hourly.nc')
            print("Creation of netCDF file successful with variables: " + str(reader_salinity.variables))
            print("===============================================\n\n")



        else:
            # Print an error message if the request was not successful
            print(f"Error: {response.status_code} - {response.text}")
            

    except requests.ConnectionError:
        print("Error: Unable to connect to the Hasura API. Please check the server.")
    except Exception as e:
        print(f"An error occurred: {e}")
