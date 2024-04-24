import requests
import json
import random
import secret
import distance

def receive_adsb(dlat, dlon, qrad):
    # Defines a function that takes the device's latitude (dlat), longitude (dlon), and query radius (qrad)

    baseurl = "https://adsbexchange-com1.p.rapidapi.com/v2"
    fullurl = baseurl + "/lat/" + str(dlat) + "/lon/" + str(dlon) + "/dist/" + str(qrad) + "/"
    # Combines the url with the device latitude, longitude and query radius

    # url = "https://adsbexchange-com1.p.rapidapi.com/v2/lat/51.46888/lon/-0.45536/dist/250/"

    headers = {
        "X-RapidAPI-Key": secret.key_adsb,
        "X-RapidAPI-Host": "adsbexchange-com1.p.rapidapi.com",
    }  # API password keys

    response = requests.get(fullurl, headers=headers)  # Gets data from ADS-B exchange

    data = json.loads(response.text)  # Converts it to a dictionary

    #print(f"The current number of airborne aircraft within a {qrad} NM radius is {data['total']}.")
    return data


def rand_selector(dlat,dlon, qrad):  # Creates a function that takes the dictionary data and randomly selects an aircraft
    
    data = receive_adsb(dlat, dlon, qrad)
    b = random.choice(data['ac'])
    return b


def near_selector(dlat,dlon, qrad):
    
    data = receive_adsb(dlat, dlon, qrad)
    
    min_dist = 999999
    min_ac = None
    
    for aircraft in data["ac"]:
        
        if 'alt_baro' in aircraft.keys():
            height = aircraft["alt_baro"]
        elif 'alt_geom' in aircraft.keys():
            height = aircraft["alt_geom"]
        else:
            continue
        
        if (height != "ground") and (height > 0):
            delta_lat = dlat - aircraft['lat']
            delta_lon = dlat - aircraft['lon']
            dist = (delta_lat**2 + delta_lon**2)**0.5
            
            if min_dist > dist:
                min_dist = dist
                min_ac = aircraft

    return min_ac

def near_selector_bearing(dlat, dlon, qrad, bearing_min, bearing_max):
    
    data = receive_adsb(dlat, dlon, qrad)
    
    min_dist = 999999
    min_ac = None
    
    # There are no aircraft within the radius.
    if 'ac' not in data.keys():
        return None

    
    for aircraft in data["ac"]:
        
        aircraft['bearing'] = distance.find_bearing(dlat, dlon, aircraft['lat'], aircraft['lon'])
        
        if aircraft['bearing'] <0:
            aircraft['bearing'] = 360 + aircraft['bearing']
        
        if bearing_min < aircraft['bearing'] < bearing_max:
    
            if 'alt_baro' in aircraft.keys():
                height = aircraft["alt_baro"]
            elif 'alt_geom' in aircraft.keys():
                height = aircraft["alt_geom"]
            else:
                continue
            
            if (height != "ground") and (height > 700):
                delta_lat = dlat - aircraft['lat']
                delta_lon = dlon - aircraft['lon']
                dist = (delta_lat**2 + delta_lon**2)**0.5
                
                if min_dist > dist:
                    min_dist = dist
                    min_ac = aircraft
                    
    return min_ac


if __name__ == "__main__":
    data = near_selector_bearing(45.630, -122.610, 25, 188, 355.4)
    print(data)
