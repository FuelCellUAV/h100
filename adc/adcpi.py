#!/usr/bin/env python3
# Re-written by Simon Howroyd 2014 for python3
#
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

import quick2wire.i2c as i2c


class AdcPi2:
    adc_address1 = 0x68
    adc_address2 = 0x69
    varDivisior = 64  # from pdf sheet on adc addresses and config
    varMultiplier = (2.495 / varDivisior) / 1000

    def changechannel(self, address, adcConfig):
        with i2c.I2CMaster() as bus:
            bus.transaction(
                i2c.writing_bytes(address, adcConfig))

    def getadcreading(self, address, adcConfig):
        with i2c.I2CMaster() as bus:

            # create byte array and fill with initial values to define size
            adcreading = bytearray()

            adcreading.append(0x00)
            adcreading.append(0x00)
            adcreading.append(0x00)
            adcreading.append(0x00)

            adcreading = bus.transaction(
                i2c.writing_bytes(address, adcConfig),
                i2c.reading(address, 4))[0]

            #print('full= ',adcreading)
            #print('0= ',adcreading[0])
            #print('1= ',adcreading[1])
            #print('2= ',adcreading[2])
            #print('3= ',adcreading[3])

            h = adcreading[0]
            m = adcreading[1]
            l = adcreading[2]
            s = adcreading[3]

            # wait for new data
            while (s & 128):
                adcreading = bus.transaction(
                    i2c.writing_bytes(address, adcConfig),
                    i2c.reading(address, 4))[0]
                h = adcreading[0]
                m = adcreading[1]
                l = adcreading[2]
                s = adcreading[3]

            # shift bits to product result
            t = ((h & 0b00000001) << 16) | (m << 8) | l
            # check if positive or negative number and invert if needed
            if h > 128:
                t = ~(0x020000 - t)
            return t * self.varMultiplier

    def get(self, address, config):
        self.changechannel(address, config)
        return self.getadcreading(address, config)

    def printall(self):
        print("Channel 1: %02f" % self.get(self.adc_address1, 0x9C)),
        print("2: %02f" % self.get(self.adc_address1, 0xBC)),
        print("3: %02f" % self.get(self.adc_address1, 0xDC)),
        print("4: %02f" % self.get(self.adc_address1, 0xFC)),
        print("5: %02f" % self.get(self.adc_address2, 0x9C)),
        print("6: %02f" % self.get(self.adc_address2, 0xBC)),
        print("7: %02f" % self.get(self.adc_address2, 0xDC)),
        print("8: %02f" % self.get(self.adc_address2, 0xFC)),
        print("\n")


class AdcPi2Daemon(AdcPi2, multiprocessing.Process):
    val = multiprocessing.Array('d', range(8))

    def __init__(self):
        multiprocessing.Process.__init__(self)
        self.threadId = 1
        self.Name = 'AdcPi2'

    def run(self):
        try:
            while True:
                self.val[0] = self.get(self.adc_address1, 0x9C)
                self.val[1] = self.get(self.adc_address1, 0xBC)
                self.val[2] = self.get(self.adc_address1, 0xDC)
                self.val[3] = self.get(self.adc_address1, 0xFC)
                self.val[4] = self.get(self.adc_address2, 0x9C)
                self.val[5] = self.get(self.adc_address2, 0xBC)
                self.val[6] = self.get(self.adc_address2, 0xDC)
                self.val[7] = self.get(self.adc_address2, 0xFC)
        finally:
            print('\nADC Shut Down\n')
