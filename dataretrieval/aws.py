""" The purpose of this file is to encapsulate an interface for gathering
Lake Tahoe Station data from AWS. 

Note: all timestamps are in UTC
"""

from collections import defaultdict
import numpy as np
import pandas as pd
import datetime
import requests

ENDPOINTS = {
    'USCG': "https://tepfsail50.execute-api.us-west-2.amazonaws.com/v1/report/met-uscg2020",
    'NASA_BUOY': "https://tepfsail50.execute-api.us-west-2.amazonaws.com/v1/report/nasa-tb",
    'NEARSHORE': "https://tepfsail50.execute-api.us-west-2.amazonaws.com/v1/report/ns-station-range"
}

"""
JSON Data Formats (examples)
------------
USCG Station:
{
    'ID': '1',
    'Station_Name': 'USCG2020',
    'TmStamp': '2021-01-04 23:40:00',
        ... (omitted)
    'AirTemp_C': '2.958',
    'NetTot_Avg': '5.534'
}

NASA Buoy:
{
    "ID": "4",
    "Station_Name": "tb4",
    "TmStamp": "2022-01-22 00:00:00",
    "RBR_0p5_m": "5.97",
    "WindSpeed_1": "12.7",
    "AirTemp_1": "1.5",
    "WindDir_1": "53.4",
    "WindSpeed_2": "11.0",
    "AirTemp_2": "1.9",
    "WindDir_2": "199.4"
}

Nearshore:
{
    "ID": "9",
    "Station_Name": "Tahoe City",
    "TmStamp": "2022-01-22 00:00:00",
    "LS_Chlorophyll_Avg": "194.8053",
    "LS_Temp_Avg": "5.1184",
    "LS_Turbidity_Avg": "14.75914",
    "WaveHeight": "0.0709095"
}
"""

## Default station IDs to use

# There is only 1 USCG station with this ID
USCG_ID = 1
# There are 4 NASA buoys with ID's 1-4
NASA_BUOY_ID = 4
# Multiple nearshore stations with ID's 1-9
NEAR_SHORE_ID = 9

"""
Args:
    name (str): endpoint name
    station (int): station id
    start_date (datetime): starting date of query
    end_date (datetime, optional): end date of query
"""
def get_endpoint_json(name, id, start_date, end_date=None):
    # Must specify an endpoint
    if ENDPOINTS.get(name) == None:
        # Given endpoint is invalid
        raise ValueError

    # Set GET request parameters
    # We must specify the start and end time of the desired data
    format_date = lambda date: date.strftime("%Y%m%d")
    params = {
        "id": id,
        "rptdate": format_date(start_date),
    }
    # Also specify end date if applicable
    if end_date is not None:
        params['rptend'] = format_date(end_date)

    # Send request and return data in JSON format
    response = requests.get(ENDPOINTS[name], params=params).json()
    return response

