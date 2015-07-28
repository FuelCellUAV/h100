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

# Import libraries
import argparse, sys, time, select
from display import h100Display
from h100Controller import H100
from switch import switch
from tdiLoadbank import loadbank
from scheduler import scheduler
from esc import esc
from timer import timer


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

# Function to write list data
def _writer(function, data):
    if type(data) is float:
        try:
            function("{0:.1f}".format(data) + '\t', end='')
        except (ValueError, TypeError):  # Not a print function
            function(str(data) + '\t')
    else: # Assume type(data) is str:
        try:
            function(data + '\t', end='')
        except (ValueError, TypeError):  # Not a print function
            function(str(data) + '\t')

    return data

# Function to print the header
def _display_header(destination):
    header = ("\n\n\n"
              + "Hybrid Powertrain Controller \n"
              + "with PEMFC Control \n"
              + "for the Horizon H-100 Fuel Cell \n"
              + "(c) Simon Howroyd and Jason James 2014 \n"
              + "Loughborough University \n"
              + "\n"
              + "This program is distributed in the hope that it will be useful, \n"
              + "but WITHOUT ANY WARRANTY; without even the implied warranty of \n"
              + "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the \n"
              + "GNU General Public License for more details. \n\n"
              + str(time.asctime())
              + "\n\n")
    
    # Write the data to destination
    _writer(destination, header),

    # Return the data
    return header

# Function to print the time
def _print_time(my_time, destination, verbose=False):
    # Get the time data
    if verbose:
        delta = [
            "Epoch:",    time.time(),
            "Duration:", time.time() - timeStart,
            "dt:",       my_time.delta,
        ]
    else:
        delta = [
            time.time(),
            time.time() - timeStart,
            my_time.delta,
        ]

    # Write the data to destination
    for cell in delta:
        _writer(destination, cell)

    # Return the data
    return delta

# Function to print the state
def _print_state(h100, destination, verbose=False):
    # Get the state from the controller
    if verbose:
        state = h100.state
    else:
        # Convert state to code for Matlab compatibility
        if "off" in h100.state:
            state = 1
        elif "startup" in h100.state: 
            state = 2
        elif "on" in h100.state:
            state = 3
        elif "shutdown" in h100.state:
            state = 4
        elif "error" in h100.state:
            state = -1
        else:
            state = 999

    # Write the data to destination
    _writer(destination, state),

    # Return the data
    return state

# Function to print the electrical data
def _print_electric(h100, load, destination, verbose=False):
    # Get the data from the controller
    if verbose:
        electric = [
            "V_fc_h:", h100.voltageHybrid[0], # FC output
            "V_fc:",   h100.voltage[0],
            "I_fc_h:", h100.currentHybrid[0],
            "I_fc:",   h100.current[0],
#            h100.power[0],

            "V_b_h:",  h100.voltageHybrid[1], # Battery output
            "V_b:",    h100.voltage[1],
            "I_b_h:",  h100.currentHybrid[1],
            "I_b:",    h100.current[1],
#            h100.power[1],

            "V_out_h:",h100.voltageHybrid[2], # System output
            "V_out:",  h100.voltage[2],
            "I_out_h:",h100.currentHybrid[2],
            "I_out:",  h100.current[2],
#            h100.power[2]
            ]
    else:
        electric = [
            h100.voltageHybrid[0], # FC output
            h100.voltage[0],
            h100.currentHybrid[0],
            h100.current[0],
#            h100.power[0],

            h100.voltageHybrid[1], # Battery output
            h100.voltage[1],
            h100.currentHybrid[1],
            h100.current[1],
#            h100.power[1],

            h100.voltageHybrid[2], # System output
            h100.voltage[2],
            h100.currentHybrid[2],
            h100.current[2],
#            h100.power[2]
            ]

    # If there is a digital loadbank connected get that data
    if load:
        if verbose:
            mode_code = load.mode.split()[0] + load.mode.split()[1]

            # Add the load data to the controller data
            electric = electric + ["Mode:",  mode_code,
                                   "V_load:", load.voltage,
                                   "I_load:", load.current,
                                   "P_load:", load.power]
        else:
            # Convert mode to a code for Matlab compatibility
            if "CURRENT" in load.mode:
                mode_code = "1 " + load.mode.split()[1]
            elif "VOLTAGE" in load.mode:
                mode_code = "2 " + load.mode.split()[1]
            elif "POWER" in load.mode:
                mode_code = "3 " + load.mode.split()[1]
            else:
                mode_code = 999

            # Add the load data to the controller data
            electric = electric + [mode_code,
                                   load.voltage,
                                   load.current,
                                   load.power]
    
    # Write the data to destination
    for cell in electric:
        _writer(destination, cell)

    # Return the data
    return electric

