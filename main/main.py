import time
import RPi.GPIO as GPIO
from stepper import StepperDriver
import secrets
import distance


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

STEPDELAY_FAST = 0.0005
STEPDELAY_MED = 0.005
STEPDELAY_SLOW = 0.01

STEP_DEGREES = 1.8  # 1.8 degrees per step for full stepping


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

        # GPIO.add_event_detect(PIN_PITCH_UPPER, GPIO.RISING, callback=self.limit_switch_interrupt, bouncetime=50)
        # GPIO.add_event_detect(PIN_PITCH_LOWER, GPIO.RISING, callback=self.limit_switch_interrupt, bouncetime=50)
        # GPIO.add_event_detect(PIN_YAW_LEFT, GPIO.RISING, callback=self.limit_switch_interrupt, bouncetime=50)
        # GPIO.add_event_detect(PIN_YAW_RIGHT, GPIO.RISING, callback=self.limit_switch_interrupt, bouncetime=50)

        self.pitch_motor = StepperDriver(PIN_PITCH_DIR, PIN_PITCH_STEP)
        self.yaw_motor = StepperDriver(PIN_YAW_DIR, PIN_YAW_STEP)

        # Position of each limit in steps
        self.pitch_upper_limit = None
        self.pitch_lower_limit = None
        self.yaw_left_limit = None
        self.yaw_right_limit = None

        self.pitch_axis_degrees = None
        self.yaw_axis_degrees = None

        self.device_lat = secrets.device_lat  # Degrees, latitude of the device
        self.device_long = secrets.device_lon  # Degrees, longitude of the device
        self.device_alt = secrets.device_alt  # meters, height of the device above sea level, https://en-us.topographic-map.com/

    def current_pitch(self):
        return (self.pitch_motor.steps - self.pitch_lower_limit)*STEP_DEGREES

    def current_yaw(self):
        return (self.yaw_motor.steps - self.yaw_left_limit)*STEP_DEGREES

    def ac_position(self):
        # TODO
        a_lat, a_lon, a_alt = None, None, None
        return a_lat, a_lon, a_alt

    def home(self):
        def find_limit(motor, limit_switch, clockwise, max_steps):
            """Returns the position of the limit, in steps, for a given motor and limit switch.

            motor is the motor object.
            Limit_switch_pin is the pin that the limit switch will pull high.
            max_steps is the maximum number of steps this axis should be able to move.

            Returns the step before the limit switch is triggered.

            Derived in part from https://github.com/gavinlyonsrepo/RpiMotorLib/blob/master/RpiMotorLib/RpiMotorLib.py"""

            # Approach the limit switch, and stop when it is triggered.
            triggered = False
            for i in range(max_steps):
                triggered = GPIO.input(limit_switch)
                if not triggered:
                    motor.motor_step(clockwise=clockwise, stepdelay=STEPDELAY_MED)
                else:
                    break

            # Raise an error if the previous loop never triggered the limit switch
            assert triggered

            limit = None

            # Slowly move away from the limit switch until it is no longer triggered.
            # The step when it is no longer triggered is the limit.
            for i in range(max_steps):
                triggered = GPIO.input(limit_switch)
                if triggered:
                    motor.motor_step(clockwise=not clockwise, stepdelay=STEPDELAY_SLOW)
                else:
                    limit = motor.steps
                    break

            # If the limit was never found, raise an error.
            assert limit != None

            return limit

        # Guesses, not reliable numbers
        max_steps_pitch = int(100 / STEP_DEGREES)
        max_steps_yaw = int(200 / STEP_DEGREES)

        # Find the limits, in steps, for the pitch axis
        self.pitch_upper_limit = find_limit(motor=self.pitch_motor, limit_switch=PIN_PITCH_UPPER, clockwise=True, max_steps=max_steps_pitch)
        self.pitch_lower_limit = find_limit(motor=self.pitch_motor, limit_switch=PIN_PITCH_LOWER, clockwise=False, max_steps=max_steps_pitch)
        # The pitch axis should now be at 0 degrees (horizontal)

        # Record the total travel possible on the pitch axis
        self.pitch_axis_degrees = (self.pitch_upper_limit - self.pitch_lower_limit)*STEP_DEGREES

        # # Find the limits, in steps, for the yaw axis
        # self.yaw_left_limit = find_limit(motor=self.yaw_motor, limit_switch=PIN_YAW_RIGHT, clockwise=True, max_steps=max_steps_yaw)
        # self.yaw_right_limit = find_limit(motor=self.yaw_motor, limit_switch=PIN_YAW_RIGHT, clockwise=False, max_steps=max_steps_yaw)

        # # Record the total travel possible on the yaw axis
        # self.yaw_axis_degrees = (self.yaw_left_limit - self.yaw_right_limit)*STEP_DEGREES

        # # Move the yaw axis to the center of the axis
        # steps = int(self.yaw_axis_degrees/(2*STEP_DEGREES))
        # self.yaw_motor.motor_go(clockwise=True, steps=steps)

    def thingsboard_stuff(self):
        # Update thingsboard info and check if any buttons have been pressed
        pass

    def point(self, camera):
        # Point the camera at the current being tracked aircraft.

        a_lat, a_lon, a_alt = self.ac_position()

        desired_pitch = distance.find_pitch(self.device_lat, self.device_lon, self.device_alt, a_lat, a_lon, a_alt)

        delta_pitch = desired_pitch - self.current_pitch()

        new_pitch = delta_pitch + self.current_pitch()

        # Stop the program if this would move the stepper farther than it can move
        assert new_pitch < self.pitch_axis_degrees
        assert 0 < new_pitch

        steps = abs(int(delta_pitch/1.8))

        direction = delta_pitch > 0

        self.pitch_motor.motor_go(direction=direction, steps=steps, stepdelay=STEPDELAY_FAST)

        # TODO: the same thing again but for the yaw axis, taking into account which direction the device is pointed

    def loop(self):
        armed = True
        while armed:
            self.thingsboard_stuff()
            self.point()
            time.sleep(0.05)


if __name__ == "__main__":
    try:
        engine = Engine()
        engine.home()
        # engine.loop()
    except AssertionError:
        print("Assertion failed.")
    finally:
        GPIO.output((21, 20, 24, 23), GPIO.LOW)
        GPIO.cleanup()
