import sys
import time
import RPi.GPIO as GPIO

# The following code is derived from: https://github.com/gavinlyonsrepo/RpiMotorLib/blob/master/RpiMotorLib/RpiMotorLib.py


class StopMotorInterrupt(Exception):
    """Stop the motor"""

    pass


class StepperDriver(object):
    """Derived from https://github.com/gavinlyonsrepo/RpiMotorLib/blob/master/RpiMotorLib/RpiMotorLib.py"""

    def __init__(self, direction_pin, step_pin):
        """class init method 3 inputs
        (1) direction type=int , help=GPIO pin connected to DIR pin of IC
        (2) step_pin type=int , help=GPIO pin connected to STEP of IC
        """
        self.direction_pin = direction_pin
        self.step_pin = step_pin

        self.stop_motor = False
        self.steps = 0

    def motor_stop(self):
        """Stop the motor"""
        self.stop_motor = True

    def motor_step(self, clockwise=False, stepdelay=0.005):
        """Stepper the motor forward a single step."""
        self.stop_motor = False
        GPIO.output(self.direction_pin, clockwise)

        time.sleep(stepdelay)
        GPIO.output(self.step_pin, True)
        time.sleep(stepdelay)
        GPIO.output(self.step_pin, False)
        time.sleep(stepdelay)

        if clockwise:
            self.steps += 1
        else:
            self.steps -= 1

    def motor_go(self, clockwise=False, steps=200, stepdelay=0.005, verbose=False, initdelay=0.05):
        """motor_go,  moves stepper motor based on 6 inputs

        (1) clockwise, type=bool default=False
        help="Turn stepper counterclockwise"
        (2) steps, type=int, default=200, help=Number of steps sequence's
        to execute. Default is one revolution , 200 in Full mode.
        (4) stepdelay, type=float, default=0.05, help=Time to wait
        (in seconds) between steps.
        (5) verbose, type=bool  type=bool default=False
        help="Write pin actions",
        (6) initdelay, type=float, default=1mS, help= Intial delay after
        GPIO pins initialized but before motor is moved.

        """
        self.stop_motor = False
        GPIO.output(self.direction_pin, clockwise)

        try:
            # dict resolution
            time.sleep(initdelay)

            for i in range(steps):
                if self.stop_motor:
                    raise StopMotorInterrupt
                else:
                    GPIO.output(self.step_pin, True)
                    time.sleep(stepdelay)
                    GPIO.output(self.step_pin, False)
                    time.sleep(stepdelay)

                    if clockwise:
                        self.steps += 1
                    else:
                        self.steps -= 1

                    if verbose:
                        print("Steps count {}".format(i + 1), end="\r", flush=True)

        except KeyboardInterrupt:
            print("User Keyboard Interrupt : RpiMotorLib:")
        except StopMotorInterrupt:
            print("Stop Motor Interrupt : RpiMotorLib: ")
        except Exception as motor_error:
            print(sys.exc_info()[0])
            print(motor_error)
            print("RpiMotorLib  : Unexpected error:")
        else:
            # print report status
            if verbose:
                print("\nRpiMotorLib, Motor Run finished, Details:.\n")
                print("Motor type = {}".format(self.motor_type))
                print("Clockwise = {}".format(clockwise))
                print("Number of steps = {}".format(steps))
                print("Step Delay = {}".format(stepdelay))
                print("Intial delay = {}".format(initdelay))
                print("Steps from func call = {i}")
