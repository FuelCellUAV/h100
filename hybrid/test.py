#!/usr/bin/env python3
# Written by Simon Howroyd 2015 for Loughborough University

# Test programme for the hybrid board

from hybrid import Hybrid
from time import sleep

def _get_elec(source):
    return ("Elec: "
        + 'f' + source.fc_voltage + '/' + source.fc_current_to_motor + ' '
        + 'b' + source.battery_voltage + '/' + source.battery_current + ' '
        + 'c' + source.charge_current + ' '
        + '>' + source.output_voltage + '/' + source.fc_current_to_motor)

def _get_chg(source):
    return ("Chg: "
        + source.charger_state + ' '
        + source.shutdown + ' '
        + 'i' + source.charger_info + ' '
        + 's' + source.cells + ' '
        + 'v' + source.charged_voltage + ' ')
        
  def _get_temp(source):
    return ("Tmp: "
        + source.t1 + ' '
        + source.t2 + ' ')
    
    
controller = Hybrid()

while True:
    controller.update()
    print(_get_elec(controller))
    print(_get_chg(controller))
    print(_get_tmp(controller))
    sleep(1)
    
