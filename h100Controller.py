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
	adc  = AdcPi2Daemon
	temp = [I2cTemp(0x48),
			I2cTemp(0x49),
			I2cTemp(0x4A),
			I2cTemp(0x4B)]
	
	# Define Switches
	pfio  = pifacedigitalio.PiFaceDigital() # Start piface
	fan   = Switch(0)
	h2    = Switch(1)
	purge = Switch(2)
	on    = 0
	off   = 1
	reset = 2
	
	# Define States
	STATE = enum(startup='startup', on='on', shutdown='shutdown', off='off', error='error')
	state = multiprocessing.Value(ctypes.c_char_p,'')
	state.value = STATE.off
	
	# Init Code
	def __init__(self):
		multiprocessing.Process.__init__(self)
		self.adc.daemon = True
		self.adc.start()
	
	# Main run code
	def run(self):
		timeChange = time()
		while True:
			# STOP BUTTON
			if (self.pfio.input_pins[on].value == False) and (self.pfio.input_pins[off].value == True):
				if self.state.value == self.STATE.startup or self.state.value == self.STATE.on:
					self.state.value = STATE.shutdown
					timeChange = time()
			amps					
			
			
	# Get State String
	def getState(self):
		return self.state.value
		
	# Get Current
	def getCurrent(self):
		amps[0] = (abs(adc.val[0] * 1000 / 4.2882799485) + 0.6009) / 1.6046
		