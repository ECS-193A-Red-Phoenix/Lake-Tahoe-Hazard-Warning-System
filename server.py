"""
Running this script will regularly perform this sequence of tasks

1. Fetch data from AWS + NWS and store them in the database
2. Create input surfbc.txt file
3. Run the model
4. Generate output images
"""

from numpy import short
from dataretrieval.service import DataRetrievalService
from model.run_model import run_si3d
from model.create_output_binary import create_output_binary
from save_model_output import save_model_output
import datetime
import schedule
import time

MODEL_DIR = "./model/psi3d/"
format_date = lambda date: datetime.datetime.strftime(date, "%Y-%m-%d %H:%M:%S UTC")
format_duration = lambda delta: str(delta)

drs = DataRetrievalService()

def run_si3d_workflow():
    start = datetime.datetime.now(datetime.timezone.utc)
    print(f"[DataRetrievalService]: Starting si3d workflow at {format_date(start)}")

    drs.retrieve()
    drs.create_si3d_surfbc(f"{MODEL_DIR}/surfbc.txt", start)
    run_si3d()
    # Parse model output into Numpy array files
    create_output_binary()
    # Send array files to backend server
    save_model_output()

    end = datetime.datetime.now(datetime.timezone.utc)
    print(f"[DataRetrievalService]: Finished si3d workflow at {format_date(end)}")
    print(f"[DataRetrievalService]: Job 'si3d workflow' took {format_duration(end - start)} to complete")


# schedule.every(5).minutes.do(run_si3d_workflow)
schedule.every(1).days.do(run_si3d_workflow)
schedule.run_all()

while True:
    schedule.run_pending()
    time.sleep(1)