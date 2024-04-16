import requests
headers = {
    'api-auth': "your uuid"
}
response = requests.get('https://adsbexchange.com/api/aircraft/lat/51.5005/lon/-0.1145/dist/100/', headers = headers)
data = response.text
print(data)
