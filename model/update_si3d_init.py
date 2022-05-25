import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

CTD_LAYERS = np.array([0.26, 0.26, 0.77, 1.29, 1.83, 2.38, 2.94, 3.5, 4.08, 4.67, 5.28, 5.89, 6.53, 7.17, 7.82, 8.48, 9.16, 9.86, 10.57, 11.29, 12.02, 12.77, 13.54, 14.32, 15.12, 15.93, 16.76, 17.6, 18.46, 19.34, 20.23, 21.15, 22.09, 23.04, 24.01, 25.0, 26.01, 27.04, 28.09, 29.16, 30.25, 31.37, 32.5, 33.66, 34.85, 36.06, 37.29, 38.55, 39.83, 41.13, 42.47, 43.83, 45.21, 46.62, 48.06, 49.53, 51.03, 52.56, 54.13, 55.73, 57.35, 59.01, 60.7, 62.42, 64.17, 65.97, 67.8, 69.66, 71.57, 73.51, 75.49, 77.51, 79.57, 81.67, 83.81, 86.0, 88.23, 90.5, 92.83, 95.19, 97.6, 100.06, 102.58, 105.14, 107.75, 110.41, 113.14, 115.91, 118.74, 121.62, 124.56, 127.56, 130.62, 133.75, 136.94, 140.18, 143.5, 146.88, 150.32, 153.84, 157.43, 161.09, 164.81, 169.2, 174.2, 179.2, 184.2, 189.2, 194.2, 199.2, 204.2, 209.2, 214.2, 219.2, 224.2, 229.2, 234.2, 239.2, 244.2, 249.2, 254.2, 259.2, 264.2, 269.2, 274.2, 279.2, 284.2, 289.2, 294.2, 299.2, 304.2, 309.2, 314.2, 319.2, 324.2, 329.2, 334.2, 339.2, 344.2, 349.2, 354.2, 359.2, 364.2, 369.2, 374.2, 379.2, 384.2, 389.2, 394.2, 399.2, 404.2, 409.2, 414.2, 419.2, 424.2, 429.2, 434.2, 439.2, 444.2, 449.2, 454.2, 459.2, 464.2, 469.2, 474.2, 479.2, 484.2, 489.2, 494.2, 499.2, 503.35, 503.35])

def parse_tf_file(file_path, ignore_period=timedelta(hours=0)):
    """ Parses a tf file

    Args:
        file_path (String): path to the tf file
        ignore_period (timedelta, optional): the window of time to ignore, starting at the beginning. Defaults to timedelta(hours=0).

    Returns:
        List[tuple(datetime, pd.DataFrame)]: a list of dates and the corresponding Dataframe at that time
    """
    with open(file_path, "r") as file:
        lines = file.readlines()

        date_str = lines[1].split("Start date of run:")[1]
        start_date = datetime.strptime(date_str, "  %m/%d/%Y at %H00 hours\n") \
            .replace(tzinfo=timezone.utc).astimezone(tz=None)

        # First 7 lines are a header
        lines = lines[7:]

        features = ["depth", "u", "v", "w", "Av", "Dv", "scalar"]
        num_columns = None
        dataframe = []
        res = []

        for line in lines:
            columns = list(map(float, line.split()))

            if num_columns is None:
                num_columns = len(columns)

            if len(columns) == num_columns:
                hrs, step, zeta = columns[0:3]
                hrs = timedelta(hours=hrs)
                if len(dataframe) > 0:
                    dataframe = pd.DataFrame(dataframe, columns=features)
                    if hrs > ignore_period:
                        res.append((start_date + hrs, dataframe))
                    dataframe = []
                dataframe.append(columns[3:])
            else:
                dataframe.append(columns)

        dataframe = pd.DataFrame(dataframe, columns=features)
        res.append((start_date + hrs, dataframe))
        dataframe = []
        return res


def create_si3d_init(depth_profile, output_dir="./"):
    """ Creates a si3d_init.txt file (CTD profiles)

    Args:
        depth_profile (List[tuple]): a list of 2 tuples [(km, temperature)]
        output_dir (str, optional): file path to the output directory. Defaults to "./".
    """
    today = datetime.now()
    today_str = datetime.strftime(today, "%Y-%m-%d %I:%M %p PST")    

    HEADER = "Initial condition file for si3d model            -\n" + \
             "Stratification for Lake Tahoe                    -\n" + \
            f"File created on {today_str}                       \n" + \
             "Depths (m)   Temp (oC)                           -\n" + \
             "Source: From CTD_Profile                         -\n" + \
             "--------------------------------------------------\n" 

    with open(f"{output_dir}si3d_init.txt", "w") as file:
        file.write(HEADER)

        for m, temperature in depth_profile:
            file.write(f"{m:>10.2f} {temperature:>10.4f} \n")


def create_ctd_profile_from_node(tf_file_path, output_dir):
    """ Creates a si3d init file from a given tf_node file

    Args:
        tf_file_path (string): file path to the tf file
        output_dir (string): output directory of si3d_init.txt file
    """
    new_ctd = parse_tf_file(tf_file_path)             # parse tf file                        
    new_ctd = new_ctd[-1][1]                          # extract last dataframe
    z, T = new_ctd['depth'], new_ctd['scalar']        # extract depth and temperature 
    T = np.interp(CTD_LAYERS, z, T)                   # interpolate temperature from layers
    new_ctd = list(zip(-1 * CTD_LAYERS, T))           # combine

    create_si3d_init(new_ctd, output_dir)
    print(f"Created si3d_init.txt file from {tf_file_path}")
    return new_ctd


if __name__ == "__main__":
    from matplotlib import pyplot as plt
    ctd_node = "65_135"

    tf_path = f"./model/psi3d/tf{ctd_node}.txt"
    new_ctd = create_ctd_profile_from_node(tf_path, "./model/psi3d/")
    depth, temp = list(zip(*new_ctd))

    plt.figure(figsize=(10, 8), dpi=70)
    plt.plot(temp, depth)
    plt.xlabel("Temperature ($^\circ$C)")
    plt.ylabel("Depth (m)")
    plt.title(f"CTD Profile from {ctd_node} node")

    plt.show()
