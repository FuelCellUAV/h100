#!/usr/bin/python3

# Fuel Cell Controller for the Horizon H100

# Copyright (C) 2014  Simon Howroyd
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

#from __future__ import print_function

# Define Paths
import sys
sys.path.append('./adc')
sys.path.append('./switch')
sys.path.append('./display')
sys.path.append('./temperature')
sys.path.append('./purge')

# Import libraries
<<<<<<< HEAD
import multiprocessing
import time
import pifacedigitalio
import pifacecad
import smbus
import math
from   adcpi       import *
from   tmp102      import *
from   switch      import *
from   h100Display import *
from   enum        import *
	
class Controller():
    BLUE 	       = 0x4A
    EARTH 	       = 0x49
    RED 	       = 0x48
    YELLOW 	       = 0x4B
    h2Pin 	       = 1
    fanPin 	       = 2
    purgePin       = 0
    buttonOn       = 0
    buttonOff      = 1
    buttonReset    = 2
    purgeFreq      = 30
    purgeTime      = 0.5
    startTime      = 5
    stopTime       = 10
    cutoff 	       = 31.0

	#########
    # Setup #
    #########
    def __init__(self, filename = None):
	    # Open logfile if required
        if (filename == None):
            pass
        else:
            self.log = open(filename, 'a')
        
		# Define class instances
        self.bus       = smbus.SMBus(1)
        self.purge     = Switch(purgePin)
        self.h2        = Switch(h2Pin)
        self.fan       = Switch(fanPin)
        self.blue      = I2cTemp(bus,BLUE)
        self.earth     = I2cTemp(bus,EARTH)
        self.red       = I2cTemp(bus,RED)
        self.yellow    = I2cTemp(bus,YELLOW)
		
		# Define state machine
	    self.STATE = enum(startup='startup', on='on', shutdown='shutdown', off='off', error='error')
        self.state = self.STATE.off
        
		# Initiate multiprocessing thread
        multiprocessing.Process.__init__(self)
        self.threadId = 1
        self.Name = 'Controller'
        
		# Initiate external modules
        self.pfio           = pifacedigitalio.PiFaceDigital()  # Start PiFace IO
        self.display        = FuelCellDisplay(1, "PF Display") # Start PiFace Display
        self.adc            = AdcPi2Daemon() # Start ADC

		# Start external modules
        self.display.daemon = True # To ensure the process is killed on exit
        self.display.start()       # Turn the display on
        self.adc.daemon     = True
        self.adc.start()           # Turn on the ADC
		
		# Write some test to the logfile
        if 'log' in locals():
            self.log.write("\nFuel Cell Controller")
            self.log.write("Horizon H-100 Stack")
            self.log.write("(c) Simon Howroyd 2013")
            self.log.write("Loughborough University\n")
            
            self.log.write("controller  Copyright (C) 2013  Simon Howroyd")
            self.log.write("This program comes with ABSOLUTELY NO WARRANTY; for details type `show w'.")
            self.log.write("This is free software, and you are welcome to redistribute it,")
            self.log.write("under certain conditions; type `show c' for details.")
        else:
            pass

    ########
    # Main #
    ########
    def run(self):
        self.log.write("\n")

        # STATE
        if self.state == self.STATE.off:
            self.log.write("OFF  :\t"),
        elif self.state == self.STATE.startup:
            self.log.write("START:\t"),
        elif self.state == self.STATE.on:
            self.log.write("ON   :\t"),
        elif self.state == self.STATE.shutdown:
            self.log.write("STOP :\t"),
        elif self.state == self.STATE.error:
            self.log.write("ERROR:\t"),
        self.display.state(self.STATE.reverse_mapping[self.state])
    
        tmpBlue    = self.blue()
        tmpEarth   = self.earth()
        tmpRed     = self.red()
        tmpYellow  = self.yellow()
        volts1     = abs(self.adc.val[0] * 1000 / 63.69)
        amps1      = abs(self.adc.val[1] * 1000 / 7.4)
        #volts1     = abs(adc1.get(0x68,0x9C))*1000/63.69
        #amps1      = abs(adc2.get(0x68,0xBC))*1000/7.4
        #volts2     = abs(adc3.get(0x68,0xDC))
        #amps2      = abs(adc4.get(0x68,0xFC))
        #volts3     = abs(adc5.get())
        #amps3      = abs(adc6.get())

        # STOP BUTTON
        if self.pfio.input_pins[self.buttonOn].value == False
		        and self.pfio.input_pins[self.buttonOff].value == True:
            if self.state == self.STATE.startup or self.state == self.STATE.on:
                self.state = self.STATE.shutdown
                timeChange = time.time()
     
        # ELECTRIC
        self.log.write("ADC\t"),
        self.log.write("v1:%02f,\t" % (self.volts1)),
        self.log.write("a1:%02f,\t" % (self.amps1)),
        #self.log.write("v2:%02f,\t" % (volts2)),
        #self.log.write("a2:%02f,\t" % (amps2)),
        #self.log.write("v3:%02f,\t" % (volts3)),
        #self.log.write("a3:%02f,\t" % (amps3)),
        self.display.voltage(self.volts1)
        self.display.current(self.amps1)
    

        # TEMPERATURE
        self.log.write("TMP\t"), 
        self.log.write("tB:%02f,\t" % (self.tmpBlue)),
        self.log.write("tE:%02f,\t" % (self.tmpEarth)),
        self.log.write("tR:%02f,\t" % (self.tmpRed)),
        self.log.write("tY:%02f,\t" % (self.tmpYellow)),
        if self.tmpBlue >= self.cutoff
		        or self.tmpEarth  >= self.cutoff
				or self.tmpRed    >= self.cutoff
				or self.tmpYellow >= self.cutoff:
            self.log.write("HOT"),
            self.state = self.STATE.error
        else:
            self.log.write("OK!"),
        self.display.temperature(self.tmpEarth)


        ## STATE MACHINE ##
        if self.state == self.STATE.off:
            # Off
            self.h2.switch(False)
            self.fan.switch(False)
            self.purge.switch(False)

            if self.pfio.input_pins[self.buttonOn].value == True
			        and self.pfio.input_pins[self.buttonOff].value == False:
                self.state = self.STATE.startup
                timeChange = time.time()
        if self.state == self.STATE.startup:
            # Startup
            try:
                self.h2.timed(0,self.startTime)
                self.fan.timed(0,self.startTime)
                self.purge.timed(0,self.startTime)
                if (time.time() - timeChange) > self.startTime:
                    self.state = self.STATE.on
            except Exception as e:
                #self.log.write("Startup Error")
                self.state = self.STATE.error
        if self.state == self.STATE.on:
            # Running
            try:
                self.h2.switch(True)
                self.fan.switch(True)
                self.purge.timed(self.purgeFreq,self.purgeTime)
            except Exception as e:
                #self.log.write("Running Error")
                self.state = self.STATE.error
        if self.state == self.STATE.shutdown:
            # Shutdown
            try:
                self.h2.switch(False)
                self.fan.timed(0,self.stopTime)
                self.purge.timed(0,self.stopTime)
                if (time.time() - timeChange) > self.stopTime:
                    self.state = self.STATE.off
            except Exception as e:
                #self.log.write("Shutdown Error")
                self.state = self.STATE.error
        if self.state == self.STATE.error:
            # Error lock           
            self.h2.switch(False)
            self.purge.switch(False)
            if self.blue() >= self.cutoff
			        or self.earth()  >= self.cutof
					or self.red()    >= self.cutoff
					or self.yellow() >= self.cutoff:
                self.fan.switch(True)
            else:
                self.fan.switch(False)
                # Reset button
                if self.pfio.input_pins[self.buttonReset].value == True:
                    self.state = self.STATE.off
                    #print("\nResetting")
