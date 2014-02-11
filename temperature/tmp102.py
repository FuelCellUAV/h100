#!/usr/bin/python3

import multiprocessing
from quick2wire.i2c import I2CMaster, writing_bytes, reading

# Class to read I2c TMP102 Temperature Sensor
class Tmp102:
    @staticmethod
    def get(address):
        with I2CMaster(1) as master:
            try:
                msb, lsb = master.transaction(
                    reading(address, 2))[0]
                temperature = ((( msb * 256 ) + lsb) >> 4 ) * 0.0625
                return temperature
            except Exception as e:
                #print ("I2C Temp Error")
                return -1


class Tmp102Daemon(Tmp102, multiprocessing.Process):
    val = multiprocessing.Array('d', range(4))
    address = [0x48, 0x49, 0x4a, 0x4b]
 
    def __init__(self):
        multiprocessing.Process.__init__(self)

    def run(self):
        try:
            while True:
                for x in range(4):
                    self.val[x] = self.get(self.address[x])
        finally:
            print('\nTMP102 Shut Down\n')

