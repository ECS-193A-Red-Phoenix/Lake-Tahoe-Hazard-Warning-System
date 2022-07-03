"""
Running this script will regularly perform this sequence of tasks

1. Fetch data from AWS + NWS and store them in the database
2. Create input surfbc.txt file
3. Run the model
4. Generate output images
"""

import profile
from dataretrieval.service import DataRetrievalService
from model.run_model import run_si3d
from model.create_output_binary import create_output_binary
from model.update_si3d_inp import update_si3d_inp
from model.update_si3d_init import create_ctd_profile_from_node, create_ctd_profile_from_api
from save_model_output import save_model_output
import logging
import datetime
import os
import traceback

logFilename = "logs/s3_log.log"
logging.basicConfig(
    level=logging.INFO,  # all levels greater than or equal to info will be logged to this file
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(logFilename, mode="w"),
        logging.StreamHandler()
    ]
)

MODEL_DIR = "./model/psi3d/"
format_date = lambda date: datetime.datetime.strftime(date.astimezone(tz=None), "%Y-%m-%d %H:%M:%S PST")
format_duration = lambda delta: str(delta)

drs = DataRetrievalService()

def run_si3d_workflow():
    start = datetime.datetime.now(datetime.timezone.utc)
    logging.info(f"[DataRetrievalService]: Starting si3d workflow at {format_date(start)}")

    model_start_date = start - datetime.timedelta(weeks=1)
    logging.info(f"Simulation start date: {format_date(model_start_date)}")

    try:
        # Retrieve data from various API's
        drs.retrieve()
        drs.create_si3d_surfbc(f"{MODEL_DIR}/surfbc.txt", model_start_date)

        # Update si3d_inp.txt
        update_si3d_inp(model_start_date)

        try:
            create_ctd_profile_from_api(MODEL_DIR, profile_date=model_start_date)
        except:
            # Update si3d_init.txt using node 65, 135
            tf_path = f"{MODEL_DIR}tf65_135.txt"
            logging.warning(f"Failed to create ctd profile from API, attempting to create one from {tf_path}")

            create_ctd_profile_from_node(tf_path, MODEL_DIR, profile_date=model_start_date)

        # Run si3d model
        run_si3d()

        # Parse model output into Numpy array files
        create_output_binary()

        # Send array files to S3
        save_model_output()

        end = datetime.datetime.now(datetime.timezone.utc)
        logging.info(f"[DataRetrievalService]: Finished si3d workflow at {format_date(end)}")
        logging.info(f"[DataRetrievalService]: Job 'si3d workflow' took {format_duration(end - start)} to complete")
    except Exception:
        logging.critical(f"[DataRetrievalService]: DRS failed due to error")
        logging.critical(traceback.print_exc())
    finally:
        # Shutdown EC2 instance
        # https://stackoverflow.com/a/22913651
        # Must invoke IMDSv2 to get current instance ID for shutting down
        os.system("aws ec2 stop-instances --instance-ids $(curl -s http://169.254.169.254/latest/meta-data/instance-id)")

if __name__ == '__main__':
    run_si3d_workflow()