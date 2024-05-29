from datetime import datetime, timedelta 
from opendrift.readers import reader_netCDF_CF_generic
from opendrift.readers import reader_ROMS_native
from HydroDrift import HydroDrift
from API import QueryAPI
import json
import sys

if __name__ == "__main__": 
    '''
    Args:
    1: Year
    2: Month
    3: Day
    
    '''

    # INIT VARIABLES
    # List of seeding points/lander locations
    latSensorList = []
    lonSensorList = []
    end_time,start_time = 0, 0


    # DEFAULT VALUES
    # Location in degrees
    #lat, lon = 59.658233, 10.624583
    # Seed length in hours
    seed_length = 24
    # Start and end datetime
    end_time = datetime(2024, 4, 16, 0)
    start_time = end_time - timedelta(hours=seed_length)


    arg_len = len(sys.argv)

    if arg_len > 3:
        #for arg in sys.argv:
        #    print(arg)


        # if arg_len > 4:
        #     end_time = datetime(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])) + (timedelta(hours=int(sys.argv[4])))
        # else:
        end_time = datetime(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
            
        start_time = end_time - timedelta(hours=seed_length)

    print("Starttime: " + str(start_time))
    print("Endtime: " + str(end_time))
    print("===============================================\n\n")

           
    drift = HydroDrift(loglevel=40)
    drift.suppress_qt_warnings()

    print("Pulling data from API")
    queryAPI = QueryAPI()
    locations = queryAPI.query_location_API(start_time, end_time)
    for location in locations:
        latSensorList.append(location[1])
        lonSensorList.append(location[0])
    
    # add additional lander
    # latSensorList.append(latSensorList[0] + 0.15)
    # lonSensorList.append(lonSensorList[0] - 0.1)
    # print(locations)
    print(locations)
    

    #queryAPI.query_data_API(start_time, end_time+ timedelta(hours=1))

    queryAPI.query_data_API(start_time, end_time)


    # Creation of Virtual Landers
    size_lat = 0.05
    size_lon = 0.05
    print("Creating Virtual Landers")
    drift.create_landers_from_list(start_time,seed_length, size_lat, size_lon)
    

    # Load API data from NetCDF file 
    filename = 'sensor_data.nc'
    lander_reader = reader_netCDF_CF_generic.Reader(filename)
    #print('Variables in the NetCDF file:', salinity_reader.variables)

    reader_norkyst = reader_netCDF_CF_generic.Reader(
    'https://thredds.met.no/thredds/dodsC/sea/norkyst800m/1h/aggregate_be')
   
    # drift.add_reader(salinity_reader)
    fjordOSReader = reader_ROMS_native.Reader("https://thredds.met.no/thredds/dodsC/fjordos/operational_archive/complete_archive/ocean_his.nc_2024041500")
    # norkyst800Reader = reader_netCDF_CF_generic.Reader("https://thredds.met.no/thredds/dodsC/sea/norkyst800m/1h/aggregate_be")
    metrological_model = fjordOSReader
    drift.add_reader(metrological_model)
    drift.add_reader(lander_reader, first=True)

    # drift does not have the attribute "readers"
    print(metrological_model)

    
    print(drift)
    print("===============================================\n\n")


    
    # Run the model
    number = 1
    for i in range(len(latSensorList)):
        drift.seed_elements(lon=lonSensorList[
             i], lat=latSensorList[i], time=[start_time, end_time],
                        number=500, radius=20)
        
    # drift.plot(buffer=.7, fast=True)

    seed_times = drift.elements_scheduled_time[0:number] 

    # 60 min interval in 24 hours until all particles deactivate or timeout
    # Remember time:units = "seconds since 1970-01-01 00:00:00" ;
    #drift.run(time_step=timedelta(minutes=60), duration=timedelta(hours=seed_length), outfile='output_file.nc')
    drift.run(time_step=timedelta(minutes=60), duration=timedelta(hours=seed_length))
    print("Model run complete")
    print("===============================================\n\n")

    # drift.plot(buffer=.7, fast=True)

    # Post prep of data  
    drift.smooth_landerlist()

    
    for lander in drift.lander_list:
        #if lander.change == True:   
            #lander.print_lander()
            for ind in range(lander.seed_length):
                record_data = {
                    "record_time": f"{lander.arr_datetime[ind]}",
                    "conductivity": f"{lander.arr_salinity[ind]}",
                    "temperature": f"{lander.arr_temperature[ind]}",
                    "turbidity": f"{lander.arr_turbidity[ind]}",
                    "grid_id": f"{lander.id}",
                    "changed": f"{lander.arr_change[ind]}"
                }

                # Convert the dictionary to a JSON string
                json_data = json.dumps(record_data)
                queryAPI.data_for_mutation(json_data)
                # print(json_data)

    
    queryAPI.reset_data_API()
    print("Reset data complete")
    print("===============================================\n\n")


    # queryAPI.mutation_data_API()
    print("POST data complete")
    print("===============================================\n\n")


    # CSV and Simulation
    drift.write_landers_to_csv()
    drift.animation(fast=True, filename='hydrodrift_visual_simulation.mp4')
    print("Simulation complete")
    print("===============================================\n\n")
    
    

    