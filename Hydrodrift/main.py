from datetime import datetime, timedelta 
from opendrift.readers import reader_netCDF_CF_generic


from postAPI import HasuraMutaion
from HydroDrift import HydroDrift
from timescaleAPI import QueryAPI

import json
import sys


def suppress_qt_warnings(): 
    from os import environ 
    environ["QT_DEVICE_PIXEL_RATIO"] = "0" 
    environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1" 
    environ["QT_SCREEN_SCALE_FACTORS"] = "1" 
    environ["QT_SCALE_FACTOR"] = "1"


    

if __name__ == "__main__": 
    suppress_qt_warnings()

    # INIT VARIABLES
    # List of seeding points/lander locations
    latSensorList = []
    lonSensorList = []


    # DEFAULT VALUES
    # Location in degrees
    lat, lon = 59.658233, 10.624583
    # Seed length in hours
    seed_length = 24
    # Start and end datetime
    t1 = datetime(2023, 4, 12, 15)
    t2 = t1 + timedelta(hours=seed_length)


    arg_len = len(sys.argv)

    if arg_len > 1:
        for arg in sys.argv:
            print(arg)
 
        

    o = HydroDrift(loglevel=40)
    QueryAPI()
    
    latSensorList.append(lat)
    lonSensorList.append(lon)


    # Creation of Virtual Landers
    size_lat = 0.05
    size_lon = 0.05
    o.create_landers_from_list(t1,seed_length, size_lat, size_lon)
    


    # Load API data from NetCDF file 
    filename = 'hasura_data_hourly.nc'
    salinity_reader = reader_netCDF_CF_generic.Reader(filename)
    #print('Variables in the NetCDF file:', salinity_reader.variables)
   
    o.add_reader(salinity_reader)
    o.add_readers_from_list(
    ['https://thredds.met.no/thredds/dodsC/sea/norkyst800m/1h/aggregate_be'])

    print(o.readers)
    print("===============================================\n\n")


    # Run the model
    number = 1
    for i in range(len(latSensorList)):
        o.seed_elements(lon=lonSensorList[i], lat=latSensorList[i], time=[t1, t2],
                        number=20, radius=200)

    seed_times = o.elements_scheduled_time[0:number] 

    # 60 min interval in 24 hours until all particles deactivate or timeout
    # Remember time:units = "seconds since 1970-01-01 00:00:00" ;
    o.run(time_step=timedelta(minutes=60), duration=timedelta(hours=seed_length), outfile='output_file.nc')
    print("Model run complete")
    print("===============================================\n\n")


    # Post prep of data  
    o.smooth_landerlist()
    
    postSim = HasuraMutaion()

    for lander in o.lander_list:
        if lander.change == True:   
            #lander.print_lander()
            for ind in range(lander.seed_length):
                record_data = {
                    "record_time": f"{lander.arr_datetime[ind]}",
                    "conductivity": f"{lander.arr_salinity[ind]}",
                    "temperature": f"{lander.arr_temperature[ind]}",
                    "turbidity": f"{lander.arr_turbidity[ind]}",
                    "grid_id": f"{lander.id}",
                }

                # Convert the dictionary to a JSON string
                json_data = json.dumps(record_data)
                postSim.data_for_muation(json_data)

    postSim.run_mutation()
    print("POST data complete")
    print("===============================================\n\n")


    # CSV and Simulation
    o.write_landers_to_csv()
    o.animation(fast=True, filename='hydrodrift_sim_vis.mp4')
    print("Simulation complete")
    print("===============================================\n\n")


    