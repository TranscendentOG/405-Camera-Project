import time
import RPi.GPIO as GPIO
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

STEPDELAY_FAST = 0.05
STEPDELAY_SLOW = 0.01

STEP_DEGREES = 1.8  # 1.8 degrees per step for full stepping

# Tuning offset for each axis. Adjust if the home angle does not correspond to the measured angle
PITCH_OFFSET = 1.8
YAW_OFFSET = 270


def assert_msg(condition, message):
    """Raises a RuntimeError with message if condition is false"""
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

    def current_pitch(self):
        return (self.pitch_motor.steps - self.pitch_lower_limit)*STEP_DEGREES + PITCH_OFFSET

    def current_yaw(self):
        return (self.yaw_motor.steps - self.yaw_left_limit)*STEP_DEGREES + YAW_OFFSET

    def home(self):
        def find_limit(motor, limit_switch, clockwise, max_steps):
            """Returns the position of the limit, in steps, for a given motor and limit switch.

            motor is the motor object.
            Limit_switch_pin is the pin that the limit switch will pull high.
            max_steps is the maximum number of steps this axis should be able to move.

            Returns the step before the limit switch is triggered.

            Derived in part from https://github.com/gavinlyonsrepo/RpiMotorLib/blob/master/RpiMotorLib/RpiMotorLib.py"""

            # Look for a rising edge on the limit switch
            GPIO.add_event_detect(limit_switch, GPIO.rising)

            # Approach the limit switch, and stop when it is triggered.
            for i in range(max_steps):
                triggered = GPIO.event_detected(limit_switch)
                if not triggered:
                    motor.motor_step(clockwise=clockwise, stepdelay=STEPDELAY_FAST)
                else:
                    break

            # Remove the event detection before the function can return
            GPIO.remove_event_detect(limit_switch)

            # End the function call if the limit switch was not found
            if not triggered:
                return None

            # Now look for a falling edge
            GPIO.add_event_detect(limit_switch, GPIO.falling)

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
        max_steps_pitch = int(110 / STEP_DEGREES)
        max_steps_yaw = int(220 / STEP_DEGREES)

        # Find the limits, in steps, for the pitch axis
        #self.pitch_upper_limit = find_limit(motor=self.pitch_motor, limit_switch=PIN_PITCH_UPPER, clockwise=True, max_steps=max_steps_pitch)
        #assert_msg(self.pitch_upper_limit!=None,'Failed to find pitch upper limit')
        #self.pitch_lower_limit = find_limit(motor=self.pitch_motor, limit_switch=PIN_PITCH_LOWER, clockwise=False, max_steps=max_steps_pitch)
        #assert_msg(self.pitch_lower_limit!=None,'Failed to find pitch lower limit')
        # The pitch axis should now be at home

        # Record the total travel possible on the pitch axis
        #self.pitch_axis_degrees = (self.pitch_upper_limit - self.pitch_lower_limit)*STEP_DEGREES

        # # Find the limits, in steps, for the yaw axis
        self.yaw_left_limit = find_limit(motor=self.yaw_motor, limit_switch=PIN_YAW_RIGHT, clockwise=True, max_steps=max_steps_yaw)
        assert_msg(self.yaw_left_limit != None, 'Failed to find yaw left limit')
        self.yaw_right_limit = find_limit(motor=self.yaw_motor, limit_switch=PIN_YAW_LEFT, clockwise=False, max_steps=max_steps_yaw)
        assert_msg(self.yaw_right_limit != None, 'Failed to find yaw right limit')

        # # Record the total travel possible on the yaw axis
        # self.yaw_axis_degrees = (self.yaw_left_limit - self.yaw_right_limit)*STEP_DEGREES

        # # Move the yaw axis to the center of the axis
        # steps = int(self.yaw_axis_degrees/(2*STEP_DEGREES))
        # self.yaw_motor.motor_go(clockwise=True, steps=steps)

        # Setup interrupts to stop the device if the limit switches are triggered again
        GPIO.add_event_detect(PIN_PITCH_UPPER, GPIO.RISING, callback=RuntimeError, bouncetime=50)
        GPIO.add_event_detect(PIN_PITCH_LOWER, GPIO.RISING, callback=RuntimeError, bouncetime=50)
        GPIO.add_event_detect(PIN_YAW_LEFT, GPIO.RISING, callback=RuntimeError, bouncetime=50)
        GPIO.add_event_detect(PIN_YAW_RIGHT, GPIO.RISING, callback=RuntimeError, bouncetime=50)

    def thingsboard_stuff(self):
        # Update thingsboard info and check if any buttons have been pressed
        pass

    def point(self, aircraft):
        # Point the camera at the current aircraft being tracked.

        a_lat = aircraft['lat']  # Degrees
        a_lon = aircraft['lon']  # Degrees
        a_alt = aircraft['alt_baro']  # Meters

        desired_pitch = distance.find_pitch(self.device_lat, self.device_lon, self.device_alt, a_lat, a_lon, a_alt)

        print(f"Pitch: Current:{self.current_pitch()} Desired:{round(desired_pitch,2)}")

        delta_pitch = desired_pitch - self.current_pitch()

        steps = abs(int(delta_pitch/1.8))

        direction = delta_pitch > 0

        self.pitch_motor.motor_go(clockwise=direction, steps=steps, stepdelay=STEPDELAY_FAST)

        # TODO: the same thing again but for the yaw axis, taking into account which direction the device is pointed

    def debugprint(self, aircraft):
        try:
            print(f"Flight:{aircraft['flight']}")
        except KeyError:
            print(f"Flight:None")
        print(f"alt_baro:{aircraft['alt_baro']} lat-lon:{aircraft['lat']}-{aircraft['lon']}")

    def loop(self):
        while True:
            self.thingsboard_stuff()
            aircraft = adsb.near_selector(secret.device_lat, secret.device_lon, 25)
            self.debugprint(aircraft)
            self.point(aircraft)
            time.sleep(0.1)


if __name__ == "__main__":
    try:
        engine = Engine()
        engine.home()
        engine.loop()
    except AssertionError:
        print("Assertion failed.")
    finally:
        # TODO cleanup thingsboard connection
        GPIO.output((21, 20, 24, 23), GPIO.LOW)
        GPIO.cleanup()
