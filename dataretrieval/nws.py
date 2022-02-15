""" The purpose of this file is to encapsulate an interface for getting
data from the National Weather Service.

Suggested Usage:

>>> from dataretrieval.nws import get_model_nws_data
>>> data = get_model_nws_data() # Returns pandas DataFrame object
>>> data.head()
                        time  shortwave   air temp  atmospheric pressure   relative humidity    longwave     wind u     wind v  
0  2022-02-03 12:00:00+00:00        NaN -15.555556                   NaN                  49  158.532795  12.901979  15.765701     
1  2022-02-03 13:00:00+00:00        NaN -16.111111                   NaN                  50  154.217981  12.901979  15.765701   
2  2022-02-03 14:00:00+00:00        NaN -16.666667                   NaN                  53  152.228903  -1.839935 -16.566136   
3  2022-02-03 15:00:00+00:00        NaN -15.555556                   NaN                  48  154.436574  11.729072  14.332455   
4  2022-02-03 16:00:00+00:00        NaN -13.888889                   NaN                  44  166.650116  16.420700  20.065438
"""

from collections import defaultdict
from datetime import timedelta
from math import nan
from dateutil import parser
import requests
import pandas as pd
import numpy as np


def parse_interval(interval):
    """
    Utility function that parses an ISO 8601 date string with a duration of time.
    e.g.  '2022-02-04T02:00:00+00:00/PT4H' represents 4 hours starting from 2 am on 2022-02-04
    
    Expects duration to be formatted as `PTnHnMnS`.

    See https://en.wikipedia.org/wiki/ISO_8601#Time_intervals to see how ISO 8601 timestamps
    are formatted.

    Arguments:
        interval (str): an ISO 8601 date string with an interval
    Returns:
        tuple(datetime.datetime, int): time and duration (in hours)
    """
    solidus = '/' if '/' in interval else '--' if '--' in interval else None
    # Date does not contain interval
    if solidus is None: 
        return parser.parse(interval), 0

    date, duration = interval.split(solidus)
    hours = 0
    integer = 0
    for letter in duration:
        if letter.isdigit():
            integer = 10 * integer + int(letter)
        elif letter == 'H':
            hours += integer # hours
            integer = 0
        elif letter == 'M':
            hours += integer // 60 # 60 min in hour
            integer = 0
        elif letter == 'S':
            hours += integer // 360 # 360 sec in hour
            integer = 0

    return parser.parse(date), hours


def round_to_nearest_hour(date):
    """
    A Utility function that rounds a date to the nearest hour
    Arguments:
        date (datetime.datetime)
    Returns:
        (datetime.datetime)
    """
    if date.minute >= 30:
        return date.replace(hour=date.hour + 1, minute=0, second=0)
    else:
        return date.replace(hour=date.hour, minute=0, second=0)


def get_nws_json():
    """
    Retrieves data from the nws api and returns a dictionary of that data

    gx, gy are constants from the following api call for lake tahoe (39.0961,-120.0397)
    https://api.weather.gov/points/{latitude},{longitude} 
    """
    base_url = "https://api.weather.gov/"
    office = "REV" 
    gx, gy = 33, 87 # Lake Tahoe

    url = base_url + f"gridpoints/{office}/{gx},{gy}"
    headers = {
        "User-Agent": "(Lake Tahoe Hazardous Warning System, maksimovich.sam@gmail.com)",
        "Accept": "application/geo+json"
    }

    response = requests.get(url, headers=headers).json()
    return response


