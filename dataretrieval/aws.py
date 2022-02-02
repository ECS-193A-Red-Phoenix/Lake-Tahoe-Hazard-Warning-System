""" The purpose of this file is to encapsulate an interface for gathering
Lake Tahoe Station data from AWS.

"""

from math import nan
from collections import defaultdict
import pandas as pd
import datetime
import requests


def get_uscg_json(start_date, id=1, end_date=None):
    """ Retrieves data from the Lake Tahoe USCG Station
    The JSON data contains an array of objects in the following format
    {
        'ID': '1', 
        'Station_Name': 'USCG2020', 
        'TmStamp': '2021-01-04 23:40:00', 
        'Batt_V': '13.83', 
        'LoggerTemp_C': '4.521', 
        'AirTemp_C': '2.958', 
        'RH_percent': '85.1', 
        'WindSpd_ms': '7.971', 
        'WindDir_deg': '243.3', 
        'WindSpdMax_ms': '15.28', 
        'Precip_mm': '0.1', 
        'WaterTemp_C': '3.535637', 
        'BP_mbar': '805.8001', 
        'ShortWaveIn_wm2': '27.8', 
        'ShortWaveOut_wm2': '1.658', 
        'LongWaveInRaw_wm2': '-12.47', 
        'LongWaveOutRaw_wm2': '8.14', 
        'LongWaveInCorr_wm2': '314.7', 
        'LongWaveOutCorr_wm2': '335.3', 
        'NR01TC_Avg': '2.458', 
        'NR01TK_Avg': '275.6', 
        'NetRs_Avg': '26.14', 
        'NetRl_Avg': '-20.6', 
        'Albedo_Avg': '0.06', 
        'UpTot_Avg': '15.33', 
        'DnTot_Avg': '9.8', 
        'NetTot_Avg': '5.534'
    }

    Args:
        start_date (datetime.datetime): starting date of query
        id (int, optional): Station ID, Currently there is only 1 Station. Defaults to 1.
        end_date (datetime.datetime, optional): end date of query. Defaults to None (24 hour period).
    """
    format_date = lambda date: date.strftime("%Y%m%d") 
    params = {
        "id": id,
        "rptdate": format_date(start_date),
    }
    if end_date is not None:
        params['rptend'] = format_date(end_date)

    url = "https://tepfsail50.execute-api.us-west-2.amazonaws.com/v1/report/met-uscg2020"
    response = requests.get(url, params=params).json()
    return response


def get_nasa_buoy_json(start_date, id=4, end_date=None):
    """Retrieves JSON data from NASA Buoy in Lake Tahoe
    The JSON data contains an array of objects in the following format
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
    },

    Args:
        start_date (datetime): starting date of query
        id (int, optional): NASA Buoy ID in [1, 4]. Defaults to 4.
        end_date (datetime, optional): end date of query. Defaults to None.
    """
    assert 1 <= id <= 4, f"Expected NASA Buoy ID in [1, 4] got {id}"

    format_date = lambda date: date.strftime("%Y%m%d") 
    params = {
        "id": id,
        "rptdate": format_date(start_date),
    }
    if end_date is not None:
        params['rptend'] = format_date(end_date)

    url = "https://tepfsail50.execute-api.us-west-2.amazonaws.com/v1/report/nasa-tb"
    response = requests.get(url, params=params).json()
    return response


def get_near_shore_json(start_date, id=9, end_date=None):
    """Retrieves JSON data from Near Shore station in Lake Tahoe
    The JSON data contains an array of objects in the following format
    {
        "ID": "9",
        "Station_Name": "Tahoe City",
        "TmStamp": "2022-01-22 00:00:00",
        "LS_Chlorophyll_Avg": "194.8053",
        "LS_Temp_Avg": "5.1184",
        "LS_Turbidity_Avg": "14.75914",
        "WaveHeight": "0.0709095"
    }

    Args:
        start_date (datetime): starting date of query
        id (int, optional): Station ID in [1, 9]. Defaults to 9. 
        end_date (datetime, optional): end date of query. Defaults to None.
    """
    assert 1 <= id <= 9, f"Expected Near Shore Station ID in [1, 9] got {id}"

    format_date = lambda date: date.strftime("%Y%m%d") 
    params = {
        "id": id,
        "rptdate": format_date(start_date),
    }
    if end_date is not None:
        params['rptend'] = format_date(end_date)

    url = "https://tepfsail50.execute-api.us-west-2.amazonaws.com/v1/report/ns-station-range"
    response = requests.get(url, params=params).json()
    return response


def get_model_aws_data(start_date, end_date=None):
    """Retrieves Lake Tahoe data from AWS and formats it to be only the
    the data that the model requires

    Args:
        start_date (datetime): start date of the query
        end_date (datetime, optional): end date of the query. Defaults to None.
    Returns:
        pandas.DataFrame Object
    """
    parse_date = lambda date: datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

    buoy_json = get_nasa_buoy_json(start_date)
    uscg_json = get_uscg_json(start_date)

    features = ["shortwave", "air temp", "atmospheric pressure", "relative humidity", "longwave", "wind u", "wind v"]
    data = defaultdict(lambda: [nan] * len(features))

    for data_sample in buoy_json:
        time = parse_date(data_sample['TmStamp'])
        air_temp1 = float(data_sample['AirTemp_1'])
        air_temp2 = float(data_sample['AirTemp_2'])
        wind_dir1 = float(data_sample['WindDir_1'])
        wind_dir2 = float(data_sample['WindDir_2'])
        wind_speed1 = float(data_sample['WindSpeed_1'])
        wind_speed2 = float(data_sample['WindSpeed_2'])
        wind_u = nan # TODO function of wind_dir and speed
        wind_v = nan # TODO function of wind_dir and speed

        data[time][features.index("air temp")] = (air_temp1 + air_temp2) / 2
        data[time][features.index("wind u")] = wind_u
        data[time][features.index("wind v")] = wind_v

    for data_sample in uscg_json:
        time = parse_date(data_sample['TmStamp'])
        shortwave_in = float(data_sample['ShortWaveIn_wm2']) 
        shortwave_out = float(data_sample['ShortWaveOut_wm2']) 
        bp_mbar = float(data_sample['BP_mbar'])
        rh_percent = float(data_sample['RH_percent'])
        longwave_in_raw = float(data_sample['LongWaveInRaw_wm2']) 
        longwave_out_raw = float(data_sample['LongWaveOutRaw_wm2']) 
        longwave_in_corr = float(data_sample['LongWaveInCorr_wm2']) 
        longwave_out_corr = float(data_sample['LongWaveOutCorr_wm2']) 
        
        shortwave = nan # TODO function of in and out
        atmospheric_pressure = bp_mbar * 100 # Convert mbar to Pa
        relative_humidity = rh_percent / 100 # Convert to fraction
        longwave = nan # TODO function of longwaves

        data[time][features.index("shortwave")] = shortwave
        data[time][features.index("atmospheric pressure")] = atmospheric_pressure
        data[time][features.index("relative humidity")] = relative_humidity
        data[time][features.index("longwave")] = longwave

    df = pd.DataFrame(
        [[time] + features for time, features in data.items()],
        columns=['time'] + features
    )

    df.sort_values(by=['time'])
    return df
