# Lake Tahoe Warning System

This repository hosts code that automates the workflow of the si3d model for Lake Tahoe. This means retrieving the necessary data from various API's and creating input files for the si3d model.

## Installation

Install Python 3. Any `3.x` version should be fine, but we use Python 3.8.8.

Make sure you install required python packages with

`pip install -r requirements.txt`

## Running the model

To start the si3d workflow, run the following:

`python si3d.py`

Running this command will complete the following steps:

1. Retrieve data, clean it, and prepare model input files located in `./model/psi3d`. In particular, we update `surfbc.txt` and `si3d_inp.txt`.
2. Run the si3d executable `./model/psi3d/psi3d`
3. Parse the model output file `./model/psi3d/plane_2` and generate `.npy` files for each temperature and flow visualization in `./outputs`
4. Upload the `.npy` files to S3 and update `contents.json`, deleting old `.npy` files if any. 

## Known Errors

Running `si3d.py` may crash and return an error for the following documented reasons.

1. A critical API endpoint may be down. This means that we are missing critical information for an accurate model run. 
