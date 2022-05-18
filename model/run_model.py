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


import subprocess, logging

MODEL_DIR = './model/psi3d'
MODEL_NAME = './psi3d'

logFilename = "logs/s3_log.log"
logging.basicConfig(
    level=logging.INFO,  # all levels greater than or equal to info will be logged to this file
    filename=logFilename,  # logger file location
    filemode="w",  # overwrites a log file
    format="%(asctime)s - %(levelname)s - %(message)s"
)

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
            str1 = line.decode('utf8')
            logging.info(str1)
    process.wait()
    

if __name__ == '__main__':
    str1 = "Assuming this file is being run from /LakeTahoe-HazardWarningSystem"
    logging.info(str1)
    res = run_si3d()
    str1 = "si3D has finished running"
    str2 = f"Output files are located in {MODEL_DIR}"
    msg = f"{str1}\n{str2}"
    logging.info(msg)