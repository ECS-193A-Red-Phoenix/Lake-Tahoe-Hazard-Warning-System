"""
The purpose of this file is to encapsulate an interface to run the hydrodynamic model.
This file provides a function that will run the hydrodynamic model. Alternatively, running 
this file directly will run the model.

Notes:
1. run_model() will query the database for the latest weather data it has, and create
the necessary input files for the model to run using that data

2. run_model() will return a python dictionary representing the output data of the model.
This python dictionary is structured as such:
{
    # Note dimensionality of arrays are (Rows, Cols, # Frames)
    'T': numpy array of temperatures
    'u': numpy array of East-West velocity magnitudes
    'v': numpy array of North-South velocity magnitudes
    'w': numpy array of Vertical velocity magnitudes
}

Example usage:

```
from run_model import run_model

run_model()
```
"""


import subprocess
from postprocessing.HPlane_Si3DtoPython import HPlane_Si3dToPython

MODEL_DIR = './lt-hws/model/SampleModel/'
MODEL_NAME = './psi3d'

def run_model(verbose=True):
    """
    Runs the hydrodynamic model as a subprocess

    Arguments:
        verbose (bool): If true will print model output
    """
    # TODO: fetch data from data base here and update input files

    # We need to change to cwd for model to properly read input file
    process = subprocess.Popen([MODEL_NAME], cwd=MODEL_DIR, stdout=subprocess.PIPE)
    for line in process.stdout:
        print(line.decode('utf8'), end='')
    process.wait()

    return HPlane_Si3dToPython(MODEL_DIR + "plane_2", dx=800)
    

if __name__ == '__main__':
    print("Assuming this file is being run from /LakeTahoe-HazardWarningSystem")
    res = run_model()
    print("si3D has finished running")
    
    # Print small visualization of the lake
    print("Lake Temperatures in final frame:")
    import math
    temps = res['T'][::-1,:,-1].tolist()
    for row in temps:
        for temp in row:
            if math.isnan(temp):
                print(" nan ", end='')
            else:
                print(f"{temp:>4.1f} ", end='')
        print('')

    print(f"Output files are located in {MODEL_DIR}")