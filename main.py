#!/usr/bin/python3

# Hybrid Powertrain Controller

# Copyright (C) 2015  Simon Howroyd
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

import argparse, os, time
from pragma4Controller import Fuelcell
from timer import timer
from tdiLoadbank import loadbank
from scheduler import scheduler
from esc import esc
from display import h100Display

# Inspect user input arguments
def _parse_commandline():
    # Define the parser
    parser = argparse.ArgumentParser(description='Fuel Cell Controller by Simon Howroyd 2014')

    # Define aguments
    parser.add_argument('--out', type=str, default='', help='Save my data to USB stick')
    parser.add_argument('--purge', type=str, default='horizon', help='Change purge controller')
    parser.add_argument('--verbose', type=int, default=0, help='Print log to screen')
    parser.add_argument('--profile', type=str, default='', help='Name of flight profile file')
    parser.add_argument('--timer', type=int, default=0, help='Performance monitor timer')
    parser.add_argument('--auto', type=float, default=0.0, help='Auto voltage hold')

    # Return what was argued
    return parser.parse_args()


def _open_logfile(args):
    # If user asked for a logfile then open this
    if args.out:
        print("Setting up logfile...",end="")
        return open(("/media/usb/" + time.strftime("%y%m%d-%H%M%S") + "-controller-" + args + ".tsv"), 'w')    # Otherwise open nothing to prevent errors
        print("done")
    else:
        return open("/dev/null", 'w')

def _start_display(h100Display):
    # Initialise LED display
    display = h100Display.FuelCellDisplay()
    
    # If we cannot connect to the display, make the variable blank
    if display.connect() is -1:
        display = ''      
    # Otherwise turn it on
    else:
        print("Setting up LED display...",end="")
        display.on = True
        # Set the fuel cell name
        display.name = "Prg4"
        print("done")

    return display
    
def _start_loadbank(loadbank):
    # Initialise Digital loadbank
    load = loadbank.TdiLoadbank('158.125.152.225', 10001, 'fuelcell')

    # If we cannot connect to the loadbank, make the variable blank
    if load.connect() == 0:
        load = ''
    # Otherwise zero it and set safety limits
    else:
        print("Setting up loadbank...",end="")
        mysleep = 0.4
        load.zero()
        time.sleep(mysleep)
        load.mode = "CURRENT"
        time.sleep(mysleep)
        load.range = "9" # 4
        time.sleep(mysleep)
        load.current_limit = "15.0" # 30.0
        time.sleep(mysleep)
        load.voltage_limit = "4.5" # 35.0
        time.sleep(mysleep)
        load.voltage_minimum = "0.01"#"1.2" # 5.0
        print("done")

def _start_scheduler(scheduler, args):
    # Initialise profile scheduler if argued
    if args:
        profile = scheduler.Scheduler(args)
        
        # If a loadbank is connected then define this as the output
        if load:
            output = "loadbank"
        # Otherwise assume a motor is connected via an ESC
        else:
            output = "esc"

        return profile, output
                
    # Otherwise make the variable blank
    else:
        return '', ''

def _performance_monitor(is_active, performance_timer, function_name):
    if is_active:
        dt = int((time.time()-performance_timer)*1000000.0) # microseconds
        print(function_name + '\t' + str(dt) + 'us')
        return time.time()

# Function to read user input while running (stdin)
def _reader():
    # Get data from screen
    __inputlist = [sys.stdin]

    # Parse the typed in characters
    while __inputlist:
        __ready = select.select(__inputlist, [], [], 0.001)[0]

        # If no data has been typed then return blank
        if not __ready:
            return ''
            
        # Otherwise parse line
        else:
            # Read the line
            for __file in __ready:
                __line = __file.readline()

            # If there is nothing it is the end of the line
            if not __line:
               __inputlist.remove(__file)
               
            # Otherwise return line with no whitespace and all letters in lowercase
            elif __line.rstrip():  # optional: skipping empty lines
                return __line.lower().strip()
                
    # If we get here something went wrong so return blank
    return ''

# Main run function
if __name__ == "__main__":
    try:
        ## Command line arguments
        # Get user arguments from command line
        args = _parse_commandline()
        
        # If user asked for a logfile then open this
        log = _open_logfile(args)

        # Initialise Digital loadbank
        load = _start_loadbank(loadbank)

        # Clear Screen
        os.system('cls' if os.name == 'nt' else 'clear')

        
        ## Initialise classes
        # Initialise controller
        fuelcell = Fuelcell(args.purge)
        
        # Initialise LED display
        display = _start_display(h100Display)
        
        # Initialise profile scheduler if argued
        profile, output = _start_scheduler(scheduler, args.profile)
        
        # Initiaise the ESC
        motor = esc.esc()
        
        # Zero the throttle for safety
        motor.throttle = 0
        
        # Start timers
        my_time = timer.My_Time()