def get_model_forecast_data():
    """
    Retrieves data from the nws api and filters it to contain only data
    required by the model 

    Returns:
        pandas.DataFrame - tabulated model forecast inputs, example below:
                               time  shortwave   air temp  atmospheric pressure   relative humidity    longwave     wind u     wind v  
        0 2022-02-03 12:00:00+00:00        NaN -15.555556                   NaN                  49  158.532795  12.901979  15.765701     
        1 2022-02-03 13:00:00+00:00        NaN -16.111111                   NaN                  50  154.217981  12.901979  15.765701   
        2 2022-02-03 14:00:00+00:00        NaN -16.666667                   NaN                  53  152.228903  -1.839935 -16.566136   
        3 2022-02-03 15:00:00+00:00        NaN -15.555556                   NaN                  48  154.436574  11.729072  14.332455   
        4 2022-02-03 16:00:00+00:00        NaN -13.888889                   NaN                  44  166.650116  16.420700  20.065438                                                                            

    Units:         pandas Timestamp        wm2    Celcius                    Pa            fraction         wm2         ms         ms
    """
    features = ["time", "shortwave", "air temp", "atmospheric pressure", "relative humidity", "longwave", "wind u", "wind v"]

    # Attempt to get data from NWS API multiple times
    # Sometimes API fails and gives us 'Unexpected Problem' as a response
    for req_attempt in range(5):
        data = get_nws_json()
        if 'properties' in data:
            # API returned data successfully
            break

    if 'properties' not in data:
        # API failed to return data multiple times
        # API is most likely down, so return empty data table
        return pd.DataFrame(columns=features)

    nws_features = ['windDirection', 'windSpeed', 'temperature', 'skyCover', 'relativeHumidity']
    model_data = defaultdict(lambda: [nan] * len(nws_features))
    
    for f_idx, feature in enumerate(nws_features):
        for sample in data['properties'][feature]['values']:
            # The NWS gives us not dates, but intervals of time
            # I parse the interval of time, including its start and duration
            # I convert the start to the nearest hour and sample for every hour in the duration
            time, duration = parse_interval(sample['validTime'])
            value = sample['value']
            time = round_to_nearest_hour(time)

            for hour in range(0, duration):
                model_data[time + timedelta(hours=hour)][f_idx] = value

    df = pd.DataFrame(
        [[time] + values for time, values in model_data.items()],
        columns=['time'] + nws_features
    )
    # Rename NWS labels to be consistent with AWS
    df.rename(columns={"temperature" : "air temp", "relativeHumidity": "relative humidity"}, inplace=True)

    # Trim rows with nan
    rows_with_nan = df.isnull().any(axis=1)
    rows_with_nan = [idx for idx, is_nan in enumerate(rows_with_nan) if is_nan]
    df.drop(axis=0, index=rows_with_nan, inplace=True)

    # Temporary shortwave formula based on historical AWS data
    hourize = lambda t: t.hour + t.minute / 60
    f = lambda t: 5.1276e+02 * np.exp(-9.4720e-02 * (t - 1.1238e-01)**2)
    g = lambda t: f(((hourize(t) + -10) % 24) - 10)
    df['shortwave'] = [g(t_i) for t_i in df['time']]

    # Based on historical pressure and confirmed by barometric pressure eq 
    df['atmospheric pressure'] = 81600 # Pa

    # Convert relative humidity to a fraction
    df['relative humidity'] /= 100

    # Decompose windDirection and windSpeed into vector
    df['wind u'] = np.cos(np.radians(df['windDirection'])) * df['windSpeed'] / 3.6 # Convert km/h to m/s
    df['wind v'] = np.sin(np.radians(df['windDirection'])) * df['windSpeed'] / 3.6 
    df.drop('windDirection', axis=1, inplace=True)
    df.drop('windSpeed', axis=1, inplace=True)

    # Add Longwave as a function of AirTemp and Cloud Cover 
    df['longwave'] = 0.937e-5 * 0.97 * 5.67e-8 * ((df['air temp'] + 273.16)**6) * (1 + 0.17*(df['skyCover'] / 100))
    df.drop('skyCover', axis=1, inplace=True)

    # Reorder columns to be consistent with AWS dataframe
    df = df[features]

    df.sort_values(by=['time'])
    df.reset_index(inplace=True, drop=True)
    return df