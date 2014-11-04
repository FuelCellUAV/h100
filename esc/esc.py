##!/usr/bin/env python3

# Arduino Electronic Speed Controller Driver

# Copyright (C) 2014  Simon Howroyd
# 
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.

#############################################################################

# Import libraries
from time import sleep
from quick2wire.i2c import I2CMaster, writing_bytes


# Define class
class esc:
    # Code to run when class is created
    def __init__(self, address=0x2c):
        self.__address = address
        self.__throttle = 0

    # Method to send throttle to Arduino
    @staticmethod
    def __set(address, value):
        try:
            # Using the I2C databus...
            with I2CMaster(1) as master:
                master.transaction(
                    writing_bytes(address, value))
                
            # Return result
            return value
            
        # If I2C error return -1
        except IOError:
            return -1

    # Property - What is the current throttle setting?
    @property
    def throttle(self):
        return self.__throttle

    # Property - Set a new throttle
    @throttle.setter
    def throttle(self, value):
        # Convert the user request to an integer
        request = int(value)
        
        # If the request is -1 that is a stop code, set zero
        if request is -1:
            setpoint = 0
            
        # If the request is 0-100 it is good, set that
        elif request<=100 and request>=0:
            setpoint = request
            
        # Otherwise raise an exception to crash the code
        else:
            raise ValueError

        # Send the accepted throttle to the Arduino
        try:
            self.__throttle = self.__set(self.__address, setpoint)
        
        # If that fails (disconnected) then ignore
        except Exception as e:
            pass

    # Calibration routine
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