# Function to print the electrical data
def _print_voltage(h100, load, destination, verbose=False):
    # Get the data from the controller
    if verbose:
        voltage = [
            "V_fc_h:",  h100.voltageHybrid[0], # FC output
            "V_fc:",    h100.voltage[0],
            "V_b_h:",   h100.voltageHybrid[1],
            "V_b:",     h100.voltage[1],
            "V_out_h:", h100.voltageHybrid[2],
            "V_out:",   h100.voltage[2],
            ]
    else:
            voltage = [
                h100.voltageHybrid[0], # FC output
                h100.voltage[0],

                h100.voltageHybrid[1], # Battery output
                h100.voltage[1],

                h100.voltageHybrid[2], # System output
                h100.voltage[2],
                ]

    # If there is a digital loadbank connected get that data
    if load:
        # Add the load data to the controller data
        voltage = voltage + ["V_load:", load.voltage]
    
    # Write the data to destination
    for cell in voltage:
        _writer(destination, cell)

    # Return the data
    return voltage

# Function to print the electrical data
def _print_current(h100, load, destination, verbose=False):
    # Get the data from the controller
    if verbose:
        current = [
            "I_fc_h:",  h100.currentHybrid[0], # FC output
            "I_fc:",    h100.current[0],
            "I_b_h:",   h100.currentHybrid[1],
            "I_b:",     h100.current[1],
            "I_out_h:", h100.currentHybrid[2],
            "I_out:",   h100.current[2],
            ]
    else:
        current = [
                h100.currentHybrid[0], # FC output
                h100.current[0],

                h100.currentHybrid[1], # Battery output
                h100.current[1],

                h100.currentHybrid[2], # System output
                h100.current[2],
                ]

    # If there is a digital loadbank connected get that data
    if load:
        # Add the load data to the controller data
        current = current + ["I_load:", load.current]
    
    # Write the data to destination
    for cell in current:
        _writer(destination, cell)

    # Return the data
    return current

# Function to print the energy data
def _print_energy(h100, destination, verbose=False):
    
    energy = h100.energy

    # Write the data to destination
    for cell in energy:
        _writer(destination, cell)
            
    # Return the data
    return energy

# Function to print the temperature
def _print_temperature(h100, destination, verbose=False):
    # Get the data from the controller
    if verbose:
        temperature = ["T_h0:", h100.temperature[0],
                       "T_h1:", h100.temperature[1],
                       "T_0:",  h100.temperature[2],
                       "T_1:",  h100.temperature[3],
                       "T_2:",  h100.temperature[4],
                       "T_3:",  h100.temperature[5]]
    else:
        temperature = [h100.temperature[0],
                       h100.temperature[1],
                       h100.temperature[2],
                       h100.temperature[3],
                       h100.temperature[4],
                       h100.temperature[5]]

    # Write the data to destination
    for cell in temperature:
        _writer(destination, cell)

    # Return the data
    return temperature

# Function to print the purge data
def _print_purge(h100, destination, verbose=False):
    # Get the data from the controller
    if verbose:
        purge = ["MFC_flow:", h100.flow_rate,
                 "MFC_mol:",  h100.flow_moles,
                 "Pg_freq:",  h100.purge_frequency,
                 "Pg_t:",     h100.purge_time]
    else:
        purge = [h100.flow_rate,
                 h100.flow_moles,
                 h100.purge_frequency,
                 h100.purge_time]
             
    # Write the data to destination
    for cell in purge:
        _writer(destination, cell)

    # Return the data
    return purge
    
# Function to print the throttle
def _print_throttle(motor, destination):
    # Get the throttle from the motor controller
    throttle = motor.throttle

    # Write the data to destination
    _writer(destination, throttle)

    # Return the data
    return throttle

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

# Funtion to moitor performance of individual functions
def _performance_monitor(is_active, performance_timer, function_name):
    if is_active:
        # Calculate dt
        dt = int((time.time()-performance_timer) * 1000000.0) # Microseconds
        
        # Display the time taken to run the function
        print(function_name + '\t' + str(dt) + 'us')
        
        # Update the performance monitor timer
        performance_timer=time.time()
                
        return performance_timer   

# Shutdown routine        
def _shutdown(motor, h100, load, log, display):
    try:
        print("\nShutting down...")

        # Set motor throttle to zero
        motor.throttle = 0
        print('...Throttle set to {:d}'.format(motor.throttle))
    
        # Shutdown loadbank
        if load:
            print('...Loadbank disconnected')
            if load.shutdown(): print('Done\n')
        
        # Shutdown fuel cell
        h100.shutdown()
    
        # Shutdown datalog
        if log:
            print('...Datalogger closed')
            if log.close(): print('Done\n')
        
        # Shutdown LED display
        if display:
            display.on = False
            print('...Display off')

    except KeyboardInterrupt:        
        if input("Force close? [y/n]: ") is "y":
            print("FORCED CLOSE. TURN OFF DEVICES MANUALLY!")
            return
        else:
            _shutdown(motor, h100, load, log, display) # RECURSION

    # End
    print('Programme successfully exited and closed down\n\n')


