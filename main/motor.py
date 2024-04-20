import RPi.GPIO as GPIO
from RpiMotorLib import RpiMotorLib, StopMotorInterrupt
import time
import math


pitch_motor = RpiMotorLib.A4988Nema(consts.PIN_PITCH_DIR, consts.PIN_PITCH_STEP, (-1, -1, -1), "DRV8825")

yaw_motor = RpiMotorLib.A4988Nema(consts.PIN_YAW_DIR, consts.PIN_YAW_STEP, (-1, -1, -1), "DRV8825")


def pitch_step(motor, direction):
    motor.motor_go(direction,  # True=Clockwise, False=Counter-Clockwise
                   "Full",  # Step type (Full,Half,1/4,1/8,1/16,1/32)
                   1,  # number of steps
                   .0005,  # step delay [sec]
                   False,  # True = print verbose output
                   .0005)  # initial delay [sec]


# def RotateCameraPitch(deg):  # Rotates the camera the designated number of degrees
#     stepSize = 1.8  # Step size in degrees
#     numSteps = math.floor(deg/stepSize)
#     if deg > 0:
#         isClockwise = True
#     if deg < 0:
#         isClockwise = False
#     GPIO.output(PitchEN_Pin, GPIO.LOW)
#     PitchMotor.motor_go(isClockwise,  # True=Clockwise, False=Counter-Clockwise
#                         "Full",  # Step type (Full,Half,1/4,1/8,1/16,1/32)
#                         numSteps,  # number of steps
#                         .0005,  # step delay [sec]
#                         False,  # True = print verbose output
#                         .0005)  # initial delay [sec]


# def RotateCameraYaw(deg):  # Rotates the camera the designated number of degrees
#     stepSize = 1.8  # Step size in degrees
#     numSteps = math.floor(deg/stepSize)
#     if deg > 0:
#         isClockwise = True
#     if deg < 0:
#         isClockwise = False
#     GPIO.output(YawEN_Pin, GPIO.LOW)
#     YawMotor.motor_go(isClockwise,  # True=Clockwise, False=Counter-Clockwise
#                       "Full",  # Step type (Full,Half,1/4,1/8,1/16,1/32)
#                       numSteps,  # number of steps
#                       .0005,  # step delay [sec]
#                       False,  # True = print verbose output
#                       .0005)  # initial delay [sec]
