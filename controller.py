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
import multiprocessing
import time
import pifacedigitalio
import pifacecad
import RPi.GPIO  as GPIO
import smbus
import argparse
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
			
	    self.STATE = enum(startup='startup', on='on', shutdown='shutdown', off='off', error='error')
        self.state = self.STATE.off

        multiprocessing.Process.__init__(self)
        self.threadId = 1
        self.Name = 'Controller'
        
        self.pfio           = pifacedigitalio.PiFaceDigital()  # Start PiFace IO
        self.display        = FuelCellDisplay(1, "PF Display") # Start PiFace Display
        self.adc            = AdcPi2Daemon() # Start ADC

        display.daemon = True # To ensure the process is killed on exit
        display.start()       # Turn the display on
        adc.daemon     = True
        adc.start()           # Turn on the ADC
		
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
        #display.run()

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

    ## end STATE MACHINE ##

#######
# End #
#######


    def stop(self):
        self._Process__stop()