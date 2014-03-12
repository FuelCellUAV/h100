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
import argparse, sys, time

from display import h100Display
from purge import pid
from h100Controller import H100
from switch import switch
from tdiLoadbank import loadbank
from writer import MyWriter

def _parse_comandline():

    # Define default global constants
    parser = argparse.ArgumentParser(description='Fuel Cell Controller by Simon Howroyd 2013')
    parser.add_argument('--out', help='Name of the output logfile')
    parser.add_argument('--purgeController', type=int, default=0, help='Set to 1 for purge controller on')
    parser.add_argument('--purgeTime'  	,type=float, 	default=0.5,	help='How long to purge for in seconds')
    parser.add_argument('--purgeFreq'  	,type=float, 	default=30,	help='Time between purges in seconds')

    return parser.parse_args()

def _display_header(display):

    print("\nFuel Cell Controller")
    print("Horizon H-100 Stack")
    print("(c) Simon Howroyd 2014")
    print("Loughborough University\n")

    print("This program comes with ABSOLUTELY NO WARRANTY; for details type `show w'.")
    print("This is free software, and you are welcome to redistribute it,")
    print("under certain conditions; type `show c' for details.\n")

    print("%s\n" % time.asctime())

    display.fuelCellName('H100')

def _print_state(h100, display):

    print(h100.getState(), end='\t')
    display.state(h100.getState())

def _print_electric(h100, display, load):

    print('v1', '\t', '%.3f' % h100.getVoltage()[0], end='\t')
    print('v2', '\t', '%.3f' % load.voltage(), end='\t')
    print('a1', '\t', '%.3f' % h100.getCurrent()[0], end='\t')
    print('a2', '\t', '%.3f' % load.current(), end='\t')
    print('p1', '\t', '%.3f' % h100.getPower()[0], end='\t')
    print('p2', '\t', '%.3f' % load.power(), end='\t')
    c = load.mode()
    if 'VOLTAGE' in c:
        print('cv', '\t', '%.3f' % load.constantVoltage(), end='\t')
    elif 'CURRENT' in c:
        print('cc', '\t', '%.3f' % load.constantCurrent(), end='\t')
    elif 'POWER' in c:
        print('cp', '\t', '%.3f' % load.constantPower(), end='\t')
    else:
        print('??', '\t', '0.0', end='\t')
        
    display.voltage(h100.getVoltage()[0])
    display.current(h100.getCurrent()[0])

def _print_temperature(h100, display):

    print('t', end='\t')
    #        print(h100.getTemperature()[0], end='\t')
    #        print(h100.getTemperature()[1], end='\t')
    print('%.3f' % h100.getTemperature()[2], end='\t')
    #        print(h100.getTemperature()[3], end='\t')
    display.temperature(max(h100.getTemperature()))

def _print_purge(h100):

    print('pf/pt', end='\t')
    print('%.3f' % h100.getPurgeFrequency(), end='\t')
    print('%.3f' % h100.getPurgeTime(), end='\t')

if __name__ == "__main__":

    #########
    # Setup #
    #########

    # Grab user args
    args = _parse_comandline()

    # Look at user arguments
    if args.out:  # save to output file
        writer = MyWriter(sys.stdout, ('/media/FUELCELL/' + time.strftime('%y%m%d %H%M%S') + ' ' + args.out + '.tsv'))
    else:
        writer = MyWriter(sys.stdout, ('/media/FUELCELL/' + time.strftime('%y%m%d %H%M%S') + '.tsv'))

    sys.stdout = writer

    if args.purgeController:
        purge = pid.Pid(10, 1, 1)
    else:
        purge = 0

    # Initialise controller class
    h100 = H100(purgeControl=purge, purgeFreq=args.purgeFreq, purgeTime=args.purgeTime)
    #h100.daemon = True

    # Initialise display class
    display = h100Display.FuelCellDisplay(1, "PF Display")
    display.daemon = True  # To ensure the process is killed on exit

    # Initialise loadbank class
    load = loadbank.TdiLoadbank('158.125.152.225', 10001, 'fuelcell')

    ########
    # Main #
    ########

    _display_header(display)

    try:

        display.start()

        while True:

            print('\n', '%.5f' % time.time(), end='\t')
            h100.run()
            # PRINT STATE
            _print_state(h100, display)

            # ELECTRIC
            _print_electric(h100, display, load)

            # TEMPERATURE
            _print_temperature(h100, display)

            # PURGE
            _print_purge(h100)

    # Programme Exit Code
    finally:
        h100.shutdown()
        print('\n\n\nProgramme successfully exited and closed down\n\n')

    #######
    # End #
    #######