=======
from   time      import time, sleep, asctime
import pifacedigitalio
import pifacecad
import RPi.GPIO  as GPIO
#import smbus
import argparse
import math
from adcpi       import *
from tmp102      import *
from switch      import *
from h100Display import *
from purge       import *

# Define default global constants
parser = argparse.ArgumentParser(description='Fuel Cell Controller by Simon Howroyd 2013')
parser.add_argument('--out'	   			,		help='Name of the output logfile')
parser.add_argument('--controller'  	,type=int, 	default=1, 	help='Set to 0 for controller off')
parser.add_argument('--purgeController' ,type=int, 	default=0, 	help='Set to 1 for purge controller on')
parser.add_argument('--purgeTime'  	,type=float, 	default=0.5,	help='How long to purge for in seconds')
parser.add_argument('--purgeFactor'  	,type=float, 	default=1,	help='Rate of change of purge frequency with current')
parser.add_argument('--purgeMax'  	,type=float, 	default=40,	help='Max time between purges in seconds')
parser.add_argument('--purgeFreq'  	,type=float, 	default=30,	help='Time between purges in seconds')
parser.add_argument('--cutoff'     	,type=float, 	default=26.0,	help='Temperature cutoff in celcius')
parser.add_argument('--p'     		,type=float, 	default=10.0,	help='Purge Proportional Controller')
parser.add_argument('--i'     		,type=float, 	default=1.0,	help='Purge Integral Controller')
parser.add_argument('--d'     		,type=float, 	default=0.5,	help='Purge Differential Controller')
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
purgeController= args.purgeController
purgeMax       = args.purgeMax
purgeFactor    = args.purgeFactor
purgeFreq      = args.purgeFreq
controller     = args.controller

