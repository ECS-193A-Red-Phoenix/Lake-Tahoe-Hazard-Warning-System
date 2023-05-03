""" The purpose of this file is to encapsulate an interface for gathering
Lake Tahoe Station data from AWS. 

Note: all timestamps are in UTC
"""

from bisect import bisect_left
from collections import defaultdict
import numpy as np
import pandas as pd
import datetime
import requests

ENDPOINTS = {
    'USCG': "https://tepfsail50.execute-api.us-west-2.amazonaws.com/v1/report/met-uscg2020",
    'NASA_BUOY': "https://tepfsail50.execute-api.us-west-2.amazonaws.com/v1/report/nasa-tb",
    'NEARSHORE': "https://tepfsail50.execute-api.us-west-2.amazonaws.com/v1/report/ns-station-range",
    'TEMPERATURE_CHAIN': "https://tepfsail50.execute-api.us-west-2.amazonaws.com/v1/report/tc-homewood"
}

## Default station IDs to use

# There is only 1 USCG station with this ID
USCG_ID = 1
# There are 4 NASA buoys with ID's 1-4
NASA_BUOY_ID = 4
# Multiple nearshore stations with ID's 1-9
NEAR_SHORE_ID = 9

"""
Args:
    url (str): endpoint url
    station (int): station id
    start_date (datetime): starting date of query
    end_date (datetime, optional): end date of query.
"""
def get_endpoint_json(url, id, start_date, end_date=None):
    # Set GET request parameters
    format_date = lambda date: date.strftime("%Y%m%d")
    params = {
        "id": id,
        "rptdate": format_date(start_date),
    }
    # Also specify end date if applicable
    if end_date is not None:
        params['rptend'] = format_date(end_date)

    # Send request and return data in JSON format
    response = requests.get(url, params=params)

    response_json = response.json()
    if response_json is None or len(response_json) == 0:
        raise Exception(f"AWS endpoint failed: {response.url}")

    return response_json


def get_model_ctd_profile(date):
    """ Creates a ctd profile by combining instrument data from the Homewood nearshore
        station and temperature chain at HWTC
        Note:
        - Instrument gives data in regular intervals of 20 minutes
        so we just pick the data that is closest to the given date
        
        Args:
            date (datetime): the date of the desired ctd profile
    """
    ctd_profile = []
    
    # Retrieve data from homewood station
    homewood_data = get_endpoint_json(ENDPOINTS['NEARSHORE'], 4, date)

    # Pick closest date within given data
    parse_date = lambda date: datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S") \
                                               .replace(tzinfo=datetime.timezone.utc)
    data_dates = [parse_date(d["TmStamp"]) for d in homewood_data]
    closest_date_idx = bisect_left(data_dates, date)
    if closest_date_idx >= len(homewood_data):
        closest_date_idx = len(homewood_data) - 1
    closest_data_sample = homewood_data[closest_date_idx]

    # Get [depth, temperature] tuple from homewood data
    homewood_depth = 2.0
    homewood_temperature = float(closest_data_sample['LS_Temp_Avg'])


    ctd_profile.append((homewood_depth, homewood_temperature))

    ####################### Temperature Chain ##########################

    # Actual measurements of the temperature chain
    tc_dimensions = {
        "P1": 2.5,
        "C1": 2.5,
        "L16": 2.5,
        "L15": 7.5,
        "L14": 12.5,
        "L13": 17.5,
        "L12": 27.5,
        "L11": 37.5,
        "L10": 47.5,
        "L9": 57.5,
        "L8": 67.5,
        "L7": 72.5,
        "L6": 77.5,
        "L5": 82.5,
        "L4": 87.5,
        "L3": 92.5,
        "L2": 97.5,
        "L1": 102.5,
        "C2": 5
    }

    # ID #"s of the sensors on the TC
    tc_sensor_ids = list(range(1, 17))

    def get_depth(tc_depth, tc_sensor_id):
        # Returns the depth of a particular sensor
        # Arguments:
        #  tc_depth: the depth of the temperature chain
        #  tc_sensor_id: an Integer in [1, 16], the ID of the temperature sensor
        return tc_depth - tc_dimensions["P1"] - tc_dimensions[f'L{tc_sensor_id}']

    # Retrieve data from temperature chain
    tc_data = get_endpoint_json(ENDPOINTS['TEMPERATURE_CHAIN'], 0, date)

    # Pick closest date within given data
    data_dates = [parse_date(d["TmStamp"]) for d in tc_data]
    closest_date_idx = bisect_left(data_dates, date)
    if closest_date_idx >= len(tc_data):
        closest_date_idx = len(tc_data) - 1
    closest_data_sample = tc_data[closest_date_idx]

    # Extract [depth, temperature] tuples from data
    tc_depth = float(closest_data_sample["Depth_m4C_Avg"])
    for sensor_id in tc_sensor_ids:
        depth = get_depth(tc_depth, sensor_id)
        temperature = float(closest_data_sample[f"LS_T{sensor_id}_Avg"])

        ctd_profile.append((depth, temperature))

    if np.isnan(ctd_profile[0,1])
        ctd_profile[0,1] = ctd_profile[1,1]

    return ctd_profile

