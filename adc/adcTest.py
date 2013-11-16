#!/usr/bin/python2

# adc tester

# Copyright (C) 2013  Simon Howroyd
# 
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
