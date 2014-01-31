#!/usr/bin/python3

import multiprocessing
import quick2wire.i2c as i2c

# Class to read I2c TMP102 Temperature Sensor
class Tmp102:
	temperature = 0.0
	address = 0x00

	def __init__(self, address):
		self.address = address

	def get(self):
		with i2c.I2CMaster() as bus:
			try:
				tmp = bus.transaction(
				i2c.writing_bytes(self.address, 0),
					i2c.reading(address, 2))[0]
				msb  = (tmp & 0x00ff)
				lsb  = (tmp & 0xff00) >> 8
				self.temperature = ((( msb * 256 ) + lsb) >> 4 ) * 0.0625
				return temp
			except Exception as e:
				#print ("I2C Temp Error")
				return -1

	def __call__(self):
		self.get()
		return self.temperature

class Tmp102Daemon( Tmp102 , multiprocessing.Process):
	val      = multiprocessing.Value('d',0.0)
	
	def __init__(self, address):
		multiprocessing.Process.__init__(self)
		self.address = address

	def run(self):
		try:
			while True:
				self.val.value = self.get()
		finally:
			print('\nTMP102 Shut Down\n')

	def __call__(self):
		return self.val.value