def get_model_historical_data(start_date, end_date=None):
    """Retrieves Lake Tahoe data from AWS and formats it to be only the
    the data that the model requires

    Args:
        start_date (datetime): start date of the query, in UTC
        end_date (datetime, optional): end date of the query. Defaults to None, giving 24 hours after start_date
    Returns:
        pandas.DataFrame Object, example below
                             time  shortwave  air temp  atmospheric pressure  relative humidity  longwave    wind u    wind v 
        2022-02-09 00:00:00+00:00    194.570      8.50              82023.55             0.3351    -125.6 -1.468730 -3.666788 
        2022-02-09 00:20:00+00:00    136.750      8.30              82023.49             0.3080    -125.9  1.883689  5.643954 
        2022-02-09 00:40:00+00:00     83.340      8.80              82029.78             0.3145    -124.6 -6.499837 -0.045988 
        2022-02-09 01:00:00+00:00     39.700      8.15              82031.74             0.2951    -123.2 -5.834419 -0.426680 
        2022-02-09 01:20:00+00:00      4.562      7.70              82042.11             0.3268    -117.6  1.975616  4.593141 
    """
    parse_date = lambda date: datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S") \
                                               .replace(tzinfo=datetime.timezone.utc)

    buoy_json = get_endpoint_json(ENDPOINTS['NASA_BUOY'], NASA_BUOY_ID, start_date, end_date=end_date)
    uscg_json = get_endpoint_json(ENDPOINTS['USCG'], USCG_ID, start_date, end_date=end_date)

    features = ["shortwave", "air temp", "atmospheric pressure", "relative humidity", "longwave", "wind speed", "wind direction"]
    data = defaultdict(lambda: [np.nan] * len(features))

    for data_sample in buoy_json:
        time = parse_date(data_sample['TmStamp'])
        air_temp1 = float(data_sample['AirTemp_1'])
        air_temp2 = float(data_sample['AirTemp_2'])
        wind_dir1 = float(data_sample['WindDir_1'])
        wind_dir2 = float(data_sample['WindDir_2'])
        wind_speed1 = float(data_sample['WindSpeed_1'])
        wind_speed2 = float(data_sample['WindSpeed_2'])
        wind_dir = (wind_dir1 + wind_dir2) / 2
        wind_speed = (wind_speed1 + wind_speed2) / 2

        data[time][features.index("air temp")] = (air_temp1 + air_temp2) / 2
        data[time][features.index("wind speed")] = wind_speed
        data[time][features.index("wind direction")] = wind_dir

    for data_sample in uscg_json:
        time = parse_date(data_sample['TmStamp'])
        shortwave_in = float(data_sample['ShortWaveIn_wm2']) 
        shortwave_out = float(data_sample['ShortWaveOut_wm2']) 
        bp_mbar = float(data_sample['BP_mbar'])
        rh_percent = float(data_sample['RH_percent'])
        longwave_in_corr = float(data_sample['LongWaveInCorr_wm2'])
        
        shortwave = shortwave_in - shortwave_out
        atmospheric_pressure = bp_mbar * 100 # Convert mbar to Pa
        relative_humidity = rh_percent / 100 # Convert to fraction
        longwave = longwave_in_corr

        data[time][features.index("shortwave")] = shortwave
        data[time][features.index("atmospheric pressure")] = atmospheric_pressure
        data[time][features.index("relative humidity")] = relative_humidity
        data[time][features.index("longwave")] = longwave

    df = pd.DataFrame(
        [[time] + features for time, features in data.items()],
        columns=['time'] + features
    )

    # Trim rows that have nan
    rows_with_nan = df.isnull().any(axis=1)
    rows_with_nan = [idx for idx, is_nan in enumerate(rows_with_nan) if is_nan]
    df.drop(axis=0, index=rows_with_nan, inplace=True)

    df.sort_values(by=['time'], inplace=True)
    df.reset_index(inplace=True, drop=True)

    remove_outliers(df)

    # Decompose wind speed and wind direction into vector
    df['wind u'] = np.sin(np.radians(df['wind direction'])) * -1 * df['wind speed']
    df['wind v'] = np.cos(np.radians(df['wind direction'])) * -1 * df['wind speed']
    df.drop('wind direction', axis=1, inplace=True)
    df.drop('wind speed', axis=1, inplace=True)

    # Redundacy here Ensure dataframe leaves with no NaNs
    rows_with_nan = df.isnull().any(axis=1)
    rows_with_nan = [idx for idx, is_nan in enumerate(rows_with_nan) if is_nan]
    df.drop(axis=0, index=rows_with_nan, inplace=True)
    return df


ATTR_BOUNDS = {
    "relative humidity": [0, 1],
    "shortwave": [-0.001, 1300],
    "longwave": [50, 450],
    "atmospheric pressure": [75000, 90000],
    "air temp": [-20, 70],
    "wind speed": [0, 40],
    "wind direction": [0, 360],
}

def remove_outliers(df):
    """ Removes outliers from AWS dataframe, inplace. This is completed in 4 steps.

    1. Median filtering

    2. All data is clipped by some bounds defined in ATTR_BOUNDS. If data is outside
    these bounds are clipped to the edges of these bounds.

    3. All data that deviates more than 3 standard deviations are set to mean of the 
    neighboring 100 points.

    4. All data that is STILL sitting at the bounds are replaced with the mean of the
    neighboring 100 points.

    5. Median filtering again

    Args:
        df (pd.DataFrame): dataframe containing historical AWS model data
    """
    
    median_filtering(df)

    # Clip features between lo and hi
    for feature, (lo, hi) in ATTR_BOUNDS.items():
        # Clip features
        df[feature] = np.clip(df[feature], lo, hi)

    # Set features > 3 std to mean
    for feature in df.columns:
        if feature == 'time':
            continue

        mean = df[feature].rolling(window=100, center=True, min_periods=1).mean()
        std = df[feature].rolling(window=100, center=True, min_periods=1).std()
        std[0] = 0 
        lo = mean - 3 * std
        hi = mean + 3 * std

        # Replace deviating features with mean
        df[feature].where(lo < df[feature], mean, inplace=True)
        df[feature].where(df[feature] < hi, mean, inplace=True)

    for feature, (lo, hi) in ATTR_BOUNDS.items():
        # Shortwave is an edge case, where its okay for data to sit at the bounds
        if feature == 'shortwave':
            continue
        mean = df[feature].rolling(window=100, center=True, min_periods=1).mean()
        df[feature].where(df[feature] != hi, mean, inplace=True)
        df[feature].where(df[feature] != lo, mean, inplace=True)

    median_filtering(df)


def median_filtering(df):
    """Replaces points with the median of neighboring points, inplace

    Args:
        df (pd.DataFrame): DataFrame to filter
    """
    for feature in df.columns:
        if feature == 'time':
            continue
        median = df[feature].rolling(window=5, min_periods=1, center=True).median()
        df[feature] = median