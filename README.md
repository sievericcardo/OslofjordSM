# Opendrift

Opendrift setup
can be found here:
https://opendrift.github.io/install.html

Initially clone the fit repository for opendrift.
https://github.com/OpenDrift/opendrift

Install Anaconda to the computer and open the prompt.

1.	Navigate to the Opendrift file:
 

2.	Use this to create an environment
```
conda env create -f environment.yml
```

 

3.	Activate opendrift
```
conda activate opendrift
```

 

4.	Then use this:  
```
pip install --no-deps -e .
```

5.	Now you could run any model by typing python, and then the filename
 

 
# To run in conda

1. First create a nc file with sensor data for the driftmodel
```
python cdf.py
```

2. Run the drift simulator
```
python SalinityDrift.py
```

3. Read the output by running
```
python cdf_reader.py
```



More indept++

'''
Pip install zarr
Netcdf4
xarray
'''
