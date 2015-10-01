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
from pragma4Controller import Pragma4
from switch import switch
from tdiLoadbank import loadbank
from scheduler import scheduler
from esc import esc
from timer import timer
import os

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

