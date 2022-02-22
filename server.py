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
import datetime
import schedule
import time

SURF_BC_PATH = "./model/psi3d/surfbc.txt"
format_date = lambda date: datetime.datetime.strftime(date, "%Y-%m-%d %H:%M:%S UTC")
format_duration = lambda delta: str(delta)

drs = DataRetrievalService()

def run_si3d_workflow():
    start = datetime.datetime.now(datetime.timezone.utc)
    print(f"[DataRetrievalService]: Starting si3d workflow at {format_date(start)}")

    drs.retrieve()
    drs.create_si3d_surfbc(SURF_BC_PATH)
    run_si3d()
    
    end = datetime.datetime.now(datetime.timezone.utc)
    print(f"[DataRetrievalService]: Finished si3d workflow at {format_date(end)}")
    print(f"[DataRetrievalService]: Job 'si3d workflow' took {format_duration(end - start)} to complete")

schedule.every(5).minutes.do(run_si3d_workflow)

while True:
    schedule.run_pending()
    time.sleep(1)