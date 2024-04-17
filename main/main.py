import RPi.GPIO as GPIO
from stepper import StepperDriver

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

MAX_STEPS_PITCH = int(1+90 / STEP_DEGREES)
MAX_STEPS_YAW = int(1+180 / STEP_DEGREES)


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

        # Find the limit, in steps, for each direction of each axis
        self.pitch_upper_limit = find_limit(motor=self.pitch_motor, limit_switch=PIN_PITCH_UPPER, clockwise=True, max_steps=MAX_STEPS_PITCH)
        self.pitch_lower_limit = find_limit(motor=self.pitch_motor, limit_switch=PIN_PITCH_LOWER, clockwise=False, max_steps=MAX_STEPS_PITCH)
        # The pitch axis should now be at 0 degrees (horizontal)

        self.yaw_left_limit = find_limit(motor=self.yaw_motor, limit_switch=PIN_YAW_RIGHT, clockwise=True, max_steps=MAX_STEPS_YAW)
        self.yaw_right_limit = find_limit(motor=self.yaw_motor, limit_switch=PIN_YAW_RIGHT, clockwise=False, max_steps=MAX_STEPS_YAW)

        # Move the yaw axis to 0 degrees


if __name__ == "__main__":
    try:
        engine = Engine()
        engine.home()
    except:
        GPIO.output((21, 20, 24, 23), GPIO.LOW)
        GPIO.cleanup()

    # armed = setup()

    # try:
    #     while engine.armed:
    #         loop()
    # except KeyboardInterrupt:
    #     GPIO.output(constants.ALL_PINS, GPIO.LOW)
    #     GPIO.cleanup()
