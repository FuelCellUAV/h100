#!/usr/bin/env python3
# Written by Simon Howroyd 2015 for Loughborough University

# Test programme for the hybrid board

from hybrid import Hybrid, Charge_Controller
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
    parser.add_argument('--on', action='store_true', help='Turn charger off')

    # Return what was argued
    return parser.parse_args()

def _get_elec(source):
    return ("Elec: "
        + 'f' + str(source.fc_voltage)[:7] + '/' + str(source.fc_current_to_motor)[:4] + ' '
        + 'b' + str(source.battery_voltage)[:4] + '/' + str(source.battery_current)[:4] + ' '
        + 'c' + str(source.charge_current)[:4] + ' '
        + '>' + str(source.output_voltage)[:7] + '/' + str(source.output_current)[:4])

def _get_chg(source):
    x = "Chg: "
    if source.charger_state: x += "ON! "
    else : x += "OFF! "
    if source.shutdown: x += "SHDN ("
    else : x += "( "
    if source.charger_info[0]: x += "LOBAT "
    if source.charger_info[1]: x += "ICL "
    if source.charger_info[2]: x += "ACP "
    if source.charger_info[3]: x += "FAULT "
    if source.charger_info[4]: x += "CHG "
    x += ") "
    if source.cells: x += "4cell "
    else: x += "3cell "
    x += (str(source.charged_voltage) + ' ')
    return x

    return ("Chg: "
        + str(source.charger_state) + ' '
        + str(source.shutdown) + ' '
        + 'i' + str(source.charger_info) + ' '
        + 's' + str(source.cells) + ' '
        + 'v' + str(source.charged_voltage) + ' ')
        
def _get_temp(source):
    return ("Tmp: "
        + str(source.t1)[:4] + ' '
        + str(source.t2)[:4] + ' ')
    
    
controller = Hybrid()
args = _parse_commandline()
pot = Charge_Controller()

# Charger Setup
controller.shutdown = args.on
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
#    pot.current = 0.0
    print(_get_temp(controller))
#    controller.h2_on()
#    controller.fan_on()
#    controller.purge_on()
#    sleep(1)
#    pot.current = 2.0
#    controller.h2_off()
#    controller.fan_off()
#    controller.purge_off()
    print('')
    sleep(1)

