#!/usr/bin/python

# Fuel Cell Controller for the Horizon H100

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

# Define Paths
import sys
sys.path.append('/home/pi/h100/adc')
sys.path.append('/home/pi/h100/switch')

# Import libraries
from   time import time
#import piface.pfio as pfio
#import pifacecommon as pfcom
import pifacedigitalio
import RPi.GPIO as GPIO
import smbus
import argparse
#import adcpi
from adcpi2  import *
from tmp102 import *
from switch import *

# Define default global constants
parser = argparse.ArgumentParser(description='Fuel Cell Controller by Simon Howroyd 2013')
parser.add_argument('--out'	   		,								help='Name of the output logfile')
parser.add_argument('--BLUE'       	,type=int, 		default=0x4a,	help='I2C address')
parser.add_argument('--EARTH'      	,type=int, 		default=0x49, 	help='I2C address')
parser.add_argument('--RED'        	,type=int, 		default=0x48, 	help='I2C address')
parser.add_argument('--YELLOW'     	,type=int, 		default=0x4b, 	help='I2C address')
parser.add_argument('--h2Pin'      	,type=float,	default=0,		help='H2 supply relay') # Relay
parser.add_argument('--fanPin'     	,type=float, 	default=1,    	help='Fan relay') 	# Relay
parser.add_argument('--purgePin'   	,type=float, 	default=2,    	help='Purge switch')
parser.add_argument('--buttonOn'   	,type=float, 	default=0,   	help='On button')
parser.add_argument('--buttonOff'  	,type=float, 	default=1,    	help='Off button')
parser.add_argument('--buttonReset'	,type=float, 	default=2,    	help='Reset button')
parser.add_argument('--purgeFreq'  	,type=float, 	default=30, 	help='How often to purge in seconds')
parser.add_argument('--purgeTime'  	,type=float, 	default=0.5,	help='How long to purge for in seconds')
parser.add_argument('--startTime'  	,type=float, 	default=2,		help='Duration of the startup routine')
parser.add_argument('--stopTime'   	,type=float, 	default=10,		help='Duration of the shutdown routine')
parser.add_argument('--cutoff'     	,type=float, 	default=31.0,	help='Temperature cutoff in celcius')
args = parser.parse_args()

# Class to save to file & print to screen
class MyWriter:
    def __init__(self, stdout, filename):
        self.stdout = stdout
        self.logfile = file(filename, 'a')
    def write(self, text):
        self.stdout.write(text)
        self.logfile.write(text)
    def close(self):
        self.stdout.close()
        self.logfile.close()

# Look at user arguments
if args.out: # save to output file
    writer     = MyWriter(sys.stdout, args.out)
    sys.stdout = writer
	
BLUE 	    = args.BLUE
EARTH 	    = args.EARTH
RED 	    = args.RED
YELLOW 	    = args.YELLOW
h2Pin 	    = args.h2Pin
fanPin 	    = args.fanPin
purgePin    = args.purgePin
buttonOn    = args.buttonOn
buttonOff   = args.buttonOff
buttonReset = args.buttonReset
purgeFreq   = args.purgeFreq
purgeTime   = args.purgeTime
startTime   = args.startTime
stopTime    = args.stopTime
cutoff 	    = args.cutoff

# State machine cases
class STATE:
	startup, on, shutdown, off, error = range(5)
state = STATE.off

# Define global constants
tmpBlue    = 0
tmpEarth   = 0
tmpRed     = 0
tmpYellow  = 0
volts1     = 0
amps1      = 0
volts2     = 0
amps2      = 0
volts3     = 0
amps3      = 0

# Define class instances
adcRes    = 12
adcGain   = 2
bus       = smbus.SMBus(0)
adc1	  = AdcPiV1(bus,1,adcRes,adcGain,(1000/63.69))
adc2	  = AdcPiV1(bus,2,adcRes,adcGain,(1000/36.60))
adc3	  = AdcPiV1(bus,3,adcRes,adcGain,(1000/63.69))
adc4	  = AdcPiV1(bus,4,adcRes,adcGain,(1000/36.60))
adc5	  = AdcPiV1(bus,5,adcRes,adcGain,(1000/63.69))
adc6	  = AdcPiV1(bus,6,adcRes,adcGain,(1000/36.60))
purge     = Switch(purgePin)
h2        = Switch(h2Pin)
fan       = Switch(fanPin)
blue      = I2cTemp(bus,BLUE)
earth     = I2cTemp(bus,EARTH)
red       = I2cTemp(bus,RED)
yellow    = I2cTemp(bus,YELLOW)

