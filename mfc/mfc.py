##!/usr/bin/env python3

# Mass Flow Controller Arduino driver

# Copyright (C) 2015  Simon Howroyd, Jason James
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
    @staticmethod
    def _getRaw(fun, ch):
        return fun.get(ch)

    # External getter
    def get(self, fun, ch):
        raw = self._getRaw(fun, ch)
        rate = raw/5.0*1.5 
        return rate

    # External getter
    def getMoles(self, fun, ch):
        rate = self.get(fun,ch)*(7.0/6280.0)  # TODO should be *125.718/134.82 (density H2 at 1.5bar)
        return rate
