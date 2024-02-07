from opendrift.models import basemodel 
from opendrift.models.oceandrift import OceanDrift 
from datetime import datetime, timedelta 
from opendrift.readers import reader_netCDF_CF_generic, reader_netCDF_CF_unstructured, reader_timeseries

from HydroParticle import HydroParticle 
from VirtualLander import VirtualLander
import numpy as np

import sys

class HydroDrift(OceanDrift):
    

    ElementType = HydroParticle

    lander_list = []

    # Could set the z limits, but need more information
    #required_profiles_z_range = [-40, 0]

    # Setting up the required variables for the run
    required_variables = {
        'sea_water_salinity': {
            'fallback': 20.0
        },
        'x_sea_water_velocity': {
            'fallback': None
        },
        'y_sea_water_velocity': {
            'fallback': None
        },
        'x_wind': {
            'fallback': None
        },
        'y_wind': {
            'fallback': None
        },
        'upward_sea_water_velocity': {
            'fallback': 0,
            'important': False
        },
        'sea_surface_wave_significant_height': {
            'fallback': 0,
            'important': False
        },
        'sea_surface_wave_stokes_drift_x_velocity': {
            'fallback': 0,
            'important': False
        },
        'sea_surface_wave_stokes_drift_y_velocity': {
            'fallback': 0,
            'important': False
        },
        'sea_surface_wave_period_at_variance_spectral_density_maximum': {
            'fallback': 0,
            'important': False
        },
        'sea_surface_wave_mean_period_from_variance_spectral_density_second_frequency_moment':
        {
            'fallback': 0,
            'important': False
        },
        'sea_ice_area_fraction': {
            'fallback': 0,
            'important': False
        },
        'sea_ice_x_velocity': {
            'fallback': 0,
            'important': False
        },
        'sea_ice_y_velocity': {
            'fallback': 0,
            'important': False
        },
        'sea_water_temperature': {
            'fallback': 10,
            'profiles': True
        },
        'sea_water_salinity': {
            'fallback': 34,
            'profiles': True
        },
        'sea_floor_depth_below_sea_level': {
            'fallback': 10000
        },
        'ocean_vertical_diffusivity': {
            'fallback': 0.02,
            'important': False,
            'profiles': True
        },
        'land_binary_mask': {
            'fallback': None
        },
        'ocean_mixed_layer_thickness': {
            'fallback': 50,
            'important': False
        },
    }


 

    def print_environment_variables(self) :
        '''
        Print method for all the available environment variable names
        '''


        field_names = self.environment.dtype.names
        for name in field_names:
            print(f"{name}: {self.environment[name]}")
    

    def update_salinity(self):
        '''
        Salinity update method for the particle using the environment data
        '''
        try:
            self.elements.salinity = self.environment.sea_water_salinity
        except AttributeError:
            print("Salinity data not found in environment.")


    def update_temperature(self):
        '''
        Temperature update method for the particle using the environment data
        '''
        try:
            self.elements.temperature = self.environment.sea_water_temperature
        except AttributeError:
            print("Temperature data not found in environment.")

    

    
    def update(self):
        # Simply move particles with ambient current
        self.advect_ocean_current()

        # Advect particles due to surface wind drag,
        # according to element property wind_drift_factor
        self.advect_wind()

        # Stokes drift
        self.stokes_drift()

        # Turbulent Mixing
        if self.get_config('drift:vertical_mixing') is True:
            self.update_terminal_velocity()
            self.vertical_mixing()
        else:  # Buoyancy
            self.vertical_buoyancy()

        # Vertical advection
        self.vertical_advection()

        # Optional machine learning correction
        self.machine_learning_correction()
    
        # Salinity value update
        self.update_salinity()

        # Temperature value update
        self.update_temperature()

        # Lander value update
        self.update_lander()


    def get_variables(self, variables, time=None,
                  x=None, y=None, z=None):
        
        variables_dict = {}

        if 'sea_water_salinity' in variables:

            salinity_values = self.data_source.get_salinity(time, x, y, z)

            variables_dict['sea_water_salinity'] = salinity_values

        return variables_dict
    
    
 
    def create_landers_from_list(self, starttime, seed_length, size_lat, size_lon):
        '''
        Method to create landers from a predefined list.
        Required variables:
            starttime
            seed_length
            size_lat
            size_lon

        '''

        # Predefined area
        min_location = [59.652879, 10.489808]
        max_location = [59.917570, 10.770731]

        location_lat_list=[]
        location_lon_list=[]


        curr_lat = min_location[0]
        while curr_lat < max_location[0]:
            location_lat_list.append(curr_lat)
            curr_lat += size_lat
        
        location_lat_list.append(curr_lat)

        curr_lon = min_location[1]
        while curr_lon < max_location[1]:
            location_lon_list.append(curr_lon)
            curr_lon += size_lon
        
        location_lon_list.append(curr_lon)

        id = 0

        for lat in range(len(location_lat_list)):
            for lon in range(len(location_lon_list)):

                if not (lat == len(location_lat_list)-1 or lon == len(location_lon_list)-1):
                    lander = VirtualLander(id)
                    lander.create_lander(location_lat_list[lat], location_lat_list[lat+1], location_lon_list[lon], location_lon_list[lon+1], starttime, seed_length) 
                    self.lander_list.append(lander)
                    id+=1




        #location_lat_list = [59.658233, 59.683, 60.000, 59.847925]
        #location_lon_list = [10.624583, 10.603, 10.603, 10.614980]

        # for ind in range(len(location_lat_list)):
        #    lander = VirtualLander(ind)
        #    lander.create_lander(location_lat_list[ind], location_lon_list[ind], starttime, seed_length) 
        #    self.lander_list.append(lander)


    def update_lander(self):
        '''
        Method to check if paticle is in any lander area and the updating the lander value
        
        '''
        current_sim_time = self.time
          
        for i in range(len(self.elements.ID)):
            for lander in self.lander_list:
                if (lander.contains(self.elements.lat[i], self.elements.lon[i])):
                    lander.update_lander(self.elements.salinity[i], self.elements.temperature[i], current_sim_time)
                    



