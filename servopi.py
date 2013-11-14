#!/usr/bin/python2
# A class to use PWM on the raspberryPi
# Written by Simon Howroyd

import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(12, GPIO.OUT)

# Class to use RC servos
class PwmPi:
	frequency = 50
	channel = 12
	p = GPIO.PWM(channel, frequency)
	dutyMin = 5
	dutyMax = 10
	
	multiAngle = 5/180
	multiPercentage = 5/100
	multiMicroseconds = 5/1
	
	def __init__(self):
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(channel, GPIO.OUT)
		
		p.start(dutyMin)

	def setMicroseconds(self, millis):
		try:
		except Exception as e:
			print("Failed to set PWM")
			
	def setPercentage(self, percent):
		try:
		except Exception as e:
			print("Failed to set PWM")
			
	def setAngle(self, angle):
		try:
		except Exception as e:
			print("Failed to set PWM")