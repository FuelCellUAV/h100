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


def _parse_commandline():
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

def _print_state(h100, *destination):
    state = h100.state

    for write in destination: _writer(write, state),

    return state

def _print_electric(h100, load='', *destination):
    electric = [
        h100.voltage[0],
        h100.current[0],
        h100.power[0],
    ]

    if load:
        electric = electric + [
            load.mode(),
            load.voltage(),
            load.current(),
            load.power(),
        ]

    for write in destination:
        for cell in electric:
            _writer(write, cell)

    return electric

def _print_temperature(h100, *destination):
    temperature = [
        h100.temperature[0],
        h100.temperature[1],
        h100.temperature[2],
        h100.temperature[3],
    ]

    for write in destination:
        for cell in temperature:
            _writer(write, cell)

    return temperature


def _print_purge(h100, *destination):
    purge = [
        h100.purgefrequency,
        h100.purgetime,
    ]

    for write in destination:
        for cell in purge:
            _writer(write, cell)

    return purge

def _print_time(timeStart, *destination):
    delta = [
        time.time(),
        time.time() - timeStart,
    ]

    for write in destination:
        for cell in delta:
            _writer(write, cell)

    return delta

def _writer(function, data):
    try:
        function(str(data)+'\t', end='')
    except TypeError: # Not a print function
        function(str(data)+'\t')

    return data

def _reader():
    __inputlist = [sys.stdin]

    while __inputlist:
        __ready = select.select(__inputlist, [], [], 0.001)[0]

        if not __ready:
            return '' # No user input received

        else:
            for __file in __ready:
                __line = __file.readline()

            if not __line:  # EOF, remove file from input list
                __inputlist.remove(__file)
            elif __line.rstrip():  # optional: skipping empty lines
                return __line.lower().strip()

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
    args = _parse_commandline()

    ## Look at user arguments
    # Logfile
    if args.out:
        log = open(("/media/usb0/" + time.strftime("%y%m%d-%H%M%S") + "-controller-" + args.out + ".tsv"), 'w')
    else:
        log = open("/dev/null",'w')
    # Purge Controller
    if args.purgeController:
        purge = pid.Pid(10, 1, 1)
    else:
        purge = False

    ## Initialise classes
    # Initialise controller class
    h100 = H100(purgeControl=purge, purgeFreq=args.purgeFreq, purgeTime=args.purgeTime)
    # Initialise display class
    display = h100Display.FuelCellDisplay()
    display.on = True
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
    display.name = "H100"

    print("Type command: [time, stat, elec, temp, purg, fly] ")

    try:
        while True:
            h100.run()
            _isRunning = _profile(profile, _isRunning)

            # HANDLE USER REQUESTED DATA
            request = _reader()
            if request:
                request = request.split(' ')
                req_len = len(request)
                for x in range(req_len): request[x] = request[x].strip()

                if req_len is 1:
                    if   request[0].startswith("time?"):
                        _print_time(timeStart, print)
                    elif request[0].startswith("stat?"):
                        _print_state(h100, print)
                    elif request[0].startswith("elec?"):
                        _print_electric(h100, load, print)
                    elif request[0].startswith("temp?"):
                        _print_temperature(h100, print)
                    elif request[0].startswith("purg?"):
                        _print_purge(h100, print)
                    elif request[0].startswith("fly?"):
                        if _isRunning: print("Currently flying")
                        else: print("In the hangar")

                elif req_len is 2:
                    if   request[0].startswith("stat"):
                        _new_state = request[1]
                        print('Changing state to',_new_state,'...',end='')
                        h100.state = _new_state
                        if h100.state is _new_state:
                            print("done!")
                        else: print("failed")
                    elif request[0].startswith("fly"):
                        if int(request[1]) is 0 and _isRunning is 1:
                            _isRunning = 0
                            print("...landing")
                        elif int(request[1]) is 1 and _isRunning is 0:
                            _isRunning = 1
                            print("...taking off")

                print()


            # LOG TIME
            _print_time(timeStart, log.write)

            # LOG STATE
            display.state = _print_state(h100, log.write)
            
            # LOG ELECTRIC
            electric = _print_electric(h100, load, log.write)
            display.voltage = electric[0]
            display.current = electric[1]
            display.power = electric[2]

            # LOG TEMPERATURE
            temp = _print_temperature(h100, log.write)
            display.temperature = max(temp)

            # LOG PURGE
            _print_purge(h100, log.write)

            # PRINT NEW LINE
            if log: log.write("\n")


    # Programme Exit Code
    finally:
        h100.shutdown()
        if log: log.close()
        display.on = False
        print('\n\n\nProgramme successfully exited and closed down\n\n')

    #######
    # End #
    #######
