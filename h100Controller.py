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

# Includes
import sys
import multiprocessing
import time
import pifacedigitalio
sys.path.append('./adc')
import adcpi
sys.path.append('./temperature')
import tmp102
sys.path.append('./switch')
import switch

# Function to mimic an 'enum'. Won't be needed in Python3.4
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in list(enums.items()))
    enums['reverse_mapping'] = reverse
    return type('Enum', (), enums)

##############
# CONTROLLER #
##############
class H100(multiprocessing.Process):
	# Define Sensors
	Adc  = AdcPi2Daemon
	Temp = [I2cTemp(0x48),
			I2cTemp(0x49),
			I2cTemp(0x4A),
			I2cTemp(0x4B)]
	
	# Define Switches
	pfio  = pifacedigitalio.PiFaceDigital() # Start piface
	fan   = Switch(0)
	h2    = Switch(1)
	purge = Switch(2)
	on    = 0 # Switch numbers on the pfio
	off   = 1
	reset = 2
	
	# Define Variables
	amps  = multiprocessing.Array('d',[0]*8) # Shared memory
	volts = multiprocessing.Array('d',[0]*8)
	power = multiprocessing.Array('d',[0]*4)
	temp  = multiprocessing.Array('d',[0]*4)
	
	# Define Controllables
	startTime = 3   # Seconds
	stopTime  = 10  # Seconds
	purgeTime = 0.5 # Seconds
	purgeFreq = 30  # Seconds
	cutoffTemp= 30  # Celsius
	
	# Define States
	STATE = enum(startup='startup', on='on', shutdown='shutdown', off='off', error='error')
	state = multiprocessing.Value(ctypes.c_char_p,'') # Shared memory
	
	##############
	# INITIALISE #
	##############
	def __init__(self):
		multiprocessing.Process.__init__(self)
		self.Adc.daemon = True
		self.Adc.start()
		self.Temp.daemon = True
		self.Temp.start()
	
	##############
	#    MAIN    #
	##############
	def run(self):
		timeChange = time()
		state.value = STATE.off
		
		while True:
			try:
				# BUTTONS
				if self.__getButton(self.off): # Turn off
					if state.value == self.STATE.startup or state.value == self.STATE.on:
						state.value = self.STATE.shutdown
						timeChange = time()
				elif self.__getButton(self.on): # Turn on
					if state.value == self.STATE.off:
						state.value = self.STATE.startup
						timeChange = time()
				elif self.__getButton(self.reset): # Reset error
					if state.value == self.STATE.error:
						state.value = self.STATE.off
						timeChange = time()
						
				# OVER TEMPERATURE
				if max(self.temp) > self.cutoffTemp:
					state.value = self.STATE.error
					
				# OVER/UNDER VOLTAGE
					# todo, not important
					
				# SENSORS
				self.amps[0]  = self.__getCurrent(0)
				self.volts[0] = self.__getVoltage(1)
				self.power[0] = self.volts*self.amps
				for x in range(len(self.temp)):
					self.temp[x] = self.__getTemperature(x)
					
				# STATE MACHINE
				if state.value == self.STATE.off:
					self.stateOff()
				if state.value == self.STATE.startup:
					self.stateStartup()
					if (time()-timeChange) > self.startTime):
						state.value = self.STATE.on
				if state.value == self.STATE.on:
					self.stateOn()
				if state.value == self.STATE.shutdown:
					self.stateShutdown()
					if (time()-timeChange) > self.stopTime):
						state.value = self.STATE.off
				if state.value == self.STATE.error:
					self.stateError()
			finally:
				# When the programme exits, put through the shutdown routine
				if state.value != self.STATE.off:
					timeChange = time()
					while (time()-timeChange) < self.stopTime:
						self.stateShutdown()
				self.Adc.stop()
				for x in range(len(self.temp)):
					self.Temp[x].stop()
				del Adc, Temp, purge, h2, fan, pfio
				print('\n\n\nFuel Cell Shut Down\n\n')
	
	##############
	#  ROUTINES  #
	##############
	# State Off Routine
	def stateOff(self):
		self.h2.switch(False)
		self.fan.switch(False)
		self.purge.switch(False)
	# State Startup Routine	
	def stateStartup(self):
		self.h2.timed(0, self.startTime)
		self.fan.timed(0, self.startTime)
		self.purge.timed(0, self.startTime)
	# State On Routine
	def stateOn(self):
		self.h2.switch(True)
		self.fan.switch(True)
		self.purge.switch(self.purgeFreq, self.purgeTime)
	# State Shutdown Routine
	def stateShutdown(self):
		self.h2.switch(False)
		self.fan.switch(0, stopTime)
		self.purge.switch(0 stopTime)
	# State Error Routine
	def stateError(self):
		self.h2.switch(False)
		self.purge.switch(False)
		if max(self.temp) > self.cutoffTemp:
			self.fan.switch(True)
		else:
			self.fan.switch(False)
	
	##############
	#EXT. GETTERS#
	##############
	# Get State String (global)
	def getState(self):
		return self.state.value
	# Get Current (global)	
	def getCurrent(self):
		return self.amps
	# Get Voltage (global)	
	def getVoltage(self):
		return self.volts
	# Get Power (global)	
	def getPower(self):
		return self.power
	# Get Temperature (global)
	def getTemperature(self):
		return self.Temp
	
	##############
	#INT. GETTERS#
	##############
	# Get Current (internal)
	def __getCurrent(self, channel):
		return (abs(self.Adc.val[channel] * 1000 / 4.2882799485) + 0.6009) / 1.6046
	# Get Voltage (internal)
	def __getVoltage(self, channel):
		return (abs(self.Adc.val[channel] * 1000 / 60.9559671563))
	# Get Temperature (internal)
	def __getTemperature(self, channel):
		return self.Temp[channel]
	# Get Button (internal)
	def __getButton(self, button):
		return self.pfio.input_pins[button].value
		