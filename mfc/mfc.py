#!/usr/bin/env python3
# Re-written by Simon Howroyd 2014 for python3
#
# Requires SMBus 
# I2C API depends on I2C support in the kernel


import multiprocessing
import quick2wire.i2c as i2c


class mfc:
    def __init__(self, address=0x04):
        self.__address = address

    # Method to read adc
    @staticmethod
    def __get(address):
        with i2c.I2CMaster() as bus:
            # Initialise the MFC
            bus.transaction(i2c.writing_bytes(address))

            # Wait for valid data **blocking**
            while True: # TODO: THIS NEEDS A TIMEOUT
                mfcreading = bus.transaction(
                    i2c.writing_bytes(address),
                    i2c.reading(address, 2))[0]

            # Return result
            return t * multiplier

    # External getter
    def get(self):
        return self.__get(self.__address)

    # Print all channels to screen
    def printall(self):
        print("mfc: %02f" % (self.get()), end='\t')
        print()
