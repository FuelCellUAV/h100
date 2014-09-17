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

import quick2wire.i2c as i2c

class MCP3424:
        # Hybrid
        # Address 1 0xD0
        # Address 2 0xD8
        
        # AdcPi2
        # Address 1 0x68
        # Address 2 0x69
    def __init__(self, address, resolution):
        # Check if user inputed a valid resolution
        if resolution != 12 and resolution != 14 and resolution != 16 and resolution != 18:
            raise IndexError('Incorrect ADC Resolution')
        else:
            self.__res = resolution
            
        # Build default address and configuration register
        self.__config = [[address, 0x90],
                         [address, 0xB0],
                         [address, 0xD0],
                         [address, 0xF0]]

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
        
        

class AdcPi2:
    def __init__(self, res=12):
        self.__adc1 = MCP3424(0x68, res)
        self.__adc2 = MCP3424(0x69, res)
        
    def get(self, channel):
        if channel in range(0,4):
            return self.__adc1.get(channel)
        elif channel in range(4,8):
            return self.__adc2.get(channel)
        else:
            return -1 # Error in channel