"""
1. Retrieves Lake Tahoe data from AWS
2. Preprocesses the data so the model can use it

Args:
    start_date (datetime): start date of the query, in UTC. Starts at midnight
    end_date (datetime, optional): end date of the query. Set 24 hours after the start date by default
Returns:
    pandas.DataFrame Object, example below
                            time  shortwave  air temp  atmospheric pressure  relative humidity  longwave    wind u    wind v 
    2022-02-09 00:00:00+00:00    194.570      8.50              82023.55             0.3351    -125.6 -1.468730 -3.666788 
    2022-02-09 00:20:00+00:00    136.750      8.30              82023.49             0.3080    -125.9  1.883689  5.643954 
    2022-02-09 00:40:00+00:00     83.340      8.80              82029.78             0.3145    -124.6 -6.499837 -0.045988 
    2022-02-09 01:00:00+00:00     39.700      8.15              82031.74             0.2951    -123.2 -5.834419 -0.426680 
    2022-02-09 01:20:00+00:00      4.562      7.70              82042.11             0.3268    -117.6  1.975616  4.593141 
"""
def get_model_historical_data(start_date, end_date=None):
    parse_date = lambda date: datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S") \
                                               .replace(tzinfo=datetime.timezone.utc)

    buoy_json = get_endpoint_json(ENDPOINTS['NASA_BUOY'], NASA_BUOY_ID, start_date, end_date=end_date)
    uscg_json = get_endpoint_json(ENDPOINTS['USCG'], USCG_ID, start_date, end_date=end_date)

    features = ["shortwave", "air temp", "atmospheric pressure", "relative humidity", "longwave", "wind speed", "wind direction"]

    # Historical data to build and return
    historical = defaultdict(lambda: [np.nan] * len(features))

    ## Parse data samples
    # NASA Buoy data samples
    for data_sample in buoy_json:
        # Parse raw data from JSON
        time = parse_date(data_sample['TmStamp'])
        air_temp1 = float(data_sample['AirTemp_1'])
        air_temp2 = float(data_sample['AirTemp_2'])
        wind_dir1 = float(data_sample['WindDir_1'])
        wind_dir2 = float(data_sample['WindDir_2'])
        wind_speed1 = float(data_sample['WindSpeed_1'])
        wind_speed2 = float(data_sample['WindSpeed_2'])

        # Take average of raw data that was measured with two instruments
        wind_dir = (wind_dir1 + wind_dir2) / 2
        wind_speed = (wind_speed1 + wind_speed2) / 2
        air_temp = (air_temp1 + air_temp2) / 2
        # Save data for this sample
        historical[time][features.index("air temp")] = air_temp
        historical[time][features.index("wind speed")] = wind_speed
        historical[time][features.index("wind direction")] = wind_dir

    # USCG data samples
    for data_sample in uscg_json:
        # Parse raw data
        time = parse_date(data_sample['TmStamp'])
        shortwave_in = float(data_sample['ShortWaveIn_wm2']) 
        shortwave_out = float(data_sample['ShortWaveOut_wm2']) 
        bp_mbar = float(data_sample['BP_mbar'])
        rh_percent = float(data_sample['RH_percent'])
        longwave_in_corr = float(data_sample['LongWaveInCorr_wm2'])

        # Calculations
        shortwave = shortwave_in - shortwave_out
        atmospheric_pressure = bp_mbar * 100 # Convert mbar to Pa
        relative_humidity = rh_percent / 100 # Convert to fraction
        longwave = longwave_in_corr

        # Save data for this sample
        historical[time][features.index("shortwave")] = shortwave
        historical[time][features.index("atmospheric pressure")] = atmospheric_pressure
        historical[time][features.index("relative humidity")] = relative_humidity
        historical[time][features.index("longwave")] = longwave

    # Convert historical data to dataframe
    df = pd.DataFrame(
        [[time] + features for time, features in historical.items()],
        columns=['time'] + features
    )

    # Trim rows that have nan
    rows_with_nan = df.isnull().any(axis=1)
    rows_with_nan = [idx for idx, is_nan in enumerate(rows_with_nan) if is_nan]
    df.drop(axis=0, index=rows_with_nan, inplace=True)

    df.sort_values(by=['time'], inplace=True, ignore_index=True)

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
        if feature in df.columns:
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
        if feature == 'shortwave' or feature not in df.columns:
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
