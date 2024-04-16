import RPi.GPIO as GPIO
import motor
from RpiMotorLib import RpiMotorLib, StopMotorInterrupt

# Motor driver  pins
PIN_PITCH_STEP = "GPIO21"
PIN_PITCH_DIR = "GPIO20"
PIN_YAW_STEP = "GPIO24"
PIN_YAW_DIR = "GPIO23"

# Limit switch pins
PIN_PITCH_UPPER = "GPIO22"
PIN_PITCH_LOWER = "GPIO27"
PIN_YAW_LEFT = "GPIO19"
PIN_YAW_RIGHT = "GPIO26"

ALL_PINS = [PIN_PITCH_STEP,
            PIN_PITCH_DIR,
            PIN_YAW_STEP,
            PIN_YAW_DIR,
            PIN_PITCH_UPPER,
            PIN_PITCH_LOWER,
            PIN_YAW_LEFT,
            PIN_YAW_RIGHT,]


class Engine():
    def __init__(self):

        GPIO.setup(PIN_PITCH_STEP, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(PIN_PITCH_DIR, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(PIN_YAW_STEP, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(PIN_YAW_DIR, GPIO.OUT, initial=GPIO.LOW)

        GPIO.setup(PIN_PITCH_UPPER, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(PIN_PITCH_LOWER, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(PIN_YAW_LEFT, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(PIN_YAW_RIGHT, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        GPIO.add_event_detect(PIN_PITCH_UPPER, GPIO.RISING, callback=self.limit_switch_interrupt, bouncetime=50)
        GPIO.add_event_detect(PIN_PITCH_LOWER, GPIO.RISING, callback=self.limit_switch_interrupt, bouncetime=50)
        GPIO.add_event_detect(PIN_YAW_LEFT, GPIO.RISING, callback=self.limit_switch_interrupt, bouncetime=50)
        GPIO.add_event_detect(PIN_YAW_RIGHT, GPIO.RISING, callback=self.limit_switch_interrupt, bouncetime=50)

        self.motor_pitch = RpiMotorLib.A4988Nema(PIN_PITCH_DIR, PIN_PITCH_STEP, (-1, -1, -1), "DRV8825")
        self.motor_yaw = RpiMotorLib.A4988Nema(PIN_YAW_DIR, PIN_YAW_STEP, (-1, -1, -1), "DRV8825")

    def home(self):

        motor.motor_go(True,  # True=Clockwise, False=Counter-Clockwise
                       "Full",  # Step type (Full,Half,1/4,1/8,1/16,1/32)
                       200,  # number of steps
                       .0005,  # step delay [sec]
                       False,  # True = print verbose output
                       .0005)  # initial delay [sec]

        # test code

    def limit_switch_interrupt():
        if GPIO.input(PIN_PITCH_UPPER):
            raise StopMotorInterrupt
        if GPIO.input(PIN_PITCH_LOWER):
            raise StopMotorInterrupt
        if GPIO.input(PIN_YAW_LEFT):
            raise StopMotorInterrupt
        if GPIO.input(PIN_YAW_RIGHT):
            raise StopMotorInterrupt


if __name__ == "__main__":
    try:
        engine = Engine()
        engine.home()
    except KeyboardInterrupt:
        GPIO.output(ALL_PINS, GPIO.LOW)
        GPIO.cleanup()

    # armed = setup()

    # try:
    #     while engine.armed:
    #         loop()
    # except KeyboardInterrupt:
    #     GPIO.output(constants.ALL_PINS, GPIO.LOW)
    #     GPIO.cleanup()