#        my_time.local
        
        # Print the header to the screen
        #_display_header(print)
        
        # Display a list of available user commands
        print("Type command: [time, throttle, fc, elec, v, i, energy, temp, purg, fly] ")
        
        # Start a timer
        performance_timer = time.time()

        flag=False
        
        # Try to run the main code loop
        try:
            while True:
                
                if args.auto:
                    if not flag:
                        fuelcell.state = 'on'
                        load.current_constant = "0.01"
                        load.load = True
                        flag = True
                    else:
                       if load.load:  
                            # End time & routine
                            #if (time.time() - timeStart) > (60*30*5): raise KeyboardInterrupt

                            # Purge strategy controller
                            #if   (time.time() - timeStart) < (60*20): h100.change_purge = "half"
                            #elif (time.time() - timeStart) < (60*20*2): h100.change_purge = "horizon"
                            #elif (time.time() - timeStart) < (60*20*3): h100.change_purge = "double"
                            #elif (time.time() - timeStart) < (60*20*4): h100.change_purge = "horizon"
                            #elif (time.time() - timeStart) < (60*20*5): h100.change_purge = "half"
   
                            controller_current = 0

                            # Voltage hold controller
                            if load.voltage < (args.auto - 0.01):
                                controller_current = float(load.current_constant) - 0.001
                            elif load.voltage > (args.auto + 0.01):
                                controller_current = float(load.current_constant) + 0.001
                            #elif load.voltage < (args.auto - 0.01):
                            #    load.current_constant = str(float(load.current_constant) - 0.01)
                            #elif load.voltage > (args.auto + 0.01):
                            #    load.current_constant = str(float(load.current_constant) + 0.01)
                            if controller_current < 0.0: controller_current = 0.0
                            load.current_constant = str(controller_current)


                ## Handle the background processes
                # Run the fuel cell controller
                fuelcell.run()
        
                # Update the performance monitor timer
                performance_timer = _performance_monitor(args.timer, performance_timer, Fuelcell.__name__)
                
                # Run the timer TODO
                my_time.run()
        
                # Update the performance monitor timer
                performance_timer = _performance_monitor(args.timer, performance_timer, timer.My_Time.__name__)
                
                # If we are running a scheduled profile...
                if profile:
                    
                    # Get the programmed setpoint
                    setpoint = profile.run()
                    
                    # If the output is the digital loadbank...
                    if "loadbank" in output and load:
                        
                        # and the setpoint is not in an error mode...
                        if setpoint >= 0:
                            
                            # Turn the loadbank on
                            load.load = True
                            
                            # Set the type of electrical profile we are running
                            mode = load.mode
                            
                            # Set the setpoint for the electrical profile for now