# Setup
pfio = pifacedigitalio.PiFaceDigital() # Start piface
print("\nFuel Cell Controller")
print("Horizon H-100 Stack")
print("(c) Simon Howroyd 2013")
print("Loughborough University\n")

print("controller  Copyright (C) 2013  Simon Howroyd")
print("This program comes with ABSOLUTELY NO WARRANTY; for details type `show w'.")
print("This is free software, and you are welcome to redistribute it,")
print("under certain conditions; type `show c' for details.")

# Main
while (True):
    print ("\n")

    # STATE
    if state == STATE.off:
        print ("OFF  :\t"),
    elif state == STATE.startup:
        print ("START:\t"),
    elif state == STATE.on:
        print ("ON   :\t"),
    elif state == STATE.shutdown:
        print ("STOP :\t"),
    elif state == STATE.error:
        print ("ERROR:\t"),

    tmpBlue    = blue()
    tmpEarth   = earth()
    tmpRed     = red()
    tmpYellow  = yellow()
    volts1     = adc1.get()
    amps1      = adc2.get()
    volts2     = adc3.get()
    amps2      = adc4.get()
    volts3     = adc5.get()
    amps3      = adc6.get()

    # STOP BUTTON
    if pfio.input_pins[buttonOn].value == False and pfio.input_pins[buttonOff].value == True:
        if state == STATE.startup or state == STATE.on:
            state = STATE.shutdown
            timeChange = time()
     
    # ELECTRIC
    print ("ADC\t"),
    print ("v1:%02f,\t" % (volts1)),
    print ("a1:%02f,\t" % (amps1)),
    print ("v2:%02f,\t" % (volts2)),
    print ("a2:%02f,\t" % (amps2)),
    print ("v3:%02f,\t" % (volts3)),
    print ("a3:%02f,\t" % (amps3)),

    # TEMPERATURE
    print ("TMP\t"), 
    print ("tB:%02f,\t" % (tmpBlue)),
    print ("tE:%02f,\t" % (tmpEarth)),
    print ("tR:%02f,\t" % (tmpRed)),
    print ("tY:%02f,\t" % (tmpYellow)),
    if tmpBlue >= cutoff or tmpEarth >= cutoff or tmpRed >= cutoff or tmpYellow >= cutoff:
        print ("HOT"),
        state = STATE.error
    else:
        print ("OK!"),

    ## STATE MACHINE ##
    if state == STATE.off:
        # Off
        h2.switch(False)
        fan.switch(False)
        purge.switch(False)

        if pfio.input_pins[buttonOn].value == True and pfio.input_pins[buttonOff].value == False:
            state = STATE.startup
            timeChange = time()
    if state == STATE.startup:
        # Startup
        try:
            h2.timed(0,startTime)
            fan.timed(0,startTime)
            purge.timed(0,startTime)
            if (time() - timeChange) > startTime:
                state = STATE.on
        except Exception as e:
            #print ("Startup Error")
            state = STATE.error
    if state == STATE.on:
        # Running
        try:
            h2.switch(True)
            fan.switch(True)
            purge.timed(purgeFreq,purgeTime)
        except Exception as e:
            #print ("Running Error")
            state = STATE.error
    if state == STATE.shutdown:
        # Shutdown
        try:
            h2.switch(False)
            fan.timed(0,stopTime)
            purge.timed(0,stopTime)
            if (time() - timeChange) > stopTime:
                state = STATE.off
        except Exception as e:
            #print ("Shutdown Error")
            state = STATE.error
    if state == STATE.error:
        # Error lock           
        h2.switch(False)
        purge.switch(False)
        if blue() >= cutoff or earth() >= cutoff or red() >= cutoff or yellow() >= cutoff:
            fan.switch(True)
        else:
            fan.switch(False)
            # Reset button
            if pfio.input_pins[buttonReset].value == True:
                state = STATE.off
                #print("\nResetting")

    ## end STATE MACHINE ##

# end main

