import requests
import xarray as xr
import numpy as np
from opendrift.readers import reader_netCDF_CF_generic
import datetime
import pandas as pd
import json
import netCDF4 as nc


class QueryAPI():
     
    def __init__(self):
        self.results = []
        self.locationlist = []
        self.hasura_url = "http://localhost:8080/v1/graphql"
        #self.hasura_url = "http://172.17.0.1:8080/v1/graphql"
        
        self.headers = {
            "Content-Type": "application/json",
            "x-hasura-admin-secret": "mylongsecretkey",
        }

    def query_location_API(self, start_datetime, end_datetime):
        """
        Pulls relevant locations from the API
        Required variables:
            start_datetime
            end_datetime
        """   
        start_from = start_datetime
        end_to = end_datetime


        # Format the dates as strings
        date_from_str = start_from.strftime('%Y-%m-%dT%H:%M:%S+00:00')
        date_to_str = end_to.strftime('%Y-%m-%dT%H:%M:%S+00:00')

        unique_location_query = f"""
        query APIQuery {{
            salinity(where: {{record_time: {{_gte: "{date_from_str}", _lte: "{date_to_str}"}}}}, distinct_on: location) {{
                location
            }}
        }}
        """

        try:
            response = requests.post(self.hasura_url, json={"query": unique_location_query}, headers=self.headers)

            if response.status_code == 200:
                data = response.json()["data"]["salinity"]

            for entry in data:
                self.locationlist.append(entry["location"]["coordinates"])

            return self.locationlist

        except requests.ConnectionError:
            print("Error: Unable to connect to the Hasura API. Please check the server.")
            exit()
        except Exception as e:
            print(f"An error occurred: {e}")
            exit()


    def query_data_API(self, start_datetime, end_datetime):
        """
        Pulls sensordata from the API and creates a netCDF file with hourly values
        Required variables:
            start_datetime
            end_datetime
        """        
        # Set the start and end dates
        start_from = start_datetime
        end_to = end_datetime
        end_to_turbidity = end_to + datetime.timedelta(hours=1)


        # Format the dates as strings
        date_from_str = start_from.strftime('%Y-%m-%dT%H:%M:%S+00:00')
        date_to_str_salinity = end_to.strftime('%Y-%m-%dT%H:%M:%S+00:00')
        date_to_str_turbidity = end_to_turbidity.strftime('%Y-%m-%dT%H:%M:%S+00:00')

        # Your GraphQL query with variables and formatted dates
        graphql_query = f"""
        query APIQuery {{
            salinity(where: {{record_time: {{_gte: "{date_from_str}", _lte: "{date_to_str_salinity}"}}}}) {{
                temperature
                conductivity
                location
                record_time
            }}
            turbidity(where: {{record_time: {{_gte: "{date_from_str}", _lte: "{date_to_str_turbidity}"}}}}) {{
                record_time
                turbidity
                location
            }}
        }}
        """

        

        try:
            response = requests.post(self.hasura_url, json={"query": graphql_query}, headers=self.headers)

            if response.status_code == 200:
                graphql_data = response.json()["data"]["salinity"]
                turbidity_data = response.json()["data"]["turbidity"]

                if graphql_data and turbidity_data:
                    print("Response successful")

                count = 0

                for location in self.locationlist:
                    count+=1
                    filtered_salinity_data = [data for data in graphql_data if data["location"]["coordinates"] == location]
                    filtered_turbidity_data = [data for data in turbidity_data if data["location"]["coordinates"] == location]

                    # Calculate hourly average for salinity and turbidity
                    salinity_hourly_avg = self.calculate_hourly_average(filtered_salinity_data, "salinity")
                    turbidity_hourly_avg = self.calculate_hourly_average(filtered_turbidity_data, "turbidity")
    

                    if (len(salinity_hourly_avg) != len(turbidity_hourly_avg)):
                        print(f"Data mismatch: Salinity: {len(salinity_hourly_avg)} Turbidity: {len(turbidity_hourly_avg)}")

                    # Convert time strings to datetime objects
                    time = [datetime.datetime.fromisoformat(time_str) for time_str in salinity_hourly_avg.keys()]
                    

                    # Extract relevant data from GraphQL response
                    depth = np.linspace(0, 100, 10, dtype=np.float64)

                    # Extract sea water salinity, temperature, and turbidity data from the API
                    sea_water_salinity_data = np.array([(value["conductivity"]) for value in salinity_hourly_avg.values()])
                    sea_water_temperature_data = np.array([(value["temperature"]) for value in salinity_hourly_avg.values()])
                    sea_water_turbidity_data = np.array([(value["turbidity"]) for value in turbidity_hourly_avg.values()])
                    
                    sensor_lat, sensor_lon = location[1], location[0]
                    

                    num_points = 100  # number of data points along lat and lon
                    lon = np.linspace(sensor_lon - 0.1, sensor_lon + 0.1, num_points)
                    lat = np.linspace(sensor_lat - 0.1, sensor_lat + 0.1, num_points)

                    min_datetime = min(salinity_hourly_avg.keys())
                    start_date_time = datetime.datetime.fromisoformat(min_datetime.replace('T', ' ').replace('+00:00', '')).strftime('%Y-%m-%d %H:%M:%S')

                    max_datetime = max(salinity_hourly_avg.keys())
                    end_date_time = datetime.datetime.fromisoformat(max_datetime.replace('T', ' ').replace('+00:00', '')).strftime('%Y-%m-%d %H:%M:%S')


                    # Change date according to run. Husk set opp metode så man slipper endre her
                    time = pd.date_range(start_date_time, end_date_time, freq='H')  # hourly data


                    depth = np.linspace(0, 100, 10)  # change this to your depth data


                    sea_water_salinity = np.zeros((len(time), len(depth), len(lat), len(lon)))
                    sea_water_temperature = np.zeros((len(time), len(depth), len(lat), len(lon)))
                    sea_water_turbidity = np.zeros((len(time), len(depth), len(lat), len(lon)))

                    for i, key in enumerate(salinity_hourly_avg.keys()):
                        sea_water_salinity[i, :, :, :] = sea_water_salinity_data[i]
                        sea_water_temperature[i, :, :, :] = sea_water_temperature_data[i]

                    for i, key in enumerate(turbidity_hourly_avg.keys()):
                        sea_water_turbidity[i, :, :, :] = sea_water_turbidity_data[i]
                    

                    if count == 1:
                        ds = xr.Dataset(
                            {"sea_water_salinity": (("time", "depth", "lat", "lon"), sea_water_salinity),
                            "sea_water_temperature": (("time", "depth", "lat", "lon"), sea_water_temperature),
                            "sea_water_turbidity": (("time", "depth", "lat", "lon"), sea_water_turbidity)},
                            coords={"lon": lon, "lat": lat, "depth": depth, "time": time},
                        )

                    else:
                        ds += xr.Dataset(
                            {"sea_water_salinity": (("time", "depth", "lat", "lon"), sea_water_salinity),
                            "sea_water_temperature": (("time", "depth", "lat", "lon"), sea_water_temperature),
                            "sea_water_turbidity": (("time", "depth", "lat", "lon"), sea_water_turbidity)},
                            coords={"lon": lon, "lat": lat, "depth": depth, "time": time},
                        )

                ds.attrs['Conventions'] = 'CF-1.6'
                ds.attrs['standard_name_vocabulary'] = 'CF-1.6'

                # Add the standard_name attribute to the salinity variable: improtant to get environment variable
                ds.sea_water_salinity.attrs['standard_name'] = 'salinity'
                ds.sea_water_temperature.attrs['standard_name'] = 'temperature'
                ds.sea_water_turbidity.attrs['standard_name'] = 'turbidity'

                # Save the data to a NetCDF file
                ds.to_netcdf("sensor_data.nc")

                # Open the saved NetCDF file as a reader and check the variable attributes
                reader_salinity = reader_netCDF_CF_generic.Reader('sensor_data.nc')
                
                print("Creation of netCDF file successful with variables: " + str(reader_salinity.variables))
                print("===============================================\n\n")


            else:
                # Print an error message if the request was not successful
                print(f"Error: {response.status_code} - {response.text}")
                exit()

        except requests.ConnectionError:
            print("Error: Unable to connect to the Hasura API. Please check the server.")
            exit()
        except Exception as e:
            print(f"An error occurred: {e}")
            exit()
            
        
    def calculate_hourly_average(self, data, type):
        """
        Calculated hourly average
        Required variables:
            data
            type
        """      
                        
        hourly_average = {}
        # Unique locations

        if type == "salinity":
            for entry in data:
                record_time = datetime.datetime.fromisoformat(entry["record_time"])
                hour_key = record_time.replace(minute=0, second=0, microsecond=0).isoformat()

                location = entry["location"]["coordinates"]
                key = (hour_key)

                if key not in hourly_average:
                    hourly_average[key] = {
                        "temperature_sum": 0,
                        "conductivity_sum": 0,
                        "count": 0,
                        "coordinates": location  # Save location coordinates
                    }

                hourly_average[hour_key]["temperature_sum"] += entry["temperature"]
                hourly_average[hour_key]["conductivity_sum"] += entry["conductivity"]
                #hourly_average[hour_key]["coordinates"] = entry["location"]["coordinates"]
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
    

    def data_for_mutation(self, json_data):
        """
        Prepares data for mutation
        Required variables:
            json_data
        """    
        # Append the JSON data to the results list
        self.results.append(json.loads(json_data))


    def mutation_data_API(self):    
        """
        Post data to the API
        """         
        # GraphQL mutation with variables
        mutation_query = """
        mutation MyMutation($objects: [simulations_insert_input!]!) {
          insert_simulations(objects: $objects) {
            affected_rows
          }
        }
        """

        # Prepare the payload with variables
        payload = {
            "query": mutation_query,
            "variables": {
                "objects": self.results
            }
        }
        try:
            # Make the HTTP POST request
            response = requests.post(self.hasura_url, headers=self.headers, json=payload)

            # Check the response
            if response.status_code == 200:
                print("Mutation successful")
                print(response.json())
            else:
                print("Mutation failed")
                print(response.text)
                exit()
        except requests.RequestException as e:
            print(f"Error during HTTP request: {e}")
            exit()

    def reset_data_API(self):

        mutation_query = """
        mutation MyMutation {
            delete_simulations(where: {id_sim: {_gt: 0}}) {
                affected_rows
            }
        }
        """
        try:
            response = requests.post(self.hasura_url, json={"query": mutation_query}, headers=self.headers)
            if response.status_code == 200:
                print("Reset successful")
                print(response.json())
            else:
                print("Reset failed")
                print(response.text)
                exit()
        except requests.RequestException as e:
            print(f"Error during HTTP request: {e}")
            exit()

    def cdf_reader(self):
        data = nc.Dataset('hasura_data_hourly.nc', 'r+')

        time_var = data.variables['time']

        time_values = time_var[:]
        time_datetime = [datetime.utcfromtimestamp(val) for val in time_values]

        print(data.variables.keys())
        print(data.variables["time"])


        selected_vars = ["time", "lon", "lat","sea_water_salinity", "sea_water_temperature", "sea_water_turbidity"]
        for var_name in selected_vars:
            var_data = data.variables[var_name][:]
            var_size = var_data.size
            if var_name == "time":
                var_data = time_datetime
            print(f'Variable name: {var_name}')
            print(f'Data: {var_data}')
            print(f'Size: {var_size}')