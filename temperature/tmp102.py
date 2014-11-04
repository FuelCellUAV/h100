##!/usr/bin/env python3

# TMP102 Temperature Sensor Driver

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
import multiprocessing
from quick2wire.i2c import I2CMaster, writing_bytes, reading


# Define class
class Tmp102:
    # Method to get the current reading
    @staticmethod
    def get(address):
        try:
            # Using the I2C databus...
            with I2CMaster(1) as master:
                
                # Read two bytes of data
                msb, lsb = master.transaction(reading(address, 2))[0]
                
                # Assemble the two bytes into a 16bit integer
                temperature = ((( msb * 256 ) + lsb) >> 4 ) * 0.0625
                
                # Return the value
                return temperature

        # If I2C error return -1
        except IOError:
            return -1
