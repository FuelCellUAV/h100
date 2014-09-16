#!/usr/bin/env python3
# Re-written by Simon Howroyd 2014 for python3
#

import quick2wire.i2c as i2c


class HybridIo:
    def __init__(self):
        __bit_register       = [0b00000000, 0b00000000]
        __direction_register = [0b00000000, 0b00000000]


    @property
    def bit_register(self):
        return self.__bit_register

    @name.setter
    def bit_register(self, register):
        self.__bit_register = 








class Hybrid:
    def __init__(self):

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
