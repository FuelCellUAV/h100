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

from __future__ import print_function

# Define Paths
import sys
sys.path.append('/home/pi/h100/adc')
sys.path.append('/home/pi/h100/switch')
sys.path.append('/home/pi/h100/display')
sys.path.append('/home/pi/h100/temperature')

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
parser.add_argument('--out'	   			,		help='Name of the output logfile')
parser.add_argument('--controller'  	,type=int, 	default=1, 	help='Set to 0 for controller off')
parser.add_argument('--purgeController' ,type=int, 	default=0, 	help='Set to 1 for purge controller on')
parser.add_argument('--purgeTime'  	,type=float, 	default=0.5,	help='How long to purge for in seconds')
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
	
BLUE 	       = 0x4a
EARTH 	       = 0x49
RED 	       = 0x48
YELLOW 	       = 0x4b
fanPin 	       = 0
h2Pin 	       = 1
purgePin       = 2
buttonOn       = 0
buttonOff      = 1
buttonReset    = 2
purgeFreq      = 0
purgeTime      = args.purgeTime
startTime      = 4
stopTime       = 10
cutoff 	       = args.cutoff
purgeController = args.purgeController
controller     = args.controller

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
volts     = [0,0,0]
amps      = [0,0,0]
timeStart = time()

# Define class instances
bus       = smbus.SMBus(1)
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
try:
	while (True):
		print('\n', time(), end='\t'),

		# PRINT STATE
		if state == STATE.off:
			print('OFF', end='\t')
		elif state == STATE.startup:
			print('STA', end='\t')
		elif state == STATE.on:
			print('ON', end='\t')
		elif state == STATE.shutdown:
			print('STO', end='\t')
		elif state == STATE.error:
			print('ERR', end='\t')
		display.state(STATE.reverse_mapping[state])
		# end

		# STOP BUTTON
		if (pfio.input_pins[buttonOn].value == False) and (pfio.input_pins[buttonOff].value == True):
			if state == STATE.startup or state == STATE.on:
				state = STATE.shutdown
				timeChange = time()
		
		# ELECTRIC
		amps[0]    = (abs(adc.val[0] * 1000 / 4.2882799485) + 0.6009) / 1.6046
		volts[0]   = (abs(adc.val[1] * 1000 / 60.9559671563))
		print('v1', '\t', '%02f' % volts[0], end='\t')
		print('a1', '\t', '%02f' % amps[0], end='\t')
		display.voltage(volts[0])
		display.current(amps[0])

		# TEMPERATURE
		tmpBlue    = blue()
		tmpEarth   = earth()
		tmpRed     = red()
		tmpYellow  = yellow() 
		print('tB', '\t', '%02f' % tmpBlue,   end='\t')
		print('tE', '\t', '%02f' % tmpEarth,  end='\t')
		print('tR', '\t', '%02f' % tmpRed,    end='\t')
		print('tY', '\t', '%02f' % tmpYellow, end='\t')
		if (tmpBlue >= cutoff) or (tmpEarth >= cutoff) or (tmpRed >= cutoff) or (tmpYellow >= cutoff):
			print('HOT', end='\t')
			state = STATE.error
		else:
			print('OK', end='\t')
		display.temperature(max(tmpBlue, tmpEarth, tmpRed, tmpYellow))
		
		# PURGE CALCULATOR
		if purgeController is 1:
			purgeFreq = -1.8*amps[0] + 30		
			clamp = lambda n, minn, maxn: max(min(maxn, n), minn)
			purgeFreq = clamp(purgeFreq, 10, 30)
		else:
			purgeFreq = 30
		print('PF', '\t', '%.1f' % purgeFreq, end='\t')
		
		# FUEL CELL CONTROLLER
		if controller is 1:
			#######
			# OFF #
			#######
			if state == STATE.off:	
				h2.switch(False)
				fan.switch(False)
				purge.switch(False)

				if pfio.input_pins[buttonOn].value == True and pfio.input_pins[buttonOff].value == False:
					state = STATE.startup
					timeChange = time()
					timeStart  = time()
			#######
			# STA #
			#######
			if state == STATE.startup:
				h2.timed(0, startTime)
				fan.timed(0, startTime)
				purge.timed(0, startTime)
				
				if (time() - timeChange) > startTime:
					state = STATE.on
			#######
			# ON  #
			#######
			if state == STATE.on:
				h2.switch(True)
				fan.switch(True)
				purge.timed(purgeFreq, purgeTime)
				
				# Voltage error handling
				if (volts[0] < 10.5) and (time()-timeStart)>10:
					state = STATE.error
				if (volts[0] >= 27.0) or (volts[0] < 10.0):
					state = STATE.error
			#######
			# SHU #
			#######
			if state == STATE.shutdown:
				h2.switch(False)
				fan.timed(0, stopTime)
				purge.timed(0, stopTime)
				
				if (time() - timeChange) > stopTime:
					state = STATE.off
			#######
			# ERR #
			####### 
			if state == STATE.error:         
				h2.switch(False)
				purge.switch(False)
				
				if (blue() >= cutoff) or (earth() >= cutoff) or (red() >= cutoff) or (yellow() >= cutoff):
					fan.switch(True)
				else:
					fan.switch(False)
					# Reset button
					if pfio.input_pins[buttonReset].value == True:
						state = STATE.off
		## end STATE MACHINE ##
			
# Programme Exit Code
except (KeyboardInterrupt, SystemExit):
    sys.exit(1)
finally:
    h2.switch(False)
    purge.switch(False)
    fan.switch(False)
    adc.stop()
    display.stop()
    del purge, h2, fan, blue, earth, red, yellow, bus
    print('\n\n\nProgramme successfully exited and closed down\n\n')
#######
# End #
#######
