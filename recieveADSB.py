import requests
import json


def receiveADSB(dlat, dlon, qrad):  # Defines a function that takes the device's latitude (dlat), longitude (dlon), and query radius (qrad)

    baseurl = "https://adsbexchange-com1.p.rapidapi.com/v2"
    fullurl = baseurl + "/lat/" + str(dlat) + "/lon/" + str(dlon) + "/dist/" + str(qrad) + "/"
    # Combines the url with the device latitude, longitude and query radius

# url = "https://adsbexchange-com1.p.rapidapi.com/v2/lat/51.46888/lon/-0.45536/dist/250/"

    headers = {
        "X-RapidAPI-Key": "",
        "X-RapidAPI-Host": "adsbexchange-com1.p.rapidapi.com"
    }  # API password keys

    response = requests.get(fullurl, headers=headers)  # Gets data from ADS-B exchange

    global data
    data = json.loads(response.text)  # Converts it to a dictionary

    print(f"The current number of airborne aircraft within a {qrad} NM radius is {data['total']}.")


receiveADSB(51.4688, -0.45536, 25)  # Runs function and
