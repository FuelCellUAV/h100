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

    def __init__(self, res=12):
        if res != 12 and res != 14 and res != 16 and res !=18:
            raise IndexError('Incorrect ADC Resolution')

        self.config = []
        self.config.append([0x68,0x90]) # Ch1
        self.config.append([0x68,0xB0]) # Ch2
        self.config.append([0x68,0xD0]) # Ch3
        self.config.append([0x68,0xF0]) # Ch4
        self.config.append([0x69,0x90]) # Ch5
        self.config.append([0x69,0xB0]) # Ch6
        self.config.append([0x69,0xD0]) # Ch7
        self.config.append([0x69,0xF0]) # Ch8

        if res is 12:
            self.getadcreading = self.getadcreading12
            self.varDivisior = 1
        elif res is 14:
            self.getadcreading = self.getadcreading12
            self.varDivisior = 4
            for x in range(len(self.config)):
                self.config[x][1] = self.config[x][1] | 0b0100
        elif res is 16:
            self.getadcreading = self.getadcreading12
            self.varDivisior = 16
            for x in range(len(self.config)):
                self.config[x][1] = self.config[x][1] | 0b1000
        elif res is 18:
            self.getadcreading = self.getadcreading18
            self.varDivisior = 64
            for x in range(len(self.config)):
                self.config[x][1] = self.config[x][1] | 0b1100

        self.varMultiplier = (2.495 / self.varDivisior) / 1000

    @staticmethod
    def changechannel(config):
        with i2c.I2CMaster() as bus:
            bus.transaction(
                i2c.writing_bytes(config[0], config[1]))

    @staticmethod
    def getadcreading18(config, multiplier):
        with i2c.I2CMaster() as bus:
            # create byte array and fill with initial values to define size
            adcreading = bytearray()

            adcreading.append(0x00)
            adcreading.append(0x00)
            adcreading.append(0x00)
            adcreading.append(0x00)

            adcreading = bus.transaction(
                i2c.writing_bytes(config[0], config[1]),
                i2c.reading(config[0], 4))[0]

            # wait for new data
            h = adcreading[0]
            m = adcreading[1]
            l = adcreading[2]
            s = adcreading[3]

            while (s & 128):
                adcreading = bus.transaction(
                    i2c.writing_bytes(config[0], config[1]),
                    i2c.reading(config[0], 4))[0]
                h = adcreading[0]
                m = adcreading[1]
                l = adcreading[2]
                s = adcreading[3]
            # shift bits to product result
            t = ((h & 0b00000001) << 16) | (m << 8) | l
            # check if positive or negative number and invert if needed
            if h > 128:
                t = ~(0x020000 - t)
            return t * multiplier

    @staticmethod
    def getadcreading12(config, multiplier):
        with i2c.I2CMaster() as bus:
            # create byte array and fill with initial values to define size
            adcreading = bytearray()

            adcreading.append(0x00)
            adcreading.append(0x00)
            adcreading.append(0x00)

            adcreading = bus.transaction(
                i2c.writing_bytes(config[0], config[1]),
                i2c.reading(config[0], 3))[0]

            h = adcreading[0]
            l = adcreading[1]
            s = adcreading[2]

            while (s & 128):
                adcreading = bus.transaction(
                    i2c.writing_bytes(config[0], config[1]),
                    i2c.reading(config[0], 3))[0]
                h = adcreading[0]
                l = adcreading[1]
                s = adcreading[2]

            # shift bits to product result
            t = (h << 8) | l
            # check if positive or negative number and invert if needed
            if h > 128:
                t = ~(0x020000 - t)
            return t * multiplier

    def get(self, channel):
        self.changechannel(self.config[channel])
        return self.getadcreading(self.config[channel], self.varMultiplier)

    def printall(self):
        for x in range(8):
            print("%d: %02f" % (x+1, self.get(x))),
        print("\n")


class AdcPi2Daemon(AdcPi2, multiprocessing.Process):
    val = multiprocessing.Array('d', range(8))

    def __init__(self, res=12):
        super().__init__(res)
        multiprocessing.Process.__init__(self)
        self.threadId = 1
        self.Name = 'AdcPi2Daemon'

    def run(self):
        try:
            while True:
                for x in range(8): self.val[x] = self.get(x)
        finally:
            print('\nADC Shut Down\n')
