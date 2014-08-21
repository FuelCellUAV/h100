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
        # Check if user inputted a valid resolution
        if res != 12 and res != 14 and res != 16 and res != 18:
            raise IndexError('Incorrect ADC Resolution')
        else:
            self.__res = res

        # Build default address and configuration register
        self.__config = [[0x68, 0x90],
                         [0x68, 0xB0],
                         [0x68, 0xD0],
                         [0x68, 0xF0],
                         [0x69, 0x90],
                         [0x69, 0xB0],
                         [0x69, 0xD0],
                         [0x69, 0xF0]]

        # Set resolution in configuration register
        for x in range(len(self.__config)):
            self.__config[x][1] = self.__config[x][1] | int((res - 12) / 2) << 2

        # Set the calibration multiplier
        self.__varDivisor = 0b1 << (res - 12)
        self.__varMultiplier = (2.495 / self.__varDivisor) / 1000

    # Method to change the channel we wish to read from
    @staticmethod
    def __changechannel(config):
        with i2c.I2CMaster() as bus:
            bus.transaction(
                i2c.writing_bytes(config[0], config[1]))

    # Method to read adc
    @staticmethod
    def __getadcreading(config, multiplier, res):
        with i2c.I2CMaster() as bus:
            # Calculate how many bytes we will receive for this resolution
            numBytes = int(max(0, res / 2 - 8) + 3)

            # Initialise the ADC
            adcreading = bus.transaction(
                i2c.writing_bytes(config[0], config[1]),
                i2c.reading(config[0], numBytes))[0]

            # Wait for valid data **blocking**
            while (adcreading[-1] & 128):
                adcreading = bus.transaction(
                    i2c.writing_bytes(config[0], config[1]),
                    i2c.reading(config[0], numBytes))[0]

            # Shift bits to product result
            if numBytes is 4:
                t = ((adcreading[0] & 0b00000001) << 16) | (adcreading[1] << 8) | adcreading[2]
            else:
                t = (adcreading[0] << 8) | adcreading[1]

            # Check if positive or negative number and invert if needed
            if adcreading[0] > 128:
                t = ~(0x020000 - t)

            # Return result
            return t * multiplier

    # External getter
    def get(self, channel):
        self.__changechannel(self.__config[channel])
        return self.__getadcreading(self.__config[channel], self.__varMultiplier, self.__res)

    # Print all channels to screen
    def printall(self):
        for x in range(8):
            print("%d: %02f" % (x + 1, self.get(x)), end='\t')
        print()
