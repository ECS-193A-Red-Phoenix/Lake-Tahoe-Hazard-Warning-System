from datetime import datetime, timedelta, timezone
import re
import logging

SI3D_INP_PATH = "./model/psi3d/si3d_inp.txt"

logFilename = "logs/s3_log.log"
logging.basicConfig(
    level=logging.INFO,  # all levels greater than or equal to info will be logged to this file
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(logFilename, mode="w"),
        logging.StreamHandler()
    ]
)

def update_si3d_inp(start_date):
    """ Updates the starting date of the simulation in si3d_inp.txt
        Arguments:
          date (datetime.datetime): the starting date of the simulation
    """

    si3d_inp = None
    with open(SI3D_INP_PATH, "r") as file:
        si3d_inp = file.read()

    year = f"{start_date.year:04}"
    month = f"{start_date.month:02}"
    day = f"{start_date.day:02}"
    hour = f"{start_date.hour:02}00"
    str1 = f"update_si3d_inp(): Updating si3d_inp date to {year}-{month}-{day} {hour}"
    logging.info(str1)

    si3d_inp = re.sub(
       r"year         !    \d+            !",
       f"year         !    {year}            !",
        si3d_inp
    )
    si3d_inp = re.sub(
       r"month        !      \d+            !",
       f"month        !      {month}            !",
        si3d_inp
    )
    si3d_inp = re.sub(
       r"day          !      \d+            !",
       f"day          !      {day}            !",
        si3d_inp
    )
    si3d_inp = re.sub(
       r"hour         !    \d+            !",
       f"hour         !    {hour}            !",
        si3d_inp
    )

    # Save file
    with open(SI3D_INP_PATH, "w") as file:
        file.write(si3d_inp)

if __name__ == "__main__":
    start_date = datetime.now(timezone.utc) - timedelta(days=7)
    update_si3d_inp(start_date)
    str1 = "Updated si3d_inp.txt"
    logging.info(str1)