def suppress_qt_warnings(): 
    from os import environ 
    environ["QT_DEVICE_PIXEL_RATIO"] = "0" 
    environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1" 
    environ["QT_SCREEN_SCALE_FACTORS"] = "1" 
    environ["QT_SCALE_FACTOR"] = "1"


if __name__ == "__main__": 
    suppress_qt_warnings()

    o = HydroDrift(loglevel=30)

    # Currently static but need to fix it dynamically when we get the correct pos    
    lat = 59.658233
    lon = 10.624583
    seed_length = 24


    # Load API data from NetCDF file 
    filename = 'hasura_thermo_salinity_data.nc'
    salinity_reader = reader_netCDF_CF_generic.Reader(filename)
    #print('Salinity variable name:', salinity_reader.variable_mapping['sea_water_salinity'])
    #print('Temperature variable name:', salinity_reader.variable_mapping['sea_water_temperature'])

    print("----------------------------------------------------------------")

    o.add_reader(salinity_reader)
   
    o.add_readers_from_list(
    ['https://thredds.met.no/thredds/dodsC/sea/norkyst800m/1h/aggregate_be'])


    t1 = datetime(2023, 4, 12)
    t2 = t1 + timedelta(hours=seed_length)
    
    print(o.get_variables)
    
    number = 1
    o.seed_elements(lon=lon, lat=lat, time=[t1, t2],
                    number=200, radius=200, z=-40)

    seed_times = o.elements_scheduled_time[0:number]

    # Remember time:units = "seconds since 1970-01-01 00:00:00" ;
    size_lat = 0.02
    size_lon = 0.02
    o.create_landers_from_list(t1,seed_length, size_lat, size_lon)


    # 30 min interval in 188 hours until all particles deactivate or timeout
    o.run(time_step=timedelta(minutes=60), duration=timedelta(hours=seed_length), outfile='output_file.nc')
  
    print("---------------------------------------------------------------------------------")
    for lander in o.lander_list:
        if lander.change == True:
            lander.smoother()
            lander.print_lander()
            #o.seed_elements(lon=lander.center_lon, lat=lander.center_lat, time=t1, number=100000)

    

    #o.write_netcdf_density_map('output_filename.nc')
    o.animation(fast=True, filename='hydrodrift_sim_vis.mp4')
 

    