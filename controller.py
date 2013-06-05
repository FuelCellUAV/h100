#!/usr/bin/python2

# Import libraries
import sys
from   time import time
import piface.pfio as pfio
import RPi.GPIO as GPIO
import smbus
import argparse

# Define default global constants
parser = argparse.ArgumentParser(description='Fuel Cell Controller by Simon Howroyd 2013')
parser.add_argument('--out'	   	,help='Name of the output logfile')
parser.add_argument('--BLUE'       	,type=int, 	default=0x4a,	help='I2C address')
parser.add_argument('--EARTH'      	,type=int, 	default=0x49, 	help='I2C address')
parser.add_argument('--RED'        	,type=int, 	default=0x48, 	help='I2C address')
parser.add_argument('--YELLOW'     	,type=int, 	default=0x4b, 	help='I2C address')
parser.add_argument('--h2Pin'      	,type=float,	default=0,	help='H2 supply relay') # Relay
parser.add_argument('--fanPin'     	,type=float, 	default=1,    	help='Fan relay') 	# Relay
parser.add_argument('--purgePin'   	,type=float, 	default=2,    	help='Purge switch')
parser.add_argument('--buttonOn'   	,type=float, 	default=0,   	help='On button')
parser.add_argument('--buttonOff'  	,type=float, 	default=1,    	help='Off button')
parser.add_argument('--buttonReset'	,type=float, 	default=2,    	help='Reset button')
parser.add_argument('--purgeFreq'  	,type=float, 	default=30, 	help='How often to purge in seconds')
parser.add_argument('--purgeTime'  	,type=float, 	default=0.5,	help='How long to purge for in seconds')
parser.add_argument('--startTime'  	,type=float, 	default=2,	help='Duration of the startup routine')
parser.add_argument('--stopTime'   	,type=float, 	default=10,	help='Duration of the shutdown routine')
parser.add_argument('--cutoff'     	,type=float, 	default=25.0,	help='Temperature cutoff in celcius')
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
        writer = MyWriter(sys.stdout, args.out)
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

# Class to read ADC
class AdcPiV1:
	# create byte array and fill with initial values to define size
	adcreading = bytearray()

	adcreading.append(0x00)
	adcreading.append(0x00)
	adcreading.append(0x00)
	adcreading.append(0x00)

	resolution = 15.625 / 1000000 # 15.625uV for 18bit sampling
	calibration= 1.0
	#attoVolt   = 1/(63.69*1000)
	#attoAmps   = 1/(36.60*1000)
	
	res = 14
	
	def __init__(self, bus, address, config):
		self.bus     = bus
		self.address = address
		self.config  = config
		
	def __init__(self, bus, address, config, calibration):
		self.bus         = bus
		self.address     = address
		self.config      = config
		self.calibration = calibration
		
	def get(self):
		self.bus.write_byte(self.address, self.config)
		self.adcreading = self.bus.read_i2c_block_data(self.address,self.config)
		h = self.adcreading[0]
		m = self.adcreading[1]
		l = self.adcreading[2]
		s = self.adcreading[3]
		# wait for new data ***BLOCKING FUNCTION***
		while (s & 128):
			self.adcreading = self.bus.read_i2c_block_data(self.address,self.config)
			h = self.adcreading[0]
			m = self.adcreading[1]
			l = self.adcreading[2]
			s = self.adcreading[3]

		# shift bits to product result
		if res is 18:
			t = ((h & 0b00000001) << 16) | (m << 8) | l
			# check if positive or negative number and invert if needed
			if (h > 128):
				t = ~(0x020000 - t)
			t = t * 15.625 / 1000000 * self.calibration
		elif res is 14:
			t = (h & 0b00011111) << 8) | m
			# check if positive or negative number and invert if needed
			if (h > 128):
				t = ~(0x020000 - t)
		return t * 250 / 1000000 * self.calibration

# Class to enable controlled switching
class Switch:
	pin   = 0
	state = False
	lastTime = 0
	lastOff= 0
	
	def __init__(self, pin):
		self.pin = pin
		
	def timed(self, freq, duration):
		# Deactivate if time is up
		if (time()-self.lastTime) >= duration and self.state == True:
		    self.lastTime = time()
		    self.state = False
		    return self.write()

		# Activate
		if (time()-self.lastTime) >= freq and self.state == False:
		    self.lastTime = time()
		    self.state = True
		    return self.write()

	def switch(self, state):
		self.state = state
		return self.write()

	def write(self):
		try:
		    pfio.digital_write(self.pin,self.state)
		except Exception as e:
    		    print ("Timer digital write error")
                
		return self.state

