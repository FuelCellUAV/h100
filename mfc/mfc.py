##!/usr/bin/env python3

# Mass Flow Controller Arduino driver

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
from quick2wire.i2c import I2CMaster, reading

# Define class
class mfc:
    # Code to run when class is created
    def __init__(self, address=0x2c):
        self.__address = address

    # Method to read flow rate from the Arduino
    @staticmethod
    def __get(address):
        mfcreading = -1
        
        # Using the I2C databus...
        with I2CMaster(1) as master:
            mfcreading = master.transaction(
                reading(address, 2))[0]
            
        # Return result
        return mfcreading

    # External getter
    def get(self):
        # Try and get the flow rate from the Arduino
        try:
            data = self.__get(self.__address)
            
        # If that fails (disconnected) return -1, the error code
        except Exception as e:
            return -1
            
        # Assemble the two 8bit words to one 16bit integer
        result = data[1] | (data[0] << 8)
        
        # Return result in litres/min
        return result/1000.0
