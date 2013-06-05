#!/usr/bin/python2
from time import time
import piface.pfio as pfio

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
