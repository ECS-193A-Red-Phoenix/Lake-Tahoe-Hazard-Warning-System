from model.HPlane_Si3DtoPython import HPlane_Si3dToPython
import numpy as np
import os

##############################################################
# User Config
OUTPUT_DIR = "./outputs/"                     # Output file directory
H_PLANE_PATH = "./model/psi3d/plane_2"        # Path to model output file
DX = 200                                      # idx parameter from simulation
FLOW_DIR = "flow/"
TEMPERATURE_DIR = "temperature/"
##############################################################

logFilename = "logs/s3_log.log"
logging.basicConfig(
    level=logging.INFO,  # all levels greater than or equal to info will be logged to this file
    filename=logFilename,  # logger file location
    filemode="w",  # overwrites a log file
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def create_output_binary():
    h_plane = HPlane_Si3dToPython(H_PLANE_PATH, DX)

    n_rows, n_cols, n_frames = h_plane['Tg'].shape
    str1 = "Found h plane file"
    str2 = f"Map dimensions (row, cols, n_frames) = {(n_rows, n_cols, n_frames)}"
    msg = f"{str1}\n{str2}"
    logging.info(msg)

    # Create output directories if they don't exist
    if not os.path.isdir(OUTPUT_DIR):
        str1 = f"Output directory does not exist, creating folders {OUTPUT_DIR}"
        logging.info(str1)
        os.mkdir(OUTPUT_DIR)
    if not os.path.isdir(OUTPUT_DIR + "temperature/"):
        os.mkdir(OUTPUT_DIR + TEMPERATURE_DIR)
    if not os.path.isdir(OUTPUT_DIR + "flow/"):
        os.mkdir(OUTPUT_DIR + FLOW_DIR)

    for idx, timestamp in enumerate(h_plane['time']):
        u = h_plane['ug'][:, :, idx]
        v = h_plane['vg'][:, :, idx]
        uv = np.array([u, v])
        np.save(OUTPUT_DIR + FLOW_DIR + timestamp + '.npy', uv)

        t = h_plane['Tg'][:, :, idx]
        np.save(OUTPUT_DIR + TEMPERATURE_DIR + timestamp + '.npy', t)
        str1 = f"Saved uv and temperature at {timestamp}"
        logging.info(str1)



if __name__ == '__main__':
    create_output_binary()

