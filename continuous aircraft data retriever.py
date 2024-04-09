import time
import json 
import requests

def retrieveacposition(dlat,dlon,qrad,trackac): # Creates a function to retrieve all relevant position and velocity data based on aircraft hex ID
    baseurl = "https://adsbexchange-com1.p.rapidapi.com/v2"
    fullurl = baseurl + "/lat/" + str(dlat) + "/lon/" + str(dlon) + "/dist/" + str(qrad) + "/"
    # Combines the url with the device latitude, longitude and query radius 

    headers = {
	"X-RapidAPI-Key": "30ea111d16msh15f80fe203bf6dap1bce4bjsn7ad3da2a68d7",
	"X-RapidAPI-Host": "adsbexchange-com1.p.rapidapi.com"
    } # API password keys

    response = requests.get(fullurl, headers=headers) # Gets data from ADS-B exchange
    
    dat = json.loads(response.text) # Converts it to a dictionary
    for items in dat['ac']:
        if items['hex'] == trackac:
            aclon = items['lon']# Aircraft longitude
            aclat = items['lat']# Aircraft latitude
            acalt_baro = items['alt_baro']# Aircraft barometric altitude in feet
            acgs = items['gs']# Aircraft ground speed in knots
            acdir = items['dir'] # 
            
            print(aclon,aclat,acalt_baro,acgs,acdir)
print(f'Retrieving heading, location, altitude, and velocity data for aircraft hex ID {trackhex}.')
while True:
    time.sleep(0.5)
    retrieveacposition(51.4688,-0.45536,50,trackhex)