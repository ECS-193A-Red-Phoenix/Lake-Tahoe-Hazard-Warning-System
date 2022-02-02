""" The purpose of this file is to encapsulate an interface for getting
data from the National Weather Service.

Suggested Usage:

>>> from dataretrieval.nws import get_model_nws_data
>>> data = get_model_nws_data() # Returns pandas DataFrame object
>>> data
>>>
                         time  windDirection  windSpeed  temperature  skyCover  relativeHumidity
0   2022-01-28 19:00:00+00:00            230      3.704    -0.555556        22                51
1   2022-01-28 20:00:00+00:00            220      7.408     1.111111        14                45
2   2022-01-28 21:00:00+00:00            220      7.408     1.666667         5                47
3   2022-01-28 22:00:00+00:00            220      9.260     1.666667         5                48
4   2022-01-28 23:00:00+00:00            210      5.556     3.333333         4                44
..                        ...            ...        ...          ...       ...               ...
169 2022-02-04 20:00:00+00:00            260     18.520    -4.444444        32                54
170 2022-02-04 21:00:00+00:00            260     18.520    -3.888889        34                55
171 2022-02-04 22:00:00+00:00            270     16.668    -3.888889        34                55
172 2022-02-04 23:00:00+00:00            300     14.816    -5.000000        35                59
173 2022-02-05 00:00:00+00:00            310     11.112    -6.111111        35                62
"""

from collections import defaultdict
from datetime import timedelta
from math import nan
from dateutil import parser
import requests
import pandas as pd


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


def get_nws_data():
    """
    Retrieves data from the nws api and returns a dictionary of that data
    """
    base_url = "https://api.weather.gov/"
    office = "TOP" 
    gx, gy = 32, 86

    url = base_url + f"gridpoints/{office}/{gx},{gy}"
    headers = {
        "User-Agent": "(Lake Tahoe Hazardous Warning System, maksimovich.sam@gmail.com)",
        "Accept": "application/geo+json"
    }

    response = requests.get(url, headers=headers).json()
    return response


def get_model_nws_data():
    """
    Retrieves data from the nws api and filters it to contain only data
    required by the model 

    Returns:
        pandas.DataFrame - tabulated NWS data, example below:
    ################################################################################################
                           time    windDirection  windSpeed  temperature  skyCover  relativeHumidity
    0 2022-01-28 19:00:00+00:00              230      3.704    -0.555556        22                51
    1 2022-01-28 20:00:00+00:00              220      7.408     1.111111        14                45   
    2 2022-01-28 21:00:00+00:00              220      7.408     1.666667         5                47   
    3 2022-01-28 22:00:00+00:00              220      9.260     1.666667         5                48   
    4 2022-01-28 23:00:00+00:00              210      5.556     3.333333         4                44   
                                                                                                    
    Units:     pandas Timestamp   degrees (angle)      km/h      Celcius   percent           percent
    """
    data = get_nws_data()
    features = ['windDirection', 'windSpeed', 'temperature', 'skyCover', 'relativeHumidity']
    
    # Create a dictionary (time (str)) -> List[temperature, ..., ]
    model_data = defaultdict(lambda: [nan for i in range(len(features))])
    
    for f_idx, feature in enumerate(features):
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
        columns=['time'] + features
    )

    # Trim rows with nan
    rows_with_nan = df.isnull().any(axis=1)
    rows_with_nan = [idx for idx, is_nan in enumerate(rows_with_nan) if is_nan]
    df.drop(axis=0, index=rows_with_nan, inplace=True)

    # Add Longwave as a function of AirTemp and Cloud Cover 
    # Hlwin = 0.937e-5 * 0.97 * 5.67e-8 * ((AirT + 273.16)**6) * (1 + 0.17*Cl)
    df['longwave'] = 0.937e-5 * 0.97 * 5.67e-8 * ((df['temperature'] + 273.16)**6) * (1 + 0.17*(df['skyCover'] / 100))
    
    df.sort_values(by=['time'])
    return df

