from matplotlib import pyplot as plt
from .HPlane_Si3DtoPython import HPlane_Si3dToPython
import time
import os, logging, sys

##############################################################
# User Config
OUTPUT_DIR = "./model/outputs/"                     # Output file directory
H_PLANE_PATH = "./model/psi3d/plane_2"        # Path to model output file
DX = 200                                      # idx parameter from simulation
##############################################################

logFilename = "logs/s3_log.log"
logging.basicConfig(
    level=logging.INFO,  # all levels greater than or equal to info will be logged to this file
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(logFilename, mode="w"),
        logging.StreamHandler()
    ]
)

def create_output_maps():
    start_time = time.time()

    str1 = f"File running from directory {os.getcwd()}"
    str2 = f"Searching for h plane file {H_PLANE_PATH}"
    msg = f"{str1}\n{str2}"
    logging.info(msg)

    if not os.path.isfile(H_PLANE_PATH):
        str1 = f"[Error]: Could not find h plane file {H_PLANE_PATH}"
        str2 = "Exiting program"
        msg = f"{str1}\n{str2}"
        logging.error(msg)
        sys.exit(0)
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
        os.mkdir(OUTPUT_DIR + "temperature/")
    if not os.path.isdir(OUTPUT_DIR + "flow/"):
        os.mkdir(OUTPUT_DIR + "flow/")


    ##############################################################
    # Create flow maps in batch
    ##############################################################
    FLOW_DIR = "flow/"
    fig, ax = plt.subplots(1, 1)
    text = ax.text(0.7, 0.882, "m/s", transform=fig.transFigure)
    xg = h_plane['xg']
    yg = h_plane['yg']
    cbar = surface_flow = None
    for idx, timestamp in enumerate(h_plane['time']):
        # Remove previous plot for efficient rerender
        if cbar is not None or surface_flow is not None:
            cbar.remove()
            surface_flow.remove()

        u = h_plane['ug'][:, :, idx]
        v = h_plane['vg'][:, :, idx]
        w = h_plane['wg'][:, :, idx]
        magnitude = (u**2 + v**2 + w**2)**0.5
        surface_flow = ax.quiver(
            xg, 
            yg, 
            u, 
            v, 
            magnitude, 
            cmap='Spectral_r', 
            scale=4, 
            scale_units='inches', 
            headwidth=3, 
            headlength=5, 
            headaxislength=10, 
            width=0.008
        )

        cax = plt.axes([0.7, 0.125, 0.02, 0.75])
        cbar = fig.colorbar(surface_flow, cax=cax)
        cbar.ax.tick_params(labelsize=9)
        
        fig.suptitle(timestamp + ":00")
        ax.set_aspect('equal')
        ax.axis('off')

        plt.savefig(OUTPUT_DIR + FLOW_DIR + f'flow_{timestamp}', bbox_inches='tight')
        plt.cla()
        str1 = f"Created output flow map for {timestamp}"
        logging.info(str1)
    plt.close()
    str1 = f"Finished creating {n_frames} flow maps located in {OUTPUT_DIR + FLOW_DIR}"
    logging.info(str1)


    ##############################################################
    # Create temperature maps in batch
    ##############################################################
    TEMPERATURE_DIR = "temperature/"
    fig, ax = plt.subplots(1, 1)
    ax.text(0.7, 0.882, "° Celsius", transform=fig.transFigure)
    xg = h_plane['xg']
    yg = h_plane['yg']
    cbar = temp_map = None
    for idx, timestamp in enumerate(h_plane['time']):
        z = h_plane['Tg'][:, :, idx]
        # Remove previous plot for efficient rerender
        if cbar is not None or temp_map is not None:
            cbar.remove()
            temp_map.remove()

        temp_map = ax.pcolormesh(xg, yg, z, shading='gouraud', cmap='RdYlBu_r')

        cax = plt.axes([0.7, 0.125, 0.02, 0.75])
        cbar = fig.colorbar(temp_map, cax=cax)
        cbar.ax.tick_params(labelsize=9)
        
        fig.suptitle(timestamp + ":00")
        ax.set_aspect('equal')
        ax.axis('off')

        plt.savefig(OUTPUT_DIR + TEMPERATURE_DIR + f'temperature_{timestamp}', bbox_inches='tight')
        plt.cla()
        str1 = f"Created output temperature map for {timestamp}"
        logging.info(str1)
    str1 = f"Finished creating {n_frames} temperature maps located in {OUTPUT_DIR + TEMPERATURE_DIR}"
    logging.info(str1)
    plt.close()

    end_time = time.time()
    str1 = f"Completed all tasks in {(end_time - start_time):.2f} seconds"
    str2 = f"Created {n_frames} flow maps from {h_plane['time'][0]} to {h_plane['time'][-1]}"
    msg = f"{str1}\n{str2}"
    logging.info(msg)


if __name__ == '__main__':
    create_output_maps()