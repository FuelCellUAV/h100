#!/usr/bin/python3

import multiprocessing
from quick2wire.i2c import I2CMaster, writing_bytes, reading

# Class to read I2c TMP102 Temperature Sensor
class Tmp102:
    temperature = 0.0
    address = 0x00
    iodir_register = 0x00
    register = 0x00

    def __init__(self, address):
        self.address = address
    
    def get(self):
        with I2CMaster() as master:
            try:
                master.transaction(
                    writing_bytes(self.address, self.iodir_register, 0xFF))
                tmp = master.transaction(
                    writing_bytes(self.address, self.register),
                    reading(self.address, 2))
                msb = tmp[0][0]
                lsb = tmp[0][1]
                self.temperature = ((( msb * 256 ) + lsb) >> 4 ) * 0.0625
                return self.temperature
            except Exception as e:
                #print ("I2C Temp Error")
                return -1


class Tmp102Daemon(Tmp102, multiprocessing.Process):
    val = multiprocessing.Value('d', 0.0)
 
    def __init__(self, address):
        self.address = address
        multiprocessing.Process.__init__(self)

    def run(self):
        try:
            while True:
                self.val.value = self.get()
        finally:
            print('\nTMP102 Shut Down\n')

    def __call__(self):
        print('getting ', hex(self.address),end='\t')

        return self.val.value
