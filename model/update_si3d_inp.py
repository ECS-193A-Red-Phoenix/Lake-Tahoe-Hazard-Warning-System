from datetime import datetime, timezone
import re

SI3D_INP_PATH = "./model/psi3d/si3d_inp.txt"

def update_si3d_inp():
    """ Updates si3d_inp.txt

        1. Update the simulation start date so that output
        files are labeled correctly. We use UTC for date
    """

    si3d_inp = None
    with open(SI3D_INP_PATH, "r") as file:
        si3d_inp = file.read()

    now = datetime.now(timezone.utc)
    year = f"{now.year:04}"
    month = f"{now.month:02}"
    day = f"{now.day:02}"
    hour = f"{now.hour:02}"
    print(f"update_si3d_inp(): Updating si3d_inp date to {year}-{month}-{day} {hour}")

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
       r"hour         !      \d+            !",
       f"hour         !      {hour}            !",
        si3d_inp
    )

    # Save file
    with open(SI3D_INP_PATH, "w") as file:
        file.write(si3d_inp)

if __name__ == "__main__":
    update_si3d_inp()
    print("Updated si3d_inp.txt")