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
#from quick2wire.i2c import I2CMaster, reading

# Define class
class mfc:
    # Code to run when class is created
    def __init__(self, getadc, channel):
        self.__getadc = getadc
        self.__channel = channel

    @staticmethod
    def _getRaw(fun, ch):
        return fun(ch)

    # External getter
    def get(self):
        raw = self.__getadc(self.__channel)
        print(raw)
        rate = raw/5.0*1.5
        return rate
