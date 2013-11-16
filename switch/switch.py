#!/usr/bin/python2

# Simple software timer for a switch on the piface digital io

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

from time import time
import ../piface.pfio as pfio

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
