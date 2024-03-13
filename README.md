
# <img src="logo.jpg" width="40"> HydroDrift

Opendrift setup can be found here:
https://opendrift.github.io/install.html

### Setup local 

1. Clone the repository.


2. Install Anaconda to the computer and open the prompt.
 

3.	Run to create an environment
```
conda env create -f environment.yml
```


4.	Activate opendrift
```
conda activate opendrift
```

 

4. Run to install dependencies  
```
pip install --no-deps -e .
```


5.	Now you could run any model by typing python, and then the filename
 

### Setup Docker

1. Clone the repository.
 

3.	Run to build the image
```
docker build -t hydrodrift . 
```


4.	To run the docker
```
docker run -it --rm hydrodrift
```
 
### Run model


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




