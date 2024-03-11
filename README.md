# HydroDrift

Opendrift setup
can be found here:
https://opendrift.github.io/install.html

Initially clone the fit repository for opendrift.
https://github.com/OpenDrift/opendrift

Install Anaconda to the computer and open the prompt.

1.	Navigate to the Opendrift directory:
 

2.	run this to create an environment
```
conda env create -f environment.yml
```

 

3.	Activate opendrift
```
conda activate opendrift
```

 

4.	Then run this to install dependencies  
```
pip install --no-deps -e .
pip install psycopg2
pip install logger
```
#Remember to update dependecy file

5.	Now you could run any model by typing python, and then the filename
 

 
# To run HydroDrift in conda


Run the drift model by navigating to HydroDrift and then:
```
python main.py
```

The result:
- Outputfile with particle properties
- Visual simulation
- Update the API with results


The main function has initial end simulation date set as 2023-4-13 15.00.00,
but could also be run with arguments for date time:
```
python main.py "year" "month" "day" "hour"
```

Example:
```
python main.py 2023 4 14 16
```

This requires available sensordata in the API (for the previous 24 hours)




