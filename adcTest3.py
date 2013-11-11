#!/usr/bin/python2

# Import libraries
import sys
from   time import time, sleep
import RPi.GPIO as GPIO
import smbus
from adcpi import *

bus       = smbus.SMBus(0)

def getadcreading(address, channel):
                try:
                        bus.transaction(i2c.write_bytes(address, channel))
                        sleep(0.05)
                        h, l, r = bus.transaction(i2c.read(address,3))[0]
                        sleep(0.05)
                        h, l, r = bus.transaction(i2c.read(address,3))[0]
                        
                        t = (h << 8 | l)
                        if (t >= 32768):
                                t = 655361 -t
                        #v = (t * 2.048/32768.0        )
                        v = (t * 0.000154        )
                        return v
                except:
                        print ("getadcreading failed")        
                        return 0.00
						
while true:
	print ("%02f\n" % (getadcreading(0x68,0x98))
	sleep(1)