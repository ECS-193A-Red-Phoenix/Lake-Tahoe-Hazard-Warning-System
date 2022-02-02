""" This file encapsulates all tasks of the data retrieval service
List of Tasks:

1. Retrieve
    - This retrieves data from AWS and NWS and stores it in a database
    - TODO Notes:
    - This currently only retrieves data from NWS since we are missing data 
    from AWS
    - Since MySQL is not set up yet, this will store the retrieved data in a
    csv file. If the csv file already exists, it will append the data to it.

Example Usage:
>>> drs = DataRetrievalService()
>>> drs.retrieve()
"""

from nws import get_model_nws_data
import pandas as pd
import os

class DataRetrievalService:
    CSV_FILE = "./database.csv"

    def __init__(self):
        # Use csv file as database for now
        if os.path.isfile(self.CSV_FILE):
            self.db = pd.read_csv(self.CSV_FILE)
        else:
            self.db = None


    def save(self):
        if self.db is not None:
            self.db.to_csv(self.CSV_FILE)


    def retrieve(self):
        """ Retrieves data from NWS and stores it in database
        """
        nws_data = get_model_nws_data()
        if self.db is None:
            self.db = nws_data
        else:
            earliest_date = nws_data['time'][0]
            self.db = pd.concat([
                self.db[self.db['time'] < earliest_date],
                nws_data
            ])

        self.save()

