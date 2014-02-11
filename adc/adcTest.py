#!/usr/bin/python2

# adc tester

# Copyright (C) 2013  Simon Howroyd
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

# Import libraries
from   time import sleep

from   adcpi import *


adc = AdcPi2()

#########
# Setup #
#########
print("\nADC Tester")
print("(c) Simon Howroyd 2013")
print("Loughborough University\n")

########
# Main #
########
while True:
    sleep(1)
    adc.printall()