#                            if "VOLTAGE" in mode:
#                                load.voltage_constant = str(setpoint)
#                            elif "CURRENT" in mode:
#                                load.current_constant = str(setpoint)
#                            elif "POWER" in mode:
#                                load.power_constant = str(setpoint)
                            args.auto = float(setpoint)
                                
                        # Setpoint is in an error mode (eg profile finished) so turn off
                        else:
                            load.load = False
                            
                    # Otherwise assume a throttle profile, send this to the motor
                    else:
                        motor.throttle = setpoint
        
                # Update the performance monitor timer
                performance_timer = _performance_monitor(args.timer, performance_timer, scheduler.Scheduler.__name__)
        
                # If there is a loadbank connected, update the sensor values
                if load:
                    load.update()
        
                # Update the performance monitor timer
                performance_timer = _performance_monitor(args.timer, performance_timer, loadbank.TdiLoadbank.__name__)
        
                ## Handle the user interface
                # Read typed in user data on the screen
                request = _reader()
                
                # If something was typed in...
                if request:
                    
                    # Split the argument from the value
                    request = request.split(' ')
                    
                    # Determine the number of pieces of information
                    req_len = len(request)
                    
                    # Strip away any whitespace
                    for x in range(req_len):
                        request[x] = request[x].strip()
        
                    # If only one piece of information, it is a request for data
                    if req_len is 1:
                        if request[0].startswith("time?"):
                            _print_time(my_time, print, True)
                        elif request[0].startswith("throttle?"):
                            _print_throttle(motor, print, True)
                        elif request[0].startswith("fc?"):
                            _print_state(fuelcell, print, True)
                        elif request[0].startswith("elec?"):
                            _print_electric(fuelcell, load, print, True)
                        elif request[0].startswith("v?"):
                            _print_voltage(fuelcell, load, print, True)
                        elif request[0].startswith("i?"):
                            _print_current(fuelcell, load, print, True)
                        elif request[0].startswith("energy?"):
                            _print_energy(fuelcell, print, True)
                        elif request[0].startswith("temp?"):
                            _print_temperature(fuelcell, print, True)
                        elif request[0].startswith("purg?"):
                            _print_purge(fuelcell, print, True)
                        elif request[0].startswith("fly?"):
                            if profile and profile.running:
                                print("Currently flying")
                            else:
                                print("In the hangar")
        
                    # If there are two pieces of information it is a command to change something
                    elif req_len is 2:
                        if request[0].startswith("fc"):
                            _new_state = request[1]
                            print('Changing state to', _new_state)
                            fuelcell.state = _new_state
                        elif request[0].startswith("fly"):
                            profile.running = request[1]
                        elif request[0].startswith("off"):
                            load.current_constant = str(0.0)
                            load.load = False
                            fuelcell.state = "off"
                        elif request[0].startswith("i"):
                            load.current_constant = str(request[1])
                        elif request[0].startswith("v"):
                            if args.auto > 0.0:
                                args.auto = float(request[1])
                            else:
                                print("Don't understand!")
                        elif request[0].startswith("load"):
                            if request[1].startswith("on"):
                                load.load = True
                            else:
                                load.load = False
                        elif request[0].startswith("throttle"):
                            if request[1].startswith("calibration"):
                                motor.calibration()
                            else:
                                motor.throttle = request[1]
        
                    # Print a new line to the screen
                    print()
        
                # Update the performance monitor timer
                performance_timer = _performance_monitor(args.timer, performance_timer, "UI")
        
                ## Handle the logfile
                # Log time
                _print_time(my_time, log.write)
        
                # Update the performance monitor timer
                performance_timer = _performance_monitor(args.timer, performance_timer, "log_time")
        
                # Log state
                state = _print_state(fuelcell, log.write)
                
                # Send state to LED display if connected
                if display:
                    display.state = state
        
                # Update the performance monitor timer
                performance_timer = _performance_monitor(args.timer, performance_timer, "log_state")
        
                # Log electrical data
                electric = _print_electric(fuelcell, load, log.write)
                
                # Send electrical data to LED display if connected
                if display:
                    display.voltage = electric[0]
                    display.current = electric[1]
                    display.power = electric[2]
        
                # Update the performance monitor timer
                performance_timer = _performance_monitor(args.timer, performance_timer, "log_electrical")
        
                # Log energy data
                _print_energy(fuelcell, log.write)
        
                # Update the performance monitor timer
                performance_timer = _performance_monitor(args.timer, performance_timer, "energy")
        
                # Log temperature data
                temp = _print_temperature(fuelcell, log.write)
                
                # Send temperature data to LED display if connected
                if display:
                    display.temperature = max(temp)
        
                # Update the performance monitor timer
                performance_timer = _performance_monitor(args.timer, performance_timer, "log_temp")
        
                # Log purge controller data
                _print_purge(fuelcell, log.write)
        
                # Update the performance monitor timer
                performance_timer = _performance_monitor(args.timer, performance_timer, "log_purge")
        
                # Log a new line, end of this timestep
                if log:
                    log.write("\n")
        
                # If verbose is argued then print all data to screen
                if args.verbose and not args.timer:
                    _print_time(my_time, print)
                    _print_state(fuelcell, print)
                    _print_electric(fuelcell, load, print)
                    _print_energy(fuelcell, print)
                    _print_temperature(fuelcell, print)
                    _print_purge(fuelcell, print)
                    print()
        
        # Do the folowing it code crashes or keyboard exception is raised (Ctrl+C)
        finally:
            # Code crashed
            pass
    
    except KeyboardInterrupt:
        print("Shutdon initiated after %.0f sec" % (time.time() - timeStart))
        _shutdown(motor, fuelcell, load, log, display)
        
    #######
    # End #
    #######



#<!------------ SUPER MARIO BROS. 30TH ---------------
#
#
#               \\\\\\\\\\\\\\\
#               \\\\\\\\\\\\\\\
#            \\\\\\\\\\\\\\\\\\\\\\\\\\\
#            \\\\\\\\\\\\\\\\\\\\\\\\\\\
#            #########++++++###+++
#            #########++++++###+++
#         ###+++###+++++++++###++++++
#         ###+++###+++++++++###++++++
#         ###+++######+++++++++###+++++++++
#         ###+++######+++++++++###+++++++++
#         ######++++++++++++###############
#         ######++++++++++++###############
#               +++++++++++++++++++++
#               +++++++++++++++++++++
#            ######\\\#########
#            ######\\\#########
#         #########\\\######\\\#########
#         #########\\\######\\\#########
#      ############\\\\\\\\\\\\############
#      ############\\\\\\\\\\\\############
#      ++++++###\\\+++\\\\\\+++\\\###++++++
#      ++++++###\\\+++\\\\\\+++\\\###++++++
#      +++++++++\\\\\\\\\\\\\\\\\\+++++++++
#      +++++++++\\\\\\\\\\\\\\\\\\+++++++++
#      ++++++\\\\\\\\\\\\\\\\\\\\\\\\++++++
#      ++++++\\\\\\\\\\\\\\\\\\\\\\\\++++++
#            \\\\\\\\\      \\\\\\\\\
#            \\\\\\\\\      \\\\\\\\\
#         #########            #########
#         #########            #########
#
#---------------       THANK YOU!      -------------->
