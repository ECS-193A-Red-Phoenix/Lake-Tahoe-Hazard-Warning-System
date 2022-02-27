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

MODEL_DIR = './model/psi3d'
MODEL_NAME = './psi3d'

def run_si3d(verbose=True):
    """
    Runs the hydrodynamic model as a subprocess

    Arguments:
        verbose (bool): If true will print model output
    """
    # We need to change to cwd for model to properly read input file
    process = subprocess.Popen([MODEL_NAME], cwd=MODEL_DIR, stdout=subprocess.PIPE)
    if verbose:
        for line in process.stdout:
            print(line.decode('utf8'), end='')
    process.wait()
    

if __name__ == '__main__':
    print("Assuming this file is being run from /LakeTahoe-HazardWarningSystem")
    res = run_si3d()
    print("si3D has finished running")
    print(f"Output files are located in {MODEL_DIR}")