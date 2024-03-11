from opendrift.models import basemodel 
from opendrift.models.oceandrift import OceanDrift 
from datetime import datetime, timedelta 
import logger

from HydroParticle import HydroParticle 
from VirtualLander import VirtualLander
import numpy as np
import csv

class HydroDrift(OceanDrift):
    

    ElementType = HydroParticle

    lander_list = []

    # Could set the z limits, but need more information
    #required_profiles_z_range = [-40, 0]

    # Setting up the required variables for the run
    required_variables = {
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
        'sea_water_temperature': {
            'fallback': 10,
            'profiles': True
        },
        'sea_water_salinity': {
            'fallback': 34,
            'profiles': True
        },
        'sea_water_turbidity': {
            'fallback': 0.42,
            'important' : True,
            'profiles' : True
        }
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
        #print(self.environment.sea_water_temperature)
        try:
            self.elements.temperature = self.environment.sea_water_temperature
        except AttributeError:
            print("Temperature data not found in environment.")

    def update_turbidity(self):
        '''
        Temperature update method for the particle using the environment data
        '''
        #print(self.environment.sea_water_turbidity)
        try:
            self.elements.turbidity = self.environment.sea_water_turbidity
        except AttributeError:
            print("Turbidity data not found in environment.")


    # ---------------------------------------------------
    # Work in progress

    def calculate_salinity_diffusion(self):
        '''
        Method to calculate diffusion of the salinity
        ''' 

        # Predefined or calculated value for diffusion
        diffusion = 0.001
        

    def calculate_temperature_diffusion(self):
        '''
        Method to calculate diffusion of the temperature
        ''' 

        # Predefined or calculated value for diffusion
        diffusion = 0.001

    def calculate_turbidity_diffusion(self):
        '''
        Method to calculate diffusion of the turbidity
        ''' 

        # Predefined or calculated value for diffusion
        diffusion = 0.001


    # ---------------------------------------------------
        


    
    def update(self):
        '''
        Method to update the particles during simulation
        ''' 
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

        # Turbidity value update 
        self.update_turbidity()

        # Lander value update
        self.update_lander()


    def get_variables(self, requested_variables, time=None,
                      x=None, y=None, z=None,
                      indrealization=None):

            requested_variables, time, x, y, z, _outside = self.check_arguments(
                requested_variables, time, x, y, z)

            nearestTime, dummy1, dummy2, indxTime, dummy3, dummy4 = \
                self.nearest_time(time)

            if hasattr(self, 'z') and (z is not None):
                # Find z-index range
                # NB: may need to flip if self.z is ascending
                indices = np.searchsorted(-self.z, [-z.min(), -z.max()])
                indz = np.arange(np.maximum(0, indices.min() - 1 -
                                            self.verticalbuffer),
                                np.minimum(len(self.z), indices.max() + 1 +
                                            self.verticalbuffer))
                if len(indz) == 1:
                    indz = indz[0]  # Extract integer to read only one layer
            else:
                indz = 0

            if indrealization == None:
                if self.realizations is not None:
                    indrealization = range(len(self.realizations))
                else:
                    indrealization = None

            # Find indices corresponding to requested x and y
            if hasattr(self, 'clipped'):
                clipped = self.clipped
            else: clipped = 0

            if self.global_coverage():
                if self.lon_range() == '0to360':
                    x = np.mod(x, 360)  # Shift x/lons to 0-360
                elif self.lon_range() == '-180to180':
                    x = np.mod(x + 180, 360) - 180 # Shift x/lons to -180-180
            indx = np.floor(np.abs(x-self.x[0])/self.delta_x-clipped).astype(int) + clipped
            indy = np.floor(np.abs(y-self.y[0])/self.delta_y-clipped).astype(int) + clipped
            buffer = self.buffer  # Adding buffer, to cover also future positions of elements
            indy = np.arange(np.max([0, indy.min()-buffer]),
                            np.min([indy.max()+buffer, self.numy]))
            indx = np.arange(indx.min()-buffer, indx.max()+buffer+1)

            if self.global_coverage() and indx.min() < 0 and indx.max() > 0 and indx.max() < self.numx:
                logger.debug('Requested data block is not continuous in file'+
                            ', must read two blocks and concatenate.')
                indx_left = indx[indx<0] + self.numx  # Shift to positive indices
                indx_right = indx[indx>=0]
                if indx_right.max() >= indx_left.min():  # Avoid overlap
                    indx_right = np.arange(indx_right.min(), indx_left.min())
                continuous = False
            else:
                continuous = True
                indx = np.arange(np.max([0, indx.min()]),
                                np.min([indx.max(), self.numx]))

            variables = {}

            for par in requested_variables:
                if hasattr(self, 'rotate_mapping') and par in self.rotate_mapping:
                    logger.debug('Using %s to retrieve %s' %
                        (self.rotate_mapping[par], par))
                    if par not in self.variable_mapping:
                        self.variable_mapping[par] = \
                            self.variable_mapping[
                                self.rotate_mapping[par]]
                var = self.Dataset.variables[self.variable_mapping[par]]

                ensemble_dim = None
                if continuous is True:
                    if True:  # new dynamic way
                        dimindices = {'x': indx, 'y': indy, 'time': indxTime, 'z': indz}
                        subset = {vdim:dimindices[dim] for dim,vdim in self.dimensions.items() if vdim in var.dims}
                        variables[par] = var.isel(subset)
                        # Remove any unknown dimensions
                        for dim in variables[par].dims:
                            if dim not in self.dimensions.values() and dim != self.ensemble_dimension:
                                logger.debug(f'Removing unknown dimension: {dim}')
                                variables[par] = variables[par].squeeze(dim=dim)
                        if self.ensemble_dimension is not None and self.ensemble_dimension in variables[par].dims:
                            ensemble_dim = 0  # hardcoded, may not work for MEPS
                    else:  # old hardcoded way
                        if var.ndim == 2:
                            variables[par] = var[indy, indx]
                        elif var.ndim == 3:
                            variables[par] = var[indxTime, indy, indx]
                        elif var.ndim == 4:
                            variables[par] = var[indxTime, indz, indy, indx]
                        elif var.ndim == 5:  # Ensemble data
                            variables[par] = var[indxTime, indz, indrealization, indy, indx]
                            ensemble_dim = 0  # Hardcoded ensemble dimension for now
                        else:
                            raise Exception('Wrong dimension of variable: ' +
                                            self.variable_mapping[par])
                # The below should also be updated to dynamic subsetting
                else:  # We need to read left and right parts separately
                    if var.ndim == 2:
                        left = var[indy, indx_left]
                        right = var[indy, indx_right]
                        variables[par] = np.ma.concatenate((left, right), 1)
                    elif var.ndim == 3:
                        left = var[indxTime, indy, indx_left]
                        right = var[indxTime, indy, indx_right]
                        variables[par] = np.ma.concatenate((left, right), 1)
                    elif var.ndim == 4:
                        left = var[indxTime, indz, indy, indx_left]
                        right = var[indxTime, indz, indy, indx_right]
                        variables[par] = np.ma.concatenate((left, right), 2)
                    elif var.ndim == 5:  # Ensemble data
                        left = var[indxTime, indz, indrealization,
                                indy, indx_left]
                        right = var[indxTime, indz, indrealization,
                                    indy, indx_right]
                        variables[par] = np.ma.concatenate((left, right), 3)

                variables[par] = np.asarray(variables[par])

                # Mask values outside domain
                variables[par] = np.ma.array(variables[par],
                                            ndmin=2, mask=False)
                # Mask extreme values which might have slipped through
                with np.errstate(invalid='ignore'):
                    variables[par] = np.ma.masked_outside(
                        variables[par], -30000, 30000)

                # Ensemble blocks are split into lists
                if ensemble_dim is not None:
                    num_ensembles = variables[par].shape[ensemble_dim]
                    logger.debug(f'Num ensembles for {par}: {num_ensembles}')
                    newvar = [0]*num_ensembles
                    for ensemble_num in range(num_ensembles):
                        newvar[ensemble_num] = \
                            np.take(variables[par],
                                    ensemble_num, ensemble_dim)
                    variables[par] = newvar

            # Store coordinates of returned points
            try:
                variables['z'] = self.z[indz]
            except:
                variables['z'] = None
            if self.projected is True:
                variables['x'] = \
                    self.Dataset.variables[self.xname][indx]*self.unitfactor
                variables['y'] = \
                    self.Dataset.variables[self.yname][indy]*self.unitfactor
            else:
                variables['x'] = indx
                variables['y'] = indy
            variables['x'] = np.asarray(variables['x'], dtype=np.float32)
            variables['y'] = np.asarray(variables['y'], dtype=np.float32)

            variables['time'] = nearestTime

            # Rotate any east/north vectors if necessary
            if hasattr(self, 'rotate_mapping'):
                if self.y_is_north() is True:
                    logger.debug('North is up, no rotation necessary')
                else:
                    rx, ry = np.meshgrid(variables['x'], variables['y'])
                    lon, lat = self.xy2lonlat(rx, ry)
                    from opendrift.readers.basereader import vector_pairs_xy
                    for vectorpair in vector_pairs_xy:
                        if vectorpair[0] in self.rotate_mapping and vectorpair[0] in variables.keys():
                            if self.proj.__class__.__name__ == 'fakeproj':
                                logger.warning('Rotation from fakeproj is not yet implemented, skipping.')
                                continue
                            logger.debug(f'Rotating vector from east/north to xy orientation: {vectorpair[0:2]}')
                            variables[vectorpair[0]], variables[vectorpair[1]] = self.rotate_vectors(
                                lon, lat, variables[vectorpair[0]], variables[vectorpair[1]],
                                pyproj.Proj('+proj=latlong'), self.proj)

            if hasattr(self, 'shift_x'):
                # "hidden feature": if reader.shift_x and reader.shift_y are defined,
                # the returned fields are shifted this many meters in the x- and y directions
                # E.g. reader.shift_x=10000 gives a shift 10 km eastwards (if x is east direction)
                if self.proj.crs.is_geographic:  # meters to degrees
                    shift_y = (self.shift_y/111000)
                    shift_x = (self.shift_x/111000)*np.cos(np.radians(variables['y']))
                    logger.info('Shifting x between %s and %s' % (shift_x.min(), shift_x.max()))
                    logger.info('Shifting y with %s m' % shift_y)
                else:
                    shift_x = self.shift_x
                    shift_y = self.shift_y
                    logger.info('Shifting x with %s m' % shift_x)
                    logger.info('Shifting y with %s m' % shift_y)
                variables['x'] += shift_x
                variables['y'] += shift_y

            return variables
    
    
 
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
        min_location = [59.00, 10.00]
        max_location = [59.95, 11.00]

        location_lat_list=[]
        location_lon_list=[]


        curr_lat = min_location[0]
        while curr_lat < max_location[0]:
            location_lat_list.append(np.round(curr_lat,2))
            curr_lat += size_lat
        
        location_lat_list.append(np.round(curr_lat, 2))

        curr_lon = min_location[1]
        while curr_lon < max_location[1]:
            location_lon_list.append(np.round(curr_lon, 2))
            curr_lon += size_lon
        
        location_lon_list.append(np.round(curr_lon, 2))

        #print(location_lat_list)
        #print(location_lon_list)

        id = 1

        for lon in range(len(location_lon_list)):
            for lat in range(len(location_lat_list)):

                if not (lat == len(location_lat_list)-1 or lon == len(location_lon_list)-1):
                    lander = VirtualLander(id)
                    lander.create_lander(location_lat_list[lat], location_lat_list[lat+1], location_lon_list[lon], location_lon_list[lon+1], starttime, seed_length) 
                    self.lander_list.append(lander)
                    id+=1

        print(str(len(self.lander_list)) + " landers have been created!")
        print("===============================================\n\n")


    def update_lander(self):
        '''
        Method to cupdate lander values
        '''
        current_sim_time = self.time
          
        for i in range(len(self.elements.ID)):
            for lander in self.lander_list:
                if (lander.contains(self.elements.lat[i], self.elements.lon[i])):
                    lander.update_lander(self.elements.salinity[i], self.elements.temperature[i], self.elements.turbidity[i], current_sim_time)
                    

    def smooth_landerlist(self):
        '''
        Method to smoothen the values of the landers. This wil only affect the landers with the change set to True
        '''
        for lander in self.lander_list:
            if lander.change == True:
                lander.smoother()
                

    def write_landers_to_csv(self):
        '''
        Converting the landerlist to a CSV file
        '''
        with open('lander_results.csv', 'w', newline='') as file:
            writer = csv.writer(file)

            for lander in self.lander_list:
                #if lander.change == True:              
                    writer.writerow([f"Lander {lander.id} has center location {lander.center_lat} {lander.center_lon}"])
                    writer.writerow([f"Grid size Min: {lander.minlon} {lander.minlat}, Max: {lander.maxlon} {lander.maxlat}"])
                    for ind in range(lander.seed_length):
                        writer.writerow([f"Datetime: {lander.arr_datetime[ind]}"])
                        writer.writerow([f"Salinity: {lander.arr_salinity[ind]}"])
                        writer.writerow([f"Temperature: {lander.arr_temperature[ind]}"])
                        writer.writerow([f"Turbidity: {lander.arr_turbidity[ind]}"])
                        writer.writerow([f"Status of update {lander.arr_change[ind]}"])
                        writer.writerow(["\n"])
                    writer.writerow(["\n\n\n"])


    def suppress_qt_warnings(self): 
        from os import environ 
        environ["QT_DEVICE_PIXEL_RATIO"] = "0" 
        environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1" 
        environ["QT_SCREEN_SCALE_FACTORS"] = "1" 
        environ["QT_SCALE_FACTOR"] = "1"

