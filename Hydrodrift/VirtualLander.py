import numpy as np

class VirtualLander():
    '''
    variables:
    - Time
    - Location
    - Change 
    - Salinity
    - Temperature
    '''
    maxlat, minlat, maxlon, minlon, lat, lon = 0, 0, 0, 0, 0, 0
    
    df_salinity = 20
    df_temperature = 8
    arr_salinity = []
    arr_temperature = []

    arr_change = []

    starttime = None
    id= 0
    seed_length = 0

    def __init__(self, id):
        self.id = id
       


    def create_lander(self, lat, lon, starttime, seed_length):
        '''
        Method to create a single lander
        Required variables:
            lat
            lon
            starttime
        '''
        # Variable for the size of per grid
        grid_size = 0.02

        self.lat = lat
        self.lon = lon
        self.starttime = starttime
        self.seed_length = seed_length

        self.maxlat = lat + grid_size
        self.minlat = lat - grid_size
        self.maxlon = lon + grid_size
        self.minlon = lon - grid_size

        self.arr_salinity = np.full(seed_length, self.df_salinity, dtype=np.float32)
        self.arr_temperature = np.full(seed_length, self.df_temperature, dtype=np.float32)
        self.arr_change = np.full(seed_length, False)

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
        for i in range(self.seed_length):
            if i == 0 or self.arr_change[i] == True or self.arr_change[i-1] == False:
                continue
                #skip
            
            elif self.arr_change[i] == False and self.arr_change[i-1] == True:
                    next_changed_index = i+1

                    while next_changed_index < self.seed_length:
                        if self.arr_change[next_changed_index] == True:
                            self.arr_salinity[i] = np.float32((self.arr_salinity[i-1] + self.arr_salinity[next_changed_index])/2)
                            self.arr_temperature[i] = np.float32((self.arr_temperature[i-1] + self.arr_temperature[next_changed_index])/2)
                            break
                        
                        next_changed_index= next_changed_index+1

        
    def print_lander(self):      
        print(f"Lander {self.id} has location {self.lat} {self.lon}")
        print(f"Salinity: {self.arr_salinity}")
        print(f"Temperature: {self.arr_temperature} ")
        print(f"Status of update {self.arr_change} ")
        print(f"Grid size lat: {self.maxlat} {self.minlat}, lon: {self.maxlon} {self.minlon}")
        print("--------------------------------")
        
