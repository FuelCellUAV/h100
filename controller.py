#!/usr/bin/python3

# Fuel Cell Controller for the Horizon H100

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

# Import libraries
import sys
import time
import argparse
from display import h100Display
import h100Controller


# Define default global constants
parser = argparse.ArgumentParser(description='Fuel Cell Controller by Simon Howroyd 2013')
parser.add_argument('--out', help='Name of the output logfile')
args = parser.parse_args()

# Class to save to file & print to screen
class MyWriter:
    def __init__(self, stdout, filename):
        self.stdout = stdout
        self.logfile = open(filename, 'a')

    def write(self, text):
        self.stdout.write(text)
        self.logfile.write(text)

    def close(self):
        self.stdout.close()
        self.logfile.close()

    def flush(self):
        self.stdout.flush()

# Look at user arguments
if args.out: # save to output file
    writer = MyWriter(sys.stdout, args.out)
    sys.stdout = writer

#########
# Setup #
#########
display = h100Display.FuelCellDisplay(1, "PF Display")
display.daemon = True # To ensure the process is killed on exit

h100 = h100Controller.H100()
#h100.daemon = True

print("\nFuel Cell Controller")
print("Horizon H-100 Stack")
print("(c) Simon Howroyd 2013")
print("Loughborough University\n")

print("controller  Copyright (C) 2013  Simon Howroyd")
print("This program comes with ABSOLUTELY NO WARRANTY; for details type `show w'.")
print("This is free software, and you are welcome to redistribute it,")
print("under certain conditions; type `show c' for details.\n")

print("%s\n" % time.asctime())

display.fuelCellName('H100')

########
# Main #
########
try:
    h100.run()
    display.start()

    while (True):
        print('\n', time.time(), end='\t')

        # PRINT STATE
        print(h100.getState(), end='\t')
        display.state(h100.getState())

        # ELECTRIC
        print('v1', '\t', '%02f' % h100.getVoltage()[0], end='\t')
        print('a1', '\t', '%02f' % h100.getCurrent()[0], end='\t')
        print('p1', '\t', '%02f' % h100.getPower()[0], end='\t')
        display.voltage(h100.getVoltage()[0])
        display.current(h100.getCurrent()[0])

        # TEMPERATURE
        print('tMax', '\t', max(h100.getTemperature()), end='\t')
        display.temperature(max(h100.getTemperature()))

# Programme Exit Code
finally:
    h100.shutdown()
    print('\n\n\nProgramme successfully exited and closed down\n\n')
#######
# End #
#######
