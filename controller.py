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
from purge import pid





# Define default global constants
parser = argparse.ArgumentParser(description='Fuel Cell Controller by Simon Howroyd 2013')
parser.add_argument('--out', help='Name of the output logfile')
parser.add_argument('--purgeController', type=int, default=0, help='Set to 1 for purge controller on')
parser.add_argument('--purgeTime'  	,type=float, 	default=0.5,	help='How long to purge for in seconds')
parser.add_argument('--purgeFreq'  	,type=float, 	default=30,	help='Time between purges in seconds')
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
if args.out:  # save to output file
    writer = MyWriter(sys.stdout, args.out)
    sys.stdout = writer

#########
# Setup #
#########
display = h100Display.FuelCellDisplay(1, "PF Display")
display.daemon = True  # To ensure the process is killed on exit

if args.purgeController:
    purge = pid.Pid(10, 1, 1)
else:
    purge = 0

h100 = h100Controller.H100(purgeControl=purge, purgeFreq=args.purgeFreq, purgeTime=args.purgeTime)
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
    display.start()

    while (True):
        h100.run()
        print('\n', time.time(), end='\t')

        # PRINT STATE
        print(h100.getState(), end='\t')
        display.state(h100.getState())

        # ELECTRIC
        print('v1', '\t', '%.3f' % h100.getVoltage()[0], end='\t')
        print('a1', '\t', '%.3f' % h100.getCurrent()[0], end='\t')
        print('p1', '\t', '%.3f' % h100.getPower()[0], end='\t')
        display.voltage(h100.getVoltage()[0])
        display.current(h100.getCurrent()[0])

        # TEMPERATURE
        print('t', end='\t')
        print(h100.getTemperature()[0], end='\t')
        print(h100.getTemperature()[1], end='\t')
        print('%.3f' % h100.getTemperature()[2], end='\t')
        print(h100.getTemperature()[3], end='\t')
        print('%.3f' % max(h100.getTemperature()), end='\t')
        display.temperature(max(h100.getTemperature()))

        # PURGE
        print('c', end='\t')
        print('%.3f' % h100.getPurgeFrequency(), end='\t')
        print('%.3f' % h100.getPurgeTime(), end='\t')

# Programme Exit Code
finally:
    h100.shutdown()
    print('\n\n\nProgramme successfully exited and closed down\n\n')
#######
# End #
#######
