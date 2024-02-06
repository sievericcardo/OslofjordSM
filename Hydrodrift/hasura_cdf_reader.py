import netCDF4 as nc
from netCDF4 import num2date
from datetime import datetime
import csv


data = nc.Dataset('hasura_thermo_salinity_data.nc', 'r+')

time_var = data.variables['time']

time_values = time_var[:]
time_datetime = [datetime.utcfromtimestamp(val) for val in time_values]


selected_vars = ["time", "lon", "lat","sea_water_salinity", "sea_water_temperature"]
for var_name in selected_vars:
    var_data = data.variables[var_name][:]
    var_size = var_data.size
    if var_name == "time":
        var_data = time_datetime
    print(f'Variable name: {var_name}')
    print(f'Data: {var_data}')
    print(f'Size: {var_size}')