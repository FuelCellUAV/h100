#!/usr/bin/python3

# Validation Programme

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

# Includes
import time, argparse
from adc import adcpi
from tdiLoadbank import scheduler
from temperature import tmp102

def _parse_comandline():

    parser = argparse.ArgumentParser(description='Fuel Cell Controller by Simon Howroyd 2013')
    parser.add_argument('--out', type=str, default='', help='Save my data to USB stick')
    parser.add_argument('--profile', type=str, default='test.txt', help='input flight profile')
    return parser.parse_args()

# Get Current (internal)
def __getCurrent(Adc, channel):
#        current = abs(Adc.val[channel] * 1000 / 6.9) + 0.424 - 0.125
        current = abs(Adc.get(channel) * 1000 / 6.92) + 0.31 #inc divisor to lower error slope
        if current < 0.475: current = 0 # Account for opamp validity
        return current
 
# Get Voltage (internal)
def __getVoltage(Adc, channel):
#        voltage = abs(Adc.val[channel] * 1000 / 60.9559671563) + 0.029
        voltage = abs(Adc.get(channel) * 1000 / 47.5) - 5.74 #inc divisor to lower error slope
        return voltage

try:
    # Grab user args
    args = _parse_comandline()

    adc = adcpi.AdcPi2(12)
    temp = tmp102.Tmp102()
    
    load=scheduler.PowerScheduler(args.profile,'158.125.152.225',10001,'fuelcell')

    setpoint = 0
    setpointLast = -1

    input('Press enter to start')
    load.startTime = time.time()
    load.load('on')

    if args.out:
        file = open(('/media/usb/' + time.strftime('%y%m%d-%H%M%S') + '-validation-' + str(args.out) + '.tsv'),'w')

    while setpoint >= 0:
        setpoint = load.findNow()
        if setpoint != setpointLast and setpoint >=0:
            setpointLast = setpoint
            load.constantCurrent(str(setpoint))
        ci = load.constantCurrent()
        voltage = load.voltage()
        current = load.current()
        power = load.power()
    
        print('ci\t%.3f'% load.constantCurrent(), end='\t')
        print('v\t%.3f' % load.voltage(), end='\t')
        print('i\t%.3f' % load.current(), end='\t')
        print('p\t%.3f' % load.power(), end='\t')
        print()

        if args.out:
            file.write(str(time.time()) + '\t' + str(time.time()-load.startTime) + '\t')
            file.write('ci'+'\t'+str(load.constantCurrent())+'\t')
            file.write('v'+'\t'+str(load.voltage())+'\t')
            file.write('i'+'\t'+str(load.current())+'\t')
            file.write('p'+'\t'+str(load.power())+'\t')
            file.write('\n')
finally:
    # End
    file.close()
    load.constantCurrent('0')
    load.load('off')
    print('End of test.')


