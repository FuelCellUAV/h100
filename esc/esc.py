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
            if request is -1:
                setpoint = 0
            elif request<=100 and request>=0:
                setpoint = request
            else:
                return

            try:
                self.__throttle = self.__set(self.__address, setpoint)
            except Exception as e:
                print("No I2C bus")

        except Exception as e:
            print('Invalid throttle request')

    def calibration(self):
        if not input("Are you sure you want to calibrate the esc? [y]").startswith("y"):
            return

        self.throttle = 0

        input("Disconnect ESC then press enter...")
        self.__set(self.__address, 100)
        sleep(1)

        input("Connect ESC then press enter...")
        sleep(2)
        self.__set(self.__address, 0)
        sleep(2)
        self.__set(self.__address, 100)
        sleep(2)
        self.__set(self.__address, 0)

        input("Calibration complete, press enter to continue...")

        self.throttle = 0

        return


