#!/usr/bin/env python3
# Written by Simon Howroyd 2015 for Loughborough University

# Test programme for the hybrid board

from hybrid import Hybrid
from time import sleep
import argparse

# Inspect user input arguments
def _parse_commandline():
    # Define the parser
    parser = argparse.ArgumentParser(description='Hybrid Controller Tester by Simon Howroyd 2015')
    
    # Define aguments
    parser.add_argument('--iLim', type=float, default=0.0, help='Charger Current Limit')
    parser.add_argument('--cells', type=int, default=3, help='Battery Cells')
    parser.add_argument('--chem', type=float, default=4.1, help='Cell Charged Voltage')
    parser.add_argument('--h2', action='store_true', help='Turn H2 supply valve on')
    parser.add_argument('--fan', action='store_true', help='Turn fan on')
    parser.add_argument('--purge', action='store_true', help='Turn purge valve on')
    parser.add_argument('--aux1', action='store_true', help='Turn aux1 on')
    parser.add_argument('--aux2', action='store_true', help='Turn aux2 on')
    parser.add_argument('--off', action='store_false', help='Turn charger off')

    # Return what was argued
    return parser.parse_args()

def _get_elec(source):
    return ("Elec: "
        + 'f' + str(source.fc_voltage) + '/' + str(source.fc_current_to_motor) + ' '
        + 'b' + str(source.battery_voltage) + '/' + str(source.battery_current) + ' '
        + 'c' + str(source.charge_current) + ' '
        + '>' + str(source.output_voltage) + '/' + str(source.fc_current_to_motor))

def _get_chg(source):
    return ("Chg: "
        + str(source.charger_state) + ' '
        + str(source.shutdown) + ' '
        + 'i' + str(source.charger_info) + ' '
        + 's' + str(source.cells) + ' '
        + 'v' + str(source.charged_voltage) + ' ')
        
def _get_temp(source):
    return ("Tmp: "
        + str(source.t1) + ' '
        + str(source.t2) + ' ')
    
    
controller = Hybrid()
args = _parse_commandline()

# Charger Setup
controller.shutdown = args.off
#if args.iLim is not controller.__charger.current:
#    controller.__charger.current = args.iLim
    
# Battery Setup
controller.cells = args.cells
controller.charged_voltage = args.chem
    
# Turn on/off switches
if args.h2: controller.h2_on()
else:       controller.h2_off()
if args.fan: controller.fan_on()
else:        controller.fan_off()
if args.purge: controller.purge_on()
else:          controller.purge_off()
#controller.__io.power4 = args.aux1
#controller.__io.power5 = args.aux2

while True:
    controller.update()
    print(_get_elec(controller))
    print(_get_chg(controller))
    print(_get_temp(controller))
    sleep(1)
    
