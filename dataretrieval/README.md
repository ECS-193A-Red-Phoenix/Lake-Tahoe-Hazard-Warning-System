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
