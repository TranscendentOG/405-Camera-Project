# Python 3.7.3

import time
import json
import RPi.GPIO as GPIO
import paho.mqtt.client as MyMqtt
from stepper import StepperDriver
import secret
import distance
import adsb

# Motor driver  pins
PIN_PITCH_STEP = 21
PIN_PITCH_DIR = 20
PIN_YAW_STEP = 24
PIN_YAW_DIR = 23

# Limit switch pins
PIN_PITCH_UPPER = 22
PIN_PITCH_LOWER = 27
PIN_YAW_LEFT = 19
PIN_YAW_RIGHT = 26

STEPDELAY_FAST = 0.005
STEPDELAY_MED = 0.025
STEPDELAY_SLOW = 0.100

# degrees per step
STEP_DEGREES_PITCH = 0.9  # half stepping
STEP_DEGREES_YAW = 1.8 # full stepping

# Tuning offset for each axis. Adjust if the home angle does not correspond to the measured angle.
PITCH_OFFSET = -4
YAW_OFFSET =  188

TelemetryTopic = "v1/devices/me/telemetry"
RPCrequestTopic = 'v1/devices/me/rpc/request/+'

def assert_msg(condition, message):
    """Raises a RuntimeError with message if condition is false."""
    if not condition:
        raise RuntimeError(message)

