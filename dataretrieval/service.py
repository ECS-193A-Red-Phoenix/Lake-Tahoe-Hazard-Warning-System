""" This file encapsulates all tasks of the data retrieval service. If run 
directly, this file will execute the retrieve task.

List of Tasks:

1. retrieve
    - This retrieves data from AWS and NWS and stores it in a database
    - TODO Notes:
    - Since MySQL is not set up yet, this will store the retrieved data in a
    csv file. If the csv file already exists, it will append the data to it.

2. create_si3d_surfbc
    - This creates input file 'surfbc.txt' for the model

Example Usage:
>>> drs = DataRetrievalService()
>>> drs.retrieve()
"""

from dataretrieval.aws import get_model_historical_data
from dataretrieval.nws import get_model_forecast_data
import datetime
import pandas as pd
import os

class DataRetrievalService:
    ARCHIVE_DATA = False        # if set to true, will store model inputs in a csv file
    CSV_FILE = "./database.csv"

    def __init__(self):
        # Use csv file as database for now
        if self.ARCHIVE_DATA and os.path.isfile(self.CSV_FILE):
            self.db = pd.read_csv(self.CSV_FILE)
            self.db['time'] = pd.to_datetime(self.db['time'])
        else:
            self.db = None


    def save(self):
        if self.ARCHIVE_DATA and self.db is not None:
            self.db.to_csv(self.CSV_FILE, index=False)


    def retrieve(self):
        """ Retrieves data from [today - 7 days, today + 7 days], and stores it in the database,
        replacing what values already exist if any.
        """
        today = datetime.datetime.now(datetime.timezone.utc)
        last_week = today - datetime.timedelta(weeks=1)
        aws_data = get_model_historical_data(start_date=last_week, end_date=today)
        nws_data = get_model_forecast_data()
    
        # Combine the two
        most_recent_aws_date = aws_data['time'][len(aws_data) - 1] if len(aws_data) > 0 else today
        combined_data = pd.concat([
            aws_data,
            nws_data[nws_data['time'] > most_recent_aws_date]
        ], ignore_index=True)

        if self.db is None:
            self.db = combined_data
        else:
            earliest_date = combined_data['time'][0]
            self.db = pd.concat([
                self.db[self.db['time'] < earliest_date],
                combined_data
            ])
        self.db.reset_index(drop=True, inplace=True)

        self.save()


    def create_si3d_surfbc(self, file_path, start_date):
        """ Creates surfbc.txt file for model input from the given start date.

        Args:
            file_path (str): surfbc.txt file path
            start_date (datetime.datetime): starting date for surfbc file
        """
        ATTENUATION_COEFFICENT = 0.1045 # Constants based off past research
        WIND_DRAG_COEFFICENT = 0.0011
        features = ["attenuation coefficient", "shortwave", "air temp", "atmospheric pressure", "relative humidity", "longwave", "wind drag coefficient", "wind u", "wind v"]
        interval_time = datetime.timedelta(minutes=10)

        format_date = lambda date: datetime.datetime.strftime(date, '%Y-%m-%d %H:%M') 
        format_float = lambda x: f"{x:>10f}"[:10]
        
        data = self.db[self.db['time'] >= start_date]
        data.reset_index(drop=True, inplace=True)
        start_date = data['time'][0]
        assert len(data) >= 2, f"[DataRetrievalService]: I require at least 2 datapoints after {format_date(start_date)} to create surfbc.txt"

        with open(file_path, "w") as file:
            # First 6 lines are headers that are ignored by model
            today = datetime.datetime.now(datetime.timezone.utc)
            end_date = data['time'][len(data) - 1]
            n_points = ((end_date - start_date) // interval_time) + 1
            file.write("Surface boundary condition file for si3d model\n")
            file.write(f"Lake Tahoe Data (file created on {format_date(today)}) (UTC)\n")
            file.write(f"Time is given 10 minute intervals in hours starting from {format_date(start_date)} (UTC) and ending at {format_date(end_date)} (UTC)\n")
            file.write("Data format is (10X,G11.2,...)\n")
            file.write("columns=[ time  attenuation coefficient  shortwave  air temp  atmospheric pressure   relative humidity  longwave  wind drag coefficient  wind u  wind v]\n")
            file.write("units=  [hours                   number        wm2   Celsius               Pascals            fraction       wm2                 number      ms      ms]\n")
            file.write(f"   npts = {n_points}\n")

            # Some data points may be missing, so we have to linearly interpolate
            cur = start_date
            prev_i, next_i = 0, 1 # Interpolate between these indices
            while cur <= end_date:
                hours = (cur - start_date).total_seconds() / 60 / 60
                file.write(format_float(hours) + " ")
                
                # Interpolate for each feature
                for f in features:
                    if f == "attenuation coefficient":
                        file.write(format_float(ATTENUATION_COEFFICENT) + " ")
                        continue
                    elif f == "wind drag coefficient":
                        file.write(format_float(WIND_DRAG_COEFFICENT) + " ")
                        continue

                    prev_time = data['time'][prev_i]
                    next_time = data['time'][next_i]
                    prev_f = data[f][prev_i]
                    next_f = data[f][next_i]

                    slope = (next_f - prev_f) / ((next_time - prev_time).total_seconds() / 60 / 60)
                    time_from_prev = (cur - prev_time).total_seconds() / 60 / 60
                    interpolated_f = prev_f + time_from_prev * slope

                    file.write(format_float(interpolated_f) + " ")

                file.write('\n')
                cur += interval_time 
                while next_i < len(data) and not (data['time'][prev_i] <= cur <= data['time'][next_i]):
                    prev_i += 1
                    next_i += 1

        print(f"[DataRetrievalService]: Created surfbc.txt file with data from {format_date(start_date)} to {format_date(end_date)}")


if __name__ == "__main__":
    today = datetime.datetime.now(datetime.timezone.utc)
    drs = DataRetrievalService()
    drs.retrieve()
    drs.create_si3d_surfbc("./surfbc.txt", today - datetime.timedelta(days=7))

    # Log output
    format_date = lambda date: datetime.datetime.strftime(date, "%Y-%m-%d %H:%M")
    past = format_date(drs.db['time'][0])
    future = format_date(drs.db['time'][len(drs.db) - 1])
    print(f"[DataRetrievalService]: Retrieved historical and forecasted points from {past} to {future}")

    from matplotlib import pyplot as plt
    for feature in drs.db.columns:
        if feature == 'time':
            continue

        t, f = drs.db['time'], drs.db[feature]
        plt.xlabel("Time")
        plt.ylabel(feature)
        plt.title(feature)
        plt.plot(t, f)
        plt.show()

