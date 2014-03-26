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
#from tdiLoadbank import loadbank
#from writer import MyWriter

def _parse_comandline():

    parser = argparse.ArgumentParser(description='Fuel Cell Controller by Simon Howroyd 2013')
    parser.add_argument('--out', help='Save my data to USB stick')
    parser.add_argument('--purgeController', type=int, default=0, help='Set to 1 for purge controller on')
    parser.add_argument('--purgeTime'  	,type=float, 	default=0.5,	help='How long to purge for in seconds')
    parser.add_argument('--purgeFreq'  	,type=float, 	default=30,	help='Time between purges in seconds')
    parser.add_argument('--display'  	,type=int, 	default=1,	help='Piface CAD')

    return parser.parse_args()

def _display_header(display, logfile=''):
    header = ("\n"
              + "Fuel Cell Controller \n"
              + "Horizon H-100 Stack \n"
              + "(c) Simon Howroyd 2014 \n"
              + "Loughborough University \n"
              + "\n"
              + "This program comes with ABSOLUTELY NO WARRANTY; for details type `show w'. \n"
              + "This is free software, and you are welcome to redistribute it, \n"
              + "under certain conditions; type `show c' for details.\n"
              + str(time.asctime())
              + "\n\n")

    print(header)
    if logfile: logfile.write(header)

    display.setName('H100')

def _print_state(h100, display, logfile=''):
    state = h100.getState()
    print(state, end='\t')
    if logfile: logfile.write(state+'\t')
    display.setState(state)

def _print_electric(h100, display, load, logfile=''):
    voltage = h100.getVoltage()[0]
    current = h100.getCurrent()[0]
    power   = h100.getPower()[0]

    print('v1', '\t', '%.1f' % voltage, end='\t')
#    print('v2', '\t', '%.3f' % load.voltage(), end='\t')
    print('a1', '\t', '%.1f' % current, end='\t')
#    print('a2', '\t', '%.3f' % load.current(), end='\t')
    print('w1', '\t', '%.1f' % power, end='\t')
#    print('p2', '\t', '%.3f' % load.power(), end='\t')
#    c = load.mode()
#    if 'VOLTAGE' in c:
#        print('cv', '\t', '%.3f' % load.constantVoltage(), end='\t')
#    elif 'CURRENT' in c:
#        print('cc', '\t', '%.3f' % load.constantCurrent(), end='\t')
#    elif 'POWER' in c:
#        print('cp', '\t', '%.3f' % load.constantPower(), end='\t')
#    else:
#        print('??', '\t', '0.0', end='\t')

    if logfile:
        logfile.write('v'+'\t'+str(voltage)+'\t')
        logfile.write('a'+'\t'+str(current)+'\t')
        logfile.write('w'+'\t'+str(power)+'\t')
        
    display.setVolts(voltage)
    display.setAmps(current)

def _print_temperature(h100, display, logfile=''):
    t = []

    for x in range(4):
        t.append(h100.getTemperature()[x])

    print('t', end='\t')
    for x in range(4):
        print('%.1f' % t[x], end='\t')

    if logfile:
        logfile.write('t'+'\t')
        for x in range(4):
            logfile.write(str(t[x])+'\t')

    display.setTemp(max(h100.getTemperature()))

def _print_purge(h100, logfile=''):
    pFreq = h100.getPurgeFrequency()
    pTime = h100.getPurgeTime()

    print('pf/pt', end='\t')
    print('%.1f' % pFreq, end='\t')
    print('%.1f' % pTime, end='\t')

    if logfile:
        logfile.write('pf/pt'+'\t')
        logfile.write(str(pFreq)+'\t'+str(pTime)+'\t')

def _print_time(timeStart, logfile=''):
    delta = time.time() - timeStart
    
    print('%.1f' % delta, end='\t')

    if logfile: log.write(str(time.time())+'\t')

if __name__ == "__main__":

    #########
    # Setup #
    #########

    # Grab user args
    args = _parse_comandline()

    # Look at user arguments
    if args.out:  # save to output file
        #writer = MyWriter(sys.stdout, ('/media/usb0/' + time.strftime('%y%m%d %H%M%S') + ' ' + args.out + '.tsv'))
        log = open(('/media/usb0/' + time.strftime('%y%m%d-%H%M%S') + '-controller-' + args.out + '.tsv'),'w')
    else:
        log = ''
        #writer = MyWriter(sys.stdout, ('/media/usb0/' + time.strftime('%y%m%d %H%M%S') + '.tsv'))
#    sys.stdout = writer

    if args.purgeController:
        purge = pid.Pid(10, 1, 1)
    else:
        purge = 0

    # Initialise controller class
    h100 = H100(purgeControl=purge, purgeFreq=args.purgeFreq, purgeTime=args.purgeTime)
    #h100.daemon = True

    # Initialise display class
    display = h100Display.FuelCellDisplay()
    display._isOn = args.display
#    display = h100Display.FuelCellDisplay(1, "PF Display")
#    display.daemon = True  # To ensure the process is killed on exit

    # Initialise loadbank class
#    load = loadbank.TdiLoadbank('158.125.152.225', 10001, 'fuelcell')
    load = 0

    timeStart = time.time()

    ########
    # Main #
    ########

    _display_header(display)

    try:

#        display.start()

        while True:
            h100.run()

            # PRINT TIME
            _print_time(timeStart, log)

            # PRINT STATE
            _print_state(h100, display, log)

            # PRINT ELECTRIC
            _print_electric(h100, display, load, log)

            # PRINT TEMPERATURE
            _print_temperature(h100, display, log)

            # PRINT PURGE
            _print_purge(h100, log)

            # PRINT NEW LINE
            print()
            if log: log.write("\n")

    # Programme Exit Code
    finally:
        h100.shutdown()
        if log: log.close()
        display.off()
        print('\n\n\nProgramme successfully exited and closed down\n\n')

    #######
    # End #
    #######