# State machine cases
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in list(enums.items()))
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
#bus       = smbus.SMBus(1)
purge     = Switch(purgePin)
h2        = Switch(h2Pin)
fan       = Switch(fanPin)
blue      = I2cTemp(BLUE)
earth     = I2cTemp(EARTH)
red       = I2cTemp(RED)
yellow    = I2cTemp(YELLOW)
purgeCtrl = Purge(args.p, args.i, args.d, zero=30)

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

timeDelta = 0
timeBegin = 0

print("%s\n" % asctime())

display.fuelCellName('H100')

########
# Main #
########
try:
	while (True):
		print('\n', time(), end='\t')
		print('%02f' % timeDelta, end='\t')

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
		power      = volts[0]*amps[0]
		print('v1', '\t', '%02f' % volts[0], end='\t')
		print('a1', '\t', '%02f' % amps[0], end='\t')
		print('p1', '\t', '%02f' % power, end='\t')
		display.voltage(volts[0])
		display.current(amps[0])

		# TEMPERATURE
		tmpBlue    = blue()
		tmpEarth   = earth()
		tmpRed     = red()
		tmpYellow  = yellow()
		tmpMax     = max(tmpBlue, tmpEarth, tmpRed, tmpYellow)
		print('t', '\t', '%02f' % tmpMax,   end='\t')
		if tmpMax >= cutoff:
			print('HOT', end='\t')
			state = STATE.error
		else:
			print('OK', end='\t')
		display.temperature(tmpMax)
		
		# PURGE CALCULATOR
		if purgeController is 1:
#			purgeFreq = -purgeFactor*amps[0] + purgeMax #was 1.8		

#			vTarget = -0.0204*math.pow(amps[0],3) + 0.234*math.pow(amps[0],2) - 1.7969*amps[0] + 19.945
			vTarget = -1.2*amps[0] + 21
			vError = volts[0] - vTarget
#
#			purgeFreq = 30 - args.p*vError

			purgeFreq = purgeCtrl(vError)
>>>>>>> master

			clamp = lambda n, minn, maxn: max(min(maxn, n), minn)
			purgeFreq = clamp(purgeFreq, 10, purgeMax)
			print('vE', '\t', '%.2f' % vError, end='\t')
			 
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

<<<<<<< HEAD
    #######
    # End #
    #######


    def stop(self):
        self._Process__stop()
=======
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
					timeBegin = time()
			#######
			# ON  #
			#######
			if state == STATE.on:
				h2.switch(True)
				fan.switch(True)
				purge.timed(purgeFreq, purgeTime)
				
				timeDelta = time() - timeBegin
				
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
					timeDelta = 0
					timeBegin = 0
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
    del purge, h2, fan, blue, earth, red, yellow
    print('\n\n\nProgramme successfully exited and closed down\n\n')
#######
# End #
#######
>>>>>>> master
