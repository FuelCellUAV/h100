#!/usr/bin/python3

import quick2wire.i2c as i2c

# Class to read I2c TMP102 Temperature Sensor
class I2cTemp:
        def __init__(self, address):
                self.address = address

        def __call__(self):
                with i2c.I2CMaster() as bus:
					try:
						tmp = bus.transaction(
							i2c.writing_bytes(self.address, 0),
							i2c.reading(address, 2))[0]
						msb  = (tmp & 0x00ff)
						lsb  = (tmp & 0xff00) >> 8
						temp = ((( msb * 256 ) + lsb) >> 4 ) * 0.0625
						return temp
					except Exception as e:
						#print ("I2C Temp Error")
						return -1