# Class to read I2c TMP102 Temperature Sensor
class I2cTemp:
	address = 0x00
	
	def __init__(self, address):
		self.address = address
		
	def __call__(self):
		try:
		   tmp  = bus.read_word_data(self.address , 0 )
		   msb  = (tmp & 0x00ff)
		   lsb  = (tmp & 0xff00) >> 8
		   temp = ((( msb * 256 ) + lsb) >> 4 ) * 0.0625
		   return temp
		except Exception as e:
           	   print ("I2C Error")
		   return -1

# Define class instances
bus       = smbus.SMBus(0)
adc1	  = AdcPiV1(bus,0x68,0x94,(1000/63.69))
adc2	  = AdcPiV1(bus,0x68,0xB4,(1000/36.60))
adc3	  = AdcPiV1(bus,0x68,0xD4,(1000/63.69))
adc4	  = AdcPiV1(bus,0x68,0xF4,(1000/36.60))
adc5	  = AdcPiV1(bus,0x69,0x94,(1000/63.69))
adc6	  = AdcPiV1(bus,0x69,0xB4,(1000/36.60))
purge     = Switch(purgePin)
h2        = Switch(h2Pin)
fan       = Switch(fanPin)
blue      = I2cTemp(BLUE)
earth     = I2cTemp(EARTH)
red       = I2cTemp(RED)
yellow    = I2cTemp(YELLOW)


# Setup
pfio.init()
state = STATE.off
print("\nFuel Cell Controller")
print("Horizon H-100 Stack")
print("(c) Simon Howroyd 2013")
print("Loughborough University\n")

# Main
while (True):
    print ("ADC= 1:%02f,\t" % (adc1.get())),
    print ("2:%02f,\t" % (adc2.get())),
    print ("3:%02f,\t" % (adc3.get())),
    print ("4:%02f,\t" % (adc4.get())),
    print ("5:%02f,\t" % (adc5.get())),
    print ("6:%02f,\t" % (adc6.get()))

    # TEMP SHUTDOWN
    if blue() >= cutoff or earth() >= cutoff or red() >= cutoff or yellow() >= cutoff:
	print '\rToo hot! (cutoff={} degC)'.format(cutoff),
	print '\tBlue={0}\tEarth={1}\tRed={2}\tYellow={3}'.format(blue(),earth(),red(),yellow()),
	state = STATE.error

    # STOP BUTTON
    if pfio.digital_read(buttonOn) == False and pfio.digital_read(buttonOff) == True:
        if state == STATE.startup or state == STATE.on:
            state = STATE.shutdown
            timeChange = time()
            print ("Shutting down")

    ## STATE MACHINE ##
    if state == STATE.off:
        # Off
        h2.switch(False)
        fan.switch(False)
        purge.switch(False)

        if pfio.digital_read(buttonOn) == True and pfio.digital_read(buttonOff) == False:
	    state = STATE.startup
            timeChange = time()
            print ("Starting")
    if state == STATE.startup:
        # Startup
        try:
	    h2.timed(0,startTime)
            fan.timed(0,startTime)
            purge.timed(0,startTime)
            if (time() - timeChange) > startTime:
                state = STATE.on
                print ("Running")
        except Exception as e:
            print ("Startup Error")
            state = STATE.error
    if state == STATE.on:
        # Running
        try:
            h2.switch(True)
            fan.switch(True)
            purge.timed(purgeFreq,purgeTime)
        except Exception as e:
            print ("Running Error")
            state = STATE.error
    if state == STATE.shutdown:
        # Shutdown
        try:
            h2.switch(False)
            fan.timed(0,stopTime)
            purge.timed(0,stopTime)
            if (time() - timeChange) > stopTime:
                state = STATE.off
                print("Stopped")
        except Exception as e:
            print ("Shutdown Error")
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
            if pfio.digital_read(buttonReset) == True:
	        state = STATE.off
                print("\nResetting")

    ## end STATE MACHINE ##
# end main