class Engine:
    def __init__(self):

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(PIN_PITCH_STEP, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(PIN_PITCH_DIR, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(PIN_YAW_STEP, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(PIN_YAW_DIR, GPIO.OUT, initial=GPIO.LOW)

        GPIO.setup(PIN_PITCH_UPPER, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(PIN_PITCH_LOWER, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(PIN_YAW_LEFT, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(PIN_YAW_RIGHT, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        self.pitch_motor = StepperDriver(PIN_PITCH_DIR, PIN_PITCH_STEP)
        self.yaw_motor = StepperDriver(PIN_YAW_DIR, PIN_YAW_STEP)

        # Position of each limit in steps
        self.pitch_upper_limit = None
        self.pitch_lower_limit = None
        self.yaw_left_limit = None
        self.yaw_right_limit = None

        # Total amount of travel, in degrees, as measured by the limit switches
        self.pitch_span = None
        self.yaw_span = None

        self.device_lat = secret.device_lat  # Degrees, latitude of the device
        self.device_lon = secret.device_lon  # Degrees, longitude of the device
        self.device_alt = secret.device_alt  # meters, height of the device above sea level, https://en-us.topographic-map.com/

        self.client = MyMqtt.Client()

    def current_pitch(self):
        return (self.pitch_lower_limit - self.pitch_motor.steps )*STEP_DEGREES_PITCH + PITCH_OFFSET

    def current_yaw(self):
        return(self.yaw_left_limit - self.yaw_motor.steps)*STEP_DEGREES_YAW + YAW_OFFSET

    def home(self):
        def find_limit(motor, limit_switch, clockwise, max_steps, fastdelay):
            """Returns the position of the limit, in steps, for a given motor and limit switch.

            motor is the motor object.
            Limit_switch_pin is the pin that the limit switch will pull high.
            max_steps is the maximum number of steps this axis should be able to move.

            Returns the step before the limit switch is triggered.

            Derived in part from https://github.com/gavinlyonsrepo/RpiMotorLib/blob/master/RpiMotorLib/RpiMotorLib.py"""

            # Look for a rising edge on the limit switch
            GPIO.add_event_detect(limit_switch, GPIO.RISING,bouncetime=50)

            # Approach the limit switch, and stop when it is triggered.
            for i in range(max_steps):
                triggered = GPIO.event_detected(limit_switch)
                if not triggered:
                    motor.motor_step(clockwise=clockwise, stepdelay=fastdelay)
                else:
                    break

            # Remove the event detection before the function can return
            GPIO.remove_event_detect(limit_switch)

            # End the function call if the limit switch was not found
            if not triggered:
                return None

            # Now look for a falling edge
            GPIO.add_event_detect(limit_switch, GPIO.FALLING,bouncetime=50)

            # Slowly move away from the limit switch until it is no longer triggered.
            # The step when it is no longer triggered is the limit.
            for i in range(max_steps):
                triggered = GPIO.event_detected(limit_switch)
                if triggered:
                    motor.motor_step(clockwise=not clockwise, stepdelay=STEPDELAY_SLOW)
                else:
                    limit = motor.steps
                    break

            # Remove the event detection before the function can return
            GPIO.remove_event_detect(limit_switch)

            # limit will either be an integer representing the limit, or None, indicating that it failed
            return limit

        # Approximately the max number of steps needed to reach the limit switch
        max_steps_pitch = int(110 / STEP_DEGREES_PITCH)
        max_steps_yaw = int(220 / STEP_DEGREES_YAW)

        # Find the limits, in steps, for the pitch axis
        self.pitch_upper_limit = find_limit(motor=self.pitch_motor, limit_switch=PIN_PITCH_UPPER, clockwise=True, max_steps=max_steps_pitch, fastdelay=STEPDELAY_FAST)
        assert_msg(self.pitch_upper_limit!=None,'Failed to find pitch upper limit')
        print("Homing success: Pitch Upper")
        self.pitch_lower_limit = find_limit(motor=self.pitch_motor, limit_switch=PIN_PITCH_LOWER, clockwise=False, max_steps=max_steps_pitch, fastdelay=STEPDELAY_FAST)
        assert_msg(self.pitch_lower_limit!=None,'Failed to find pitch lower limit')
        print("Homing success: Pitch Lower")
        # The pitch axis should now be at home

        # Record the total travel possible on the pitch axis
        self.pitch_span = (self.pitch_lower_limit - self.pitch_upper_limit)*STEP_DEGREES_PITCH

        # # Find the limits, in steps, for the yaw axis
        self.yaw_left_limit = find_limit(motor=self.yaw_motor, limit_switch=PIN_YAW_LEFT, clockwise=True, max_steps=max_steps_yaw, fastdelay=STEPDELAY_MED)
        assert_msg(self.yaw_left_limit != None, 'Failed to find yaw left limit')
        print("Homing success: Yaw Left")
        self.yaw_right_limit = find_limit(motor=self.yaw_motor, limit_switch=PIN_YAW_RIGHT, clockwise=False, max_steps=max_steps_yaw, fastdelay=STEPDELAY_MED)
        assert_msg(self.yaw_right_limit != None, 'Failed to find yaw right limit')
        print("Homing success: Yaw Right")

        # Record the total travel possible on the yaw axis
        self.yaw_span = (self.yaw_right_limit - self.yaw_left_limit)*STEP_DEGREES_YAW

        # Move the device to the center of the yaw axis
        steps = int(self.yaw_span/(2*STEP_DEGREES_YAW))
        self.yaw_motor.motor_go(clockwise=True, steps=steps,stepdelay=STEPDELAY_FAST)



    def point(self, aircraft):
        # Point the camera at the current aircraft being tracked.

        a_lat = aircraft['lat']  # Degrees
        a_lon = aircraft['lon']  # Degrees
        a_alt = aircraft['alt_baro']  # Meters

        desired_pitch = distance.find_pitch(self.device_lat, self.device_lon, self.device_alt, a_lat, a_lon, a_alt)
        desired_yaw = distance.find_bearing(self.device_lat, self.device_lon, a_lat, a_lon)
        
        delta_pitch =  desired_pitch - self.current_pitch()
        delta_yaw = desired_yaw - self.current_yaw() 
        
        #print(f"Pitch: Current:{self.current_pitch():.1f} Desired:{desired_pitch:.1f}")
        #print(f"Yaw: Current:{self.current_yaw():.1f} Desired:{desired_yaw:.1f} Delta:{delta_yaw:.1f}")

        steps_pitch = abs(int(round(delta_pitch/STEP_DEGREES_PITCH)))
        steps_yaw = abs(int(round(delta_yaw/STEP_DEGREES_YAW)))

        direction_pitch = delta_pitch > 0
        direction_yaw = delta_yaw > 0

        self.pitch_motor.motor_go(clockwise=direction_pitch, steps=steps_pitch, stepdelay=STEPDELAY_FAST)
        self.yaw_motor.motor_go(clockwise=direction_yaw, steps=steps_yaw, stepdelay=STEPDELAY_FAST)
        
        
    # MQTT on_connect callback function
    def on_connect(self, client, userdata, flags, rc):
        print("rc code:", rc)
        client.subscribe(RPCrequestTopic)
        
    # MQTT on_message callback function
    def on_message(self, client, userdata, msg):        
        pass
    
    def connect(self):
        # Initialize variables and MQTT details
        iot_hub = "demo.thingsboard.io"
        port = 1883
        username = secret.key_thingsboard
        password = ""                
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.username_pw_set(username, password)
        self.client.connect(iot_hub, port)
        self.client.loop_start()
        print("Connection successful")
    
    def send_data(self, packet, aircraft):
        
        # Packet to be transmitted to the Thingsboard dashboard
        data_out = {"Packet": packet, # Current packet number
                    "HexID": aircraft['hex'], # Tracked aircraft hex ID
                    "Latitude": aircraft['lat'], # Tracked aircraft latitude
                    "Longitude": aircraft['lon'], # Tracked aircraft longitude
                    "Pitch": self.current_pitch(), # Device pitch
                    "Yaw": self.current_yaw(), # Device yaw
                    "Bearing": aircraft['bearing'], # Angle between the aircraft and the device, starting from north and going clockwise
            }
        
        # Not all aircraft use geometric altitude
        if 'alt_geom' in aircraft.keys():
            data_out['alt'] = aircraft['alt_geom']
        else:
            data_out['alt'] = aircraft['alt_baro']
        
        # Not all aircraft give a speed        
        if 'tas' in aircraft.keys():
            data_out['Speed'] = aircraft['tas']
        
        # Not all aircraft have registration(???)
        if 'r' in aircraft.keys():
            data_out['Registration'] = aircraft['r']
        
        # Perhaps not all aircraft will have their type given
        if 't' in aircraft.keys():
            data_out['Type'] = aircraft['t']

        print("data_out=",data_out)
        JSON_data_out = json.dumps(data_out) # Convert to JSON format
        self.client.publish(TelemetryTopic, JSON_data_out, 0) # Publish data to MQTT server
            
    def loop(self):
        i = 0
        while True:
            self.thingsboard_stuff()
            bearing_min = YAW_OFFSET
            bearing_max = YAW_OFFSET + self.yaw_span
            aircraft = adsb.near_selector_bearing(secret.device_lat, secret.device_lon, 50, bearing_min, bearing_max)
            if aircraft == None:
                print("No aircraft found.")
            else:
                self.point(aircraft)
                self.send_data(i, aircraft)
            i += 1
            time.sleep(1)
            print("=========")


if __name__ == "__main__":
    try:
        engine = Engine()
        engine.connect()
        engine.home()
        engine.loop()
    finally:
        GPIO.output((21, 20, 24, 23), GPIO.LOW)
        GPIO.cleanup()
        engine.client.disconnect()
        engine.client.loop_stop()
