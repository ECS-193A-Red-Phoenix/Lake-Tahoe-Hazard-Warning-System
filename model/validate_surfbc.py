""" 
Use this script to visually validate the surfbc.txt input file to the model.
- This script will parse a surfbc.txt file and generate time series plots
for each feature.  
"""

from matplotlib import pyplot as plt
import pandas as pd

file_path = "./model/psi3d/surfbc.txt"

lines = []
with open(file_path, "r") as file:
    lines = file.readlines()
lines = lines[7:] # Ignore first 7 header lines

data = []
for line in lines:
    sample = []
    i = 0
    while i + 10 < len(line):
        sample.append(float(line[i:i+10]))
        i += 10 + 1
    data.append(sample)    

features = ["time", "attenuation coefficient", "shortwave", "air temp", "atmospheric pressure",
   "relative humidity", "longwave", "wind drag coefficient", "wind u", "wind v"]
df = pd.DataFrame(data, columns=features)

for i in range(1, len(features)):
    plt.title(features[i])
    plt.plot(df['time'], df[features[i]])
    plt.show()