#!/usr/bin/python2

# Import libraries
import sys
from   time import time
import RPi.GPIO as GPIO
import smbus
from adcpi import *

# Define class instances
adcRes    = 12
adcGain   = 2
bus       = smbus.SMBus(0)
adc1      = AdcPiV1(bus,1,adcRes,adcGain,1)
adc2      = AdcPiV1(bus,2,adcRes,adcGain,1)
adc3      = AdcPiV1(bus,3,adcRes,adcGain,1)
adc4      = AdcPiV1(bus,4,adcRes,adcGain,1)
adc5      = AdcPiV1(bus,5,adcRes,adcGain,1)
adc6      = AdcPiV1(bus,6,adcRes,adcGain,1)
adc7      = AdcPiV1(bus,7,adcRes,adcGain,1)
adc8      = AdcPiV1(bus,8,adcRes,adcGain,1)


# Setup
print("\nADC Tester")
print("(c) Simon Howroyd 2013")
print("Loughborough University\n")

# Main
while (True):
    print "\n"
    print ("1:%02f,\t" % (adc1.get())),
    print ("2:%02f,\t" % (adc2.get())),
    print ("3:%02f,\t" % (adc3.get())),
    print ("4:%02f,\t" % (adc4.get())),
    print ("5:%02f,\t" % (adc5.get())),
    print ("6:%02f,\t" % (adc6.get())),
    print ("7:%02f,\t" % (adc7.get())),
    print ("8:%02f,\t" % (adc8.get())),
