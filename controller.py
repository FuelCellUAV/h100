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
from   time      import time, sleep, asctime
import pifacedigitalio
import pifacecad
import RPi.GPIO  as GPIO
import smbus
import argparse
import math
from adcpi       import *
from tmp102      import *
from switch      import *
from h100Display import *

# Define default global constants
parser = argparse.ArgumentParser(description='Fuel Cell Controller by Simon Howroyd 2013')
parser.add_argument('--out'	   	,				help='Name of the output logfile')
parser.add_argument('--BLUE'       	,type=int, 	default=0x4a,	help='I2C address')
parser.add_argument('--EARTH'      	,type=int, 	default=0x49, 	help='I2C address')
parser.add_argument('--RED'        	,type=int, 	default=0x48, 	help='I2C address')
parser.add_argument('--YELLOW'     	,type=int, 	default=0x4b, 	help='I2C address')
parser.add_argument('--h2Pin'      	,type=float,	default=1,	help='H2 supply relay') # Relay
parser.add_argument('--fanPin'     	,type=float, 	default=0,    	help='Fan relay') 	# Relay
parser.add_argument('--purgePin'   	,type=float, 	default=2,    	help='Purge switch')
parser.add_argument('--buttonOn'   	,type=float, 	default=0,   	help='On button')
parser.add_argument('--buttonOff'  	,type=float, 	default=1,    	help='Off button')
parser.add_argument('--buttonReset'	,type=float, 	default=2,    	help='Reset button')
parser.add_argument('--purgeFreq'  	,type=float, 	default=18, 	help='How often to purge in seconds')
parser.add_argument('--purgeTime'  	,type=float, 	default=0.5,	help='How long to purge for in seconds')
parser.add_argument('--startTime'  	,type=float, 	default=4,	help='Duration of the startup routine')
parser.add_argument('--stopTime'   	,type=float, 	default=10,	help='Duration of the shutdown routine')
parser.add_argument('--cutoff'     	,type=float, 	default=26.0,	help='Temperature cutoff in celcius')
args = parser.parse_args()

# Class to save to file & print to screen
class MyWriter:
    def __init__(self, stdout, filename):
        self.stdout = stdout
        self.logfile = open(filename, 'a')
    def write(self, text):
        self.stdout.write(text)
        self.logfile.write(text)
    def close(self):
        self.stdout.close()
        self.logfile.close()
    def flush(self):
        self.stdout.flush()

# Look at user arguments
if args.out: # save to output file
    writer     = MyWriter(sys.stdout, args.out)
    sys.stdout = writer
	
BLUE 	       = args.BLUE
EARTH 	       = args.EARTH
RED 	       = args.RED
YELLOW 	       = args.YELLOW
h2Pin 	       = args.h2Pin
fanPin 	       = args.fanPin
purgePin       = args.purgePin
buttonOn       = args.buttonOn
buttonOff      = args.buttonOff
buttonReset    = args.buttonReset
purgeFreq      = args.purgeFreq
purgeTime      = args.purgeTime
startTime      = args.startTime
stopTime       = args.stopTime
cutoff 	       = args.cutoff

# State machine cases
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.iteritems())
    enums['reverse_mapping'] = reverse
    return type('Enum', (), enums)
STATE = enum(startup='startup', on='on', shutdown='shutdown', off='off', error='error')
state = STATE.off

# Define global constants
tmpBlue   = 0
tmpEarth  = 0
tmpRed    = 0
tmpYellow = 0
volts1    = 0
amps1     = 0
volts2    = 0
amps2     = 0
volts3    = 0
amps3     = 0
timeStart = time()

# Define class instances
#adcRes    = 12
#adcGain   = 2
bus       = smbus.SMBus(1)
#adc1	  = AdcPi2()
#adc2	  = AdcPi2()
#adc3	  = AdcPi2()
#adc4	  = AdcPi2()
#adc5	  = AdcPi2()
#adc6	  = AdcPi2()
purge     = Switch(purgePin)
h2        = Switch(h2Pin)
fan       = Switch(fanPin)
blue      = I2cTemp(bus,BLUE)
earth     = I2cTemp(bus,EARTH)
red       = I2cTemp(bus,RED)
yellow    = I2cTemp(bus,YELLOW)


#########
# Setup #
#########
pfio           = pifacedigitalio.PiFaceDigital() # Start piface
display        = FuelCellDisplay(1, "PF Display")
display.daemon = True # To ensure the process is killed on exit
display.start() # Turn the display on

adc            = AdcPi2Daemon()
adc.daemon     = True
adc.start()

print("\nFuel Cell Controller")
print("Horizon H-100 Stack")
print("(c) Simon Howroyd 2013")
print("Loughborough University\n")

print("controller  Copyright (C) 2013  Simon Howroyd")
print("This program comes with ABSOLUTELY NO WARRANTY; for details type `show w'.")
print("This is free software, and you are welcome to redistribute it,")
print("under certain conditions; type `show c' for details.\n")

print("%s\n" % asctime())

########
# Main #
########
while (True):
    print '\n',
    print time(),
    print '\t',
    #display.run()

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
    display.state(STATE.reverse_mapping[state])

    tmpBlue    = blue()
    tmpEarth   = earth()
    tmpRed     = red()
    tmpYellow  = yellow()
    amps1      = (abs(adc.val[0] * 1000 / 4.2882799485) + 0.6009) / 1.6046
    volts1     =  abs(adc.val[1] * 1000 / 60.9559671563)
    #amps1      = abs(adc.val[0] * 1000 / 63.69)
    #volts1     = abs(adc.val[1] * 1000 / 7.4)

    # STOP BUTTON
    if pfio.input_pins[buttonOn].value == False and pfio.input_pins[buttonOff].value == True:
        if state == STATE.startup or state == STATE.on:
            state = STATE.shutdown
            timeChange = time()
     
    # ELECTRIC
    print ("ADC\t"),
    print ("v1:%02f,\t" % (volts1)),
    print ("a1:%02f,\t" % (amps1)),
    #print ("v2:%02f,\t" % (volts2)),
    #print ("a2:%02f,\t" % (amps2)),
    #print ("v3:%02f,\t" % (volts3)),
    #print ("a3:%02f,\t" % (amps3)),
    if (volts1 >= 27.0 or volts1 < 12.0 or amps1 >= 10) and (time()-timeStart)>10:
            state = STATE.error
    display.voltage(volts1)
    display.current(amps1)
    

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
    display.temperature(tmpBlue)


    ## STATE MACHINE ##
    if state == STATE.off:
        # Off
        h2.switch(False)
        fan.switch(False)
        purge.switch(False)

        if pfio.input_pins[buttonOn].value == True and pfio.input_pins[buttonOff].value == False:
            state = STATE.startup
            timeChange = time()
            timeStart  = time()
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

#######
# End #
#######
