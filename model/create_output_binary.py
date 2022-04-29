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

def create_output_binary():
    h_plane = HPlane_Si3dToPython(H_PLANE_PATH, DX)

    n_rows, n_cols, n_frames = h_plane['Tg'].shape
    print("Found h plane file")
    print(f"Map dimensions (row, cols, n_frames) = {(n_rows, n_cols, n_frames)}")

    # Create output directories if they don't exist
    if not os.path.isdir(OUTPUT_DIR):
        print(f"Output directory does not exist, creating folders {OUTPUT_DIR}")
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
        print("Saved uv and temperature at " + timestamp)


if __name__ == '__main__':
    create_output_binary()

