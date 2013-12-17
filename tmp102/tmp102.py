#!/usr/bin/python2
import multiprocessing
import I2c
from smbus import SMBus

# Class to read I2c TMP102 Temperature Sensor
class I2cTemp(I2c):
    address = 0x00

    def __init__(self, address):
        self.address = address
        super().__init__()

    def get(self):
        try:
            tmp  = self.bus.read_word_data(self.address,0)
            msb  = (tmp & 0x00ff)
            lsb  = (tmp & 0xff00) >> 8
            temp = ((( msb * 256 ) + lsb) >> 4 ) * 0.0625
            return temp
        except Exception as e:
            #print ("I2C Temp Error")
            return -1
			
	def __call__(self):
	    return self.get()

class I2cTempDaemon( I2cTemp , multiprocessing.Process):
    val      = multiprocessing.Value('d',0.0)
    instance = 1
    def __init__(self):
        super().__init__()
        multiprocessing.Process.__init__(self)
        self.threadId = self.instance
		self.instance = self.instance + 1
        self.Name = 'TMP102'
		
	def run(self):
	    while True:
		    self.val.value = self.get()
			
	def stop(self):
        self._Process__stop()