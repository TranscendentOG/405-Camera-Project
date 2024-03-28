import requests
import json
import random


def receive_adsb(dlat, dlon, qrad):
    # Defines a function that takes the device's latitude (dlat), longitude (dlon), and query radius (qrad)

    baseurl = "https://adsbexchange-com1.p.rapidapi.com/v2"
    fullurl = baseurl + "/lat/" + str(dlat) + "/lon/" + str(dlon) + "/dist/" + str(qrad) + "/"
    # Combines the url with the device latitude, longitude and query radius

    # url = "https://adsbexchange-com1.p.rapidapi.com/v2/lat/51.46888/lon/-0.45536/dist/250/"

    headers = {
        "X-RapidAPI-Key": "30ea111d16msh15f80fe203bf6dap1bce4bjsn7ad3da2a68d7",
        "X-RapidAPI-Host": "adsbexchange-com1.p.rapidapi.com",
    }  # API password keys

    response = requests.get(fullurl, headers=headers)  # Gets data from ADS-B exchange

    data = json.loads(response.text)  # Converts it to a dictionary

    print(f"The current number of airborne aircraft within a {qrad} NM radius is {data['total']}.")
    return data


def rand_selector(data):  # Creates a function that takes the dictionary data and randomly selects an aircraft
    print("Locating random aircraft...")
    b = random.randint(0, len(data["ac"]))
    randst = data["ac"][b]["dst"]
    trackhex = data["ac"][b]["hex"]
    print(f"The randomly selected aircraft is {randst} NM from the device's location.")
    print(f"The randomly selected aircraft's hex identifier is {trackhex}.")
    return trackhex


def near_selector(data):
    min_dist = 999999
    min_ac = None
    for aircraft in data["ac"]:
        if aircraft["alt_baro"] != "ground":
            if min_dist > aircraft["dst"]:
                min_dist = aircraft["dst"]
                min_ac = aircraft
    return min_ac


if __name__ == "__main__":
    data = receive_adsb(51.4688, -0.45536, 25)  # Runs function and
    track_ran = rand_selector(data)
    track_near = near_selector(data)
