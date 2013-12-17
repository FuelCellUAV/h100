#!/usr/bin/env python3
# read abelectronics ADC Pi V2 board inputs with repeating reading from each channel.
# # Requries Python 2.7
# Requires SMBus 
# I2C API depends on I2C support in the kernel

# Version 1.0  - 06/02/2013
# Version History:
# 1.0 - Initial Release

#
# Usage: changechannel(address, hexvalue) to change to new channel on adc chips
# Usage: getadcreading(address, hexvalue) to return value in volts from selected channel.
#
# address = adc_address1 or adc_address2 - Hex address of I2C chips as configured by board header pins.

import multiprocessing
from smbus import SMBus
import re
import I2c

class AdcPi2(I2c):
    
    adc_address1 = 0x68
    adc_address2 = 0x69

    varDivisior = 64 # from pdf sheet on adc addresses and config
    varMultiplier = (2.4705882/varDivisior)/1000
    
    ## Constructor can receive the I2C bus or find it itself
    def __init__(self):
        #self.bus = self.getI2cBus()
		super().__init__()

    #def getI2cBus(self):
    #    # detect i2C port number and assign to i2c_bus
    #    for line in open('/proc/cpuinfo').readlines():
    #        m = re.match('(.*?)\s*:\s*(.*)', line)
    #        if m:
    #            (name, value) = (m.group(1), m.group(2))
    #            if name == "Revision":
    #                if value [-4:] in ('0002', '0003'):
    #                    i2c_bus = 0
    #                else:
    #                    i2c_bus = 1
    #                break
    #    return SMBus(i2c_bus)

    def changechannel(self, address, adcConfig):
            tmp= self.bus.write_byte(address, adcConfig)

    def getadcreading(self, address, adcConfig):
        # create byte array and fill with initial values to define size
        adcreading = bytearray()
 
        adcreading.append(0x00)
        adcreading.append(0x00)
        adcreading.append(0x00)
        adcreading.append(0x00)
    
        adcreading = self.bus.read_i2c_block_data(address,adcConfig)
        h = adcreading[0]
        m = adcreading[1]
        l = adcreading[2]
        s = adcreading[3]
        # wait for new data
        while (s & 128):
                adcreading = self.bus.read_i2c_block_data(address,adcConfig)
                h = adcreading[0]
                m = adcreading[1]
                l = adcreading[2]
                s = adcreading[3]
        
        # shift bits to product result
        t = ((h & 0b00000001) << 16) | (m << 8) | l
        # check if positive or negative number and invert if needed
        if (h > 128):
                t = ~(0x020000 - t)
        return t * self.varMultiplier

    def get(self, address, config):
        self.changechannel(address, config)
        return self.getadcreading(address, config)        

    def printall(self):
        print ("Channel 1: %02f" % self.get(self.adc_address1, 0x9C)),
        print ("2: %02f" % self.get(self.adc_address1, 0xBC)),
        print ("3: %02f" % self.get(self.adc_address1, 0xDC)),
        print ("4: %02f" % self.get(self.adc_address1, 0xFC)),
        print ("5: %02f" % self.get(self.adc_address2, 0x9C)),
        print ("6: %02f" % self.get(self.adc_address2, 0xBC)),
        print ("7: %02f" % self.get(self.adc_address2, 0xDC)),
        print ("8: %02f" % self.get(self.adc_address2, 0xFC)),
        print ("\n")


class AdcPi2Daemon( AdcPi2 , multiprocessing.Process):
    val = multiprocessing.Array('d',range(8))
    self.threadId = 1
	
    def __init__(self):
        #self.bus = self.getI2cBus()
		super().__init__()
        multiprocessing.Process.__init__(self)
        self.threadId = self.threadId + 1
        self.Name = 'AdcPi2'

    def run(self):
        while True:
            self.val[0] = self.get(self.adc_address1, 0x9C)
            self.val[1] = self.get(self.adc_address1, 0xBC)
            self.val[2] = self.get(self.adc_address1, 0xDC)
            self.val[3] = self.get(self.adc_address1, 0xFC)
            self.val[4] = self.get(self.adc_address2, 0x9C)
            self.val[5] = self.get(self.adc_address2, 0xBC)
            self.val[6] = self.get(self.adc_address2, 0xDC)
            self.val[7] = self.get(self.adc_address2, 0xFC)

    def stop(self):
        self._Process__stop()
