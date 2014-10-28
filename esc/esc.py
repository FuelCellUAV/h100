#!/usr/bin/env python3
# Simon Howroyd 2014 for python3
#
# Requires quick2wire
# I2C API depends on I2C support in the kernel


from time import sleep
import quick2wire.i2c as i2c


class esc:
    def __init__(self, address=0x2c):
        self.__address = address
        self.__throttle = 0

    # Method to read adc
    @staticmethod
    def __set(address, value):
        with i2c.I2CMaster() as bus:
            bus.transaction(
                i2c.writing_bytes(address, value))
            # Return result
            return value

    @property
    def throttle(self):
        return self.__throttle

    @throttle.setter
    def throttle(self, value):
        try:
            request = int(value)
            if request<=100 and request>=0:
                self.__throttle = self.__set(self.__address, request)
            else:
                print('Invalid throttle perentage')
        except Exception as e:
            print('Invalid throttle request')

