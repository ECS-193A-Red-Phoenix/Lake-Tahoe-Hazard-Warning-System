""" The purpose of this file is to encapsulate an interface for gathering
Lake Tahoe Station data from AWS.

"""

import datetime
import requests


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
    pass # TODO Unimplemented
