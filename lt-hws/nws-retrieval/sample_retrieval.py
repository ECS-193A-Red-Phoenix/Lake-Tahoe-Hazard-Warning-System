""" 
This file provides a sample retrieval of data from the National Weather Service.
I use the https://api.weather.gov/gridpoints/TOP/gx,gy endpoint to get the data, and save it as nws.json

"""

import requests, json

base_url = "https://api.weather.gov/"

office = "TOP" 
gx, gy = 32, 86
url = base_url + f"gridpoints/{office}/{gx},{gy}"

headers = {
    "User-Agent": "(test, )"
    "Accept: application/geo+json"
}


print("Fetching", url)

response = requests.get(url, headers=headers).json()
with open("./nws.json", "w") as file:
    file.write(json.dumps(response))
print(response)