# Main run function
if __name__ == "__main__":
    try:
        ## Command line arguments
        # Get user arguments from command line
        args = _parse_commandline()
        
        # If user asked for a logfile then open this
        if args.out:
            log = open(("/media/usb/" + time.strftime("%y%m%d-%H%M%S") + "-controller-" + args.out + ".tsv"), 'w')
            
        # Otherwise open nothing to prevent errors
        else:
            log = open("/dev/null", 'w')
        
        ## Initialise classes
        # Initialise controller
        h100 = H100(args.purge)
        
        # Initialise LED display
        display = h100Display.FuelCellDisplay()
        
        # If we cannot connect to the display, make the variable blank
        if display.connect() is -1:
            display = ''
            
        # Otherwise turn it on
        else:
            display.on = True
        
        # Initialise Digital loadbank
        load = loadbank.TdiLoadbank('158.125.152.225', 10001, 'fuelcell')
        
        # If we cannot connect to the loadbank, make the variable blank
        if load.connect() == 0:
            load = ''
            
        # Otherwise zero it and set safety limits
        else:
            print("Setting up loadbank...")
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
            load.voltage_minimum = "1.2" # 5.0
        
        # Initialise profile scheduler if argued
        if args.profile:
            profile = scheduler.Scheduler(args.profile)
            
            # If a loadbank is connected then define this as the output
            if load:
                output = "loadbank"
                
            # Otherwise assume a motor is connected via an ESC
            else:
                output = "esc"
                
        # Otherwise make the variable blank
        else:
            profile = ''
        
        # Initiaise the ESC
        motor = esc.esc()
        
        # Zero the throttle for safety
        motor.throttle = 0
        
        # Start timers
        my_time = timer.My_Time()
        timeStart = time.time() # todo
        
        # Print the header to the screen
        _display_header(print)
        
        # If there is an LED screen conencted...
        if display:
            
            # Set the fuel cell name
            display.name = "H100"
        
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
                        h100.state = 'on'
                        load.current_constant = str(0.01)
                        load.load = True
                        flag = True
                    else:
                        if load.voltage < (args.auto - 0.02):
                            load.current_constant = str(float(load.current_constant) - 0.01)
                        elif load.voltage > (args.auto + 0.02):
                            load.current_constant = str(float(load.current_constant) + 0.01)


                ## Handle the background processes
                # Run the fuel cell controller
                h100.run()
        
                # Update the performance monitor timer
                performance_timer = _performance_monitor(args.timer, performance_timer, H100.__name__)
                
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
                            if "VOLTAGE" in mode:
                                load.voltage_constant = str(setpoint)
                            elif "CURRENT" in mode:
                                load.current_constant = str(setpoint)
                            elif "POWER" in mode:
                                load.power_constant = str(setpoint)
                                
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
                            _print_state(h100, print, True)
                        elif request[0].startswith("elec?"):
                            _print_electric(h100, load, print, True)
                        elif request[0].startswith("v?"):
                            _print_voltage(h100, load, print, True)
                        elif request[0].startswith("i?"):
                            _print_current(h100, load, print, True)
                        elif request[0].startswith("energy?"):
                            _print_energy(h100, print, True)
                        elif request[0].startswith("temp?"):
                            _print_temperature(h100, print, True)
                        elif request[0].startswith("purg?"):
                            _print_purge(h100, print, True)
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
                            h100.state = _new_state
                        elif request[0].startswith("fly"):
                            profile.running = request[1]
                        elif request[0].startswith("off"):
                            load.current_constant = str(0.0)
                            load.load = False
                            h100.state = "off"
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
                state = _print_state(h100, log.write)
                
                # Send state to LED display if connected
                if display:
                    display.state = state
        
                # Update the performance monitor timer
                performance_timer = _performance_monitor(args.timer, performance_timer, "log_state")
        
                # Log electrical data
                electric = _print_electric(h100, load, log.write)
                
                # Send electrical data to LED display if connected
                if display:
                    display.voltage = electric[0]
                    display.current = electric[1]
                    display.power = electric[2]
        
                # Update the performance monitor timer
                performance_timer = _performance_monitor(args.timer, performance_timer, "log_electrical")
        
                # Log energy data
                _print_energy(h100, log.write)
        
                # Update the performance monitor timer
                performance_timer = _performance_monitor(args.timer, performance_timer, "energy")
        
                # Log temperature data
                temp = _print_temperature(h100, log.write)
                
                # Send temperature data to LED display if connected
                if display:
                    display.temperature = max(temp)
        
                # Update the performance monitor timer
                performance_timer = _performance_monitor(args.timer, performance_timer, "log_temp")
        
                # Log purge controller data
                _print_purge(h100, log.write)
        
                # Update the performance monitor timer
                performance_timer = _performance_monitor(args.timer, performance_timer, "log_purge")
        
                # Log a new line, end of this timestep
                if log:
                    log.write("\n")
        
                # If verbose is argued then print all data to screen
                if args.verbose and not args.timer:
                    _print_time(my_time, print)
                    _print_state(h100, print)
                    _print_electric(h100, load, print)
                    _print_energy(h100, print)
                    _print_temperature(h100, print)
                    _print_purge(h100, print)
                    print()
        
        # Do the folowing it code crashes or keyboard exception is raised (Ctrl+C)
        finally:
            # Code crashed
            pass
    
    except KeyboardInterrupt:
        _shutdown(motor, h100, load, log, display)
        
    #######
    # End #
    #######
