#!/usr/bin/python2


# Class to read I2c TMP102 Temperature Sensor
class I2cTemp:
        address = 0x00

        def __init__(self, i2cbus, address):
                self.address = address
                self.bus = i2cbus

        def __call__(self):
                try:
                   tmp  = self.bus.read_word_data(self.address,0)
                   msb  = (tmp & 0x00ff)
                   lsb  = (tmp & 0xff00) >> 8
                   temp = ((( msb * 256 ) + lsb) >> 4 ) * 0.0625
                   return temp
                except Exception as e:
                   #print ("I2C Temp Error")
                   return -1

