import paho.mqtt.client as MyMqtt
import json, time

### GLOBAL VARIABLES ###

TelemetryTopic = "v1/devices/me/telemetry"
RPCrequestTopic = 'v1/devices/me/rpc/request/+'
client = MyMqtt.Client()

########################

# MQTT on_connect callback function
def on_connect(client, userdata, flags, rc):
    print("rc code:", rc)
    client.subscribe(RPCrequestTopic)
    
# MQTT on_message callback function
def on_message(client, userdata, msg):        
    if msg.topic.startswith('v1/devices/me/rpc/request/'):
        data = json.loads(msg.payload)
        if data['method'] == 'setValue':
            params = data['params'] # Turn the pump on/off
            setValue(params)
            
def IOTConnect():
    # Initialize variables and MQTT details
    iot_hub = "demo.thingsboard.io"
    port = 1883
    username = " " # <==== Enter your device token from TB here
    password = ""                
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(username, password)
    client.connect(iot_hub, port)
    client.loop_start()
    print("Connection successful")
    
def SendDatatoBoard(Packet, hexID, aclat, aclon, alt, airspeed, pitch, yaw):
    data_out = {"Packet": Packet, # Current packet number
                "HexID": hexID, # Tracked aircraft hex ID
                "Latitude": aclat, # Tracked aircraft latitude
                "Longitude": aclon, # Tracked aircraft longitude
                "Altitude": alt, # Tracked aircraft altitude (barometric?)
                "Airspeed": airspeed, # Tracked aircraft airspeed
                "Pitch": pitch, # Device pitch
                "Yaw": yaw # Device yaw
        }
    print("data_out=",data_out)
    JSON_data_out = json.dumps(data_out) # Convert to JSON format
    client.publish(TelemetryTopic, JSON_data_out, 0) # Publish data to MQTT server
    time.sleep(1)
    print('---------------------------')

# Publish data to MQTT server
IOTConnect()
try:
    i=1
    while True: # Main loop for the program
        SendDatatoBoard(i,0,0,0,0,0,0,0)
        i=i+1
        
except KeyboardInterrupt:
    print("Disconnected")
    client.disconnect()
    client.loop_stop() # Stop callback loop for MQTT

