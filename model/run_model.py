"""
The purpose of this file is to encapsulate an interface to run the hydrodynamic model.
This file provides a function that will run the hydrodynamic model. Alternatively, running 
this file directly will run the model.

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