#!/usr/bin/env python3
# Simon Howroyd 2014 for python3
#
# Requires quick2wire
# I2C API depends on I2C support in the kernel


from time import sleep
import quick2wire.i2c as i2c


class mfc:
    def __init__(self, address=0x2c):
        self.__address = address

    # Method to read adc
    @staticmethod
    def __get(address):
        with i2c.I2CMaster() as bus:
            mfcreading = bus.transaction(
                i2c.reading(address, 2))[0]
            # Return result
            return mfcreading

    # External getter
    def get(self):
        data = self.__get(self.__address)
        result = data[1] | (data[0] << 8)
        return result/1000.0  # ml to l

    # Print all channels to screen
    def printall(self):
        print("mfc: %02f" % self.get(), end='\t')
        print()
