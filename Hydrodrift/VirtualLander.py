import numpy as np
from datetime import datetime, timedelta 

class VirtualLander():
    '''
    variables:
    - Time
    - Location
    - Change 
    - Salinity
    - Temperature
    '''
    maxlat, minlat, maxlon, minlon, center_lat, center_lon = 0, 0, 0, 0, 0, 0
    
    df_salinity = 20
    df_temperature = 8

    arr_salinity = []
    arr_temperature = []
    arr_datetime = []
    arr_change = []

    change = False
    starttime = None
    id= 0
    seed_length = 0

    def __init__(self, id):
        self.id = id
       


    def create_lander(self, min_lat, max_lat, min_lon, max_lon, starttime, seed_length):
        '''
        Method to create a single lander
        Required variables:
            lat
            lon
            starttime
        '''
        # Variable for the size of per grid

        self.starttime = starttime
        self.seed_length = seed_length

        self.maxlat = max_lat
        self.minlat = min_lat
        self.maxlon = max_lon
        self.minlon = min_lon

        self.calculate_center(max_lat, min_lat, max_lon, min_lon)

        self.arr_salinity = np.full(seed_length, self.df_salinity, dtype=np.float32)
        self.arr_temperature = np.full(seed_length, self.df_temperature, dtype=np.float32)
        self.arr_change = np.full(seed_length, False)
        print(starttime)
        self.arr_datetime = np.full(seed_length, (starttime))

        for i in range(seed_length):
            self.arr_datetime[i] =  (starttime) + timedelta(hours=i)

        print(f"Lander {self.id} is created")

    def update_lander(self, sim_salinity, sim_temperature, sim_time):
        '''
        Method to update the landers Salinity and Temperature
        Required variables:
            salinity
            temperature
            current run time
        
        '''
        
        time_difference = (sim_time - self.starttime)
        

        duration = int(time_difference.total_seconds() / 3600)

        self.change = True
        
        if self.arr_change[duration] == False:
            self.arr_salinity[duration] = sim_salinity
            self.arr_temperature[duration] = sim_temperature
            self.arr_change[duration] = True
            #print(f"Lander {self.id} values updated.")

        else:
            curr__salinity = self.arr_salinity[duration]
            new_salinity = np.float32((curr__salinity + sim_salinity)/2)
            self.arr_salinity[duration] = new_salinity

            curr__temperature = self.arr_temperature[duration]
            new_temperature = np.float32((curr__temperature + sim_temperature)/2)
            self.arr_temperature[duration] = new_temperature
            #print(f"Lander {self.id} values updated.")


    def contains(self, lat, lon):
        '''
        Method to check if current particle is in the lander's area
        Required variables:
            lat
            lon
        '''

        if not (self.minlat <= lat <= self.maxlat and self.minlon <= lon <= self.maxlon):
            return False
        else:
            return True
    
        
    def smoother(self):
        '''
        Smoothing method for the lander values.
        The Change-value will not be changed, but rather fill in the default values with estimated values.
        (Only if its logical)
        
        '''
        for i in range(self.seed_length):
            if i == 0 or self.arr_change[i] == True: #må endre or self.arr_change[i-1] == False
                continue
                #skip
            
            elif self.arr_change[i] == False  and (self.arr_change[i-1] == True or (self.arr_salinity[i-1] != self.df_salinity and self.arr_temperature[i-1] != self.df_temperature)):
                    next_changed_index = i+1

                    while next_changed_index < self.seed_length:
                        if self.arr_change[next_changed_index] == True:
                            self.arr_salinity[i] = np.float32((self.arr_salinity[i-1] + self.arr_salinity[next_changed_index])/2)
                            self.arr_temperature[i] = np.float32((self.arr_temperature[i-1] + self.arr_temperature[next_changed_index])/2)
                            break
                        
                        next_changed_index= next_changed_index+1

                    if self.arr_salinity[i] == self.df_salinity and self.arr_temperature[i] == self.df_temperature:
                        self.arr_salinity[i] = np.float32(self.arr_salinity[i-1])
                        self.arr_temperature[i] = np.float32(self.arr_temperature[i-1])

    def calculate_center(self, max_lat, min_lat, max_lon, min_lon):
        self.center_lat = (max_lat + min_lat) / 2
        self.center_lon = (max_lon + min_lon) / 2
        
        
    def print_lander(self):      
        print(f"Lander {self.id} has location {self.center_lat} {self.center_lon}")
        #print(f"Datetime: {self.arr_datetime}")
        print(f"Salinity: {self.arr_salinity}")
        print(f"Temperature: {self.arr_temperature} ")
        print(f"Status of update {self.arr_change} ")
        print(f"Grid size lat: {self.maxlat} {self.minlat}, lon: {self.maxlon} {self.minlon}")
        print("--------------------------------")
        
