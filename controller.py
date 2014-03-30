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
import argparse, sys, time, select

from display import h100Display
from purge import pid
from h100Controller import H100
from switch import switch
from tdiLoadbank import loadbank, scheduler

def _parse_comandline():

    parser = argparse.ArgumentParser(description='Fuel Cell Controller by Simon Howroyd 2013')
    parser.add_argument('--out', type=str, default='', help='Save my data to USB stick')
    parser.add_argument('--purgeController', type=int, default=0, help='Set to 1 for purge controller on')
    parser.add_argument('--purgeTime'  	,type=float, 	default=0.5,	help='How long to purge for in seconds')
    parser.add_argument('--purgeFreq'  	,type=float, 	default=30,	help='Time between purges in seconds')
    parser.add_argument('--display'  	,type=int, 	default=1,	help='Piface CAD (1 is on, 0 is off)')
    parser.add_argument('--load'  	,type=int, 	default=0,	help='Load (1 is on, 0 is off)')
    parser.add_argument('--profile'  	,type=str, 	default='',	help='Name of flight profile file')

    return parser.parse_args()

def _display_header(*destination):
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

    for write in destination: _writer(write, header),
    return header
    #display.setName('H100')

def _print_state(h100, *destination):
    state = h100.getState()
    for write in destination: _writer(write, state),
    return state
    #print(state, end='\t')
    #if logfile: logfile.write(state+'\t')
    #display.setState(state)

def _print_electric(h100, load='', *destination):
    electric = []
    electric.append(h100.getVoltage()[0])
    electric.append(h100.getCurrent()[0])
    electric.append(h100.getPower()[0])

    if load:
        electric.append(load.mode())
        electric.append(load.voltage())
        electric.append(load.current())
        electric.append(load.power())

    for write in destination:
        for cell in electric:      
            _writer(write, cell)

    return electric
    #display.setVolts(voltage)
    #display.setAmps(current)

def _print_temperature(h100, *destination):
    temp = []
    for x in range(4):
        temp.append(h100.getTemperature()[x])

    for write in destination:
        for cell in temp:      
            _writer(write, cell)
    return temp
    #display.setTemp(max(h100.getTemperature()))

def _print_purge(h100, *destination):
    purge = []
    purge.append(h100.getPurgeFrequency())
    purge.append(h100.getPurgeTime())

    for write in destination:
        for cell in purge:
            _writer(write, cell)
    return purge

def _print_time(timeStart, *destination):
    mytime = []
    mytime.append(time.time())
    mytime.append(time.time() - timeStart)
    
    for write in destination:
        for cell in mytime:
            _writer(write, cell)
    return mytime

def _writer(function, data):
    try:
        function(str(data)+'\t', end='')
    except TypeError: # Not a print function
        function(str(data)+'\t')
    return data

def _reader():
    inputList = [sys.stdin]
    while inputList:
        ready = select.select(inputList, [], [], 0.001)[0]
        if not ready:
            return '' # No user input received
        else:
            for file in ready:
                line = file.readline()
            if not line: # EOF, remove file from input list
                inputList.remove(file)
            elif line.rstrip(): # optional: skipping empty lines
                return line.lower()
    return ''

def _profile(profile, isRunning):
    if isRunning:
        # Do running
        isRunning = profile.main(isRunning)
    else:
        pass
    
    return isRunning

if __name__ == "__main__":

    #########
    # Setup #
    #########

    # Grab user args
    args = _parse_comandline()

    ## Look at user arguments
    # Logfile
    if args.out:
        log = open(('/media/usb0/' + time.strftime('%y%m%d-%H%M%S') + '-controller-' + args.out + '.tsv'),'w')
    else:
        log = open("/dev/null",'w')
    # Purge Controller
    if args.purgeController:
        purge = pid.Pid(10, 1, 1)
    else:
        purge = 0

    ## Initialise classes
    # Initialise controller class
    h100 = H100(purgeControl=purge, purgeFreq=args.purgeFreq, purgeTime=args.purgeTime)
    # Initialise display class
    display = h100Display.FuelCellDisplay()
    display._isOn = args.display
    # Initialise loadbank class
    if args.profile:
        profile = scheduler.PowerScheduler(args.profile, args.out, '158.125.152.225', 10001, 'fuelcell')
    else: profile = ''
    if args.load:
        if profile: load = profile
        else:
            load = loadbank.TdiLoadbank('158.125.152.225', 10001, 'fuelcell')
    else:
        load = ''

    # Record start time
    timeStart = time.time()

    #
    _isRunning = 0

    ########
    # Main #
    ########

    _display_header(print)
    print("Type command: [time, stat, elec, temp, purg] ")

    try:
        while True:
            h100.run()
            _isRunning = _profile(profile, _isRunning)

            # HANDLE USER REQUESTED DATA
            request = _reader()
            if 'time?' in request:
                _print_time(timeStart, print)
            elif 'stat?' in request:
                _print_state(h100, print)
            elif 'elec?' in request:
                _print_electric(h100, load, print)
            elif 'temp?' in request:
                _print_temperature(h100, print)
            elif 'purg?' in request:
                _print_purge(h100, print)
            elif 'fly' in request:
                _isRunning = 1
                
            if request: print()

            # LOG TIME
            _print_time(timeStart, log.write)

            # LOG STATE
            _print_state(h100, log.write)

            # LOG ELECTRIC
            _print_electric(h100, load, log.write)

            # LOG TEMPERATURE
            _print_temperature(h100, log.write)

            # LOG PURGE
            _print_purge(h100, log.write)

            # PRINT NEW LINE
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
