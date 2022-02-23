*This document is work in progress*
# Data Retrieval Service

## Purpose
The data retrieval service, `service.py`, is a Python script that continuously:
1. Fetches meterological data from:
- TERC's AWS (Amazon Web Services) API
- National Weather Service API
2. Parses the meterological data into an input file called `surfbc.txt`

<!--
## Model Parameters
This document lists the required parameters as input.
-->

## TERC AWS API
TERC provides the following parameters through these stations:
1. NASA buoy
    1. Air temperature
    2. Wind direction
    3. Wind speed
2. US Coast Guard
    1. Shortwave
    2. Atmospheric pressure
    3. Relative humidity
    4. Longwave

### JSON Formats
USCG Station:
```
{
    'ID': '1',
    'Station_Name': 'USCG2020',
    'TmStamp': '2021-01-04 23:40:00',
        ... (omitted)
    'AirTemp_C': '2.958',
    'NetTot_Avg': '5.534'
}
```
NASA Buoy:
```
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
```
Nearshore:
```
{
    "ID": "9",
    "Station_Name": "Tahoe City",
    "TmStamp": "2022-01-22 00:00:00",
    "LS_Chlorophyll_Avg": "194.8053",
    "LS_Temp_Avg": "5.1184",
    "LS_Turbidity_Avg": "14.75914",
    "WaveHeight": "0.0709095"
}
```

## National Weather Service API
NWS API provides the following parameters:
1. Air temperature
2. Relative humidity
3. Wind speed
4. Wind direction
5. Sky cover

### Conversion to model parameters
- Wind speed and wind direction are used to get wind vectors (u and v).
- Sky cover is used to get longwave.
