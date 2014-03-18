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
import time
from adc import adcpi
from tdiLoadbank import scheduler

adc = adcpi.AdcPi2Daemon()
adc.daemon = True
adc.start()

load=scheduler.PowerScheduler('./tdiLoadbank/test2.txt','158.125.152.225',10001,'fuelcell')

setpoint = 0
setpointLast = -1

input('Press enter to start')
load.startTime = time.time()
load.load('on')

# Get Current (internal)
def __getCurrent(Adc, channel):
        current = ((abs(Adc.val[channel] * 1000 / 4.2882799485) + 0.6009) / 1.6046) - 0.145 ### 0.11 added
#        if current < 0.4: current = 0 # Account for opamp validity
        return current + 0.1

# Get Voltage (internal)
def __getVoltage(Adc, channel):
        voltage = (abs(Adc.val[channel] * 1000 / 60.9559671563) + 0.029) ### 0.015 added
        current = __getCurrent(Adc,0)
        if current>=0.5: voltage -= current*0.011 - 0.005
        #voltage = voltage + 0.01*__getCurrent(adc,0)
        return voltage

with open((load.filename.split('.')[0] + 'Results' + time.strftime('%y%m%d%H%M%S') + '.txt'),'w') as file:
    while setpoint >= 0:
        setpoint = load.findNow()
        if setpoint != setpointLast and setpoint >=0:
            setpointLast = setpoint
            load.constantCurrent(str(setpoint))
        ci = load.constantCurrent()
        voltage = load.voltage()
        current = load.current()
        power = load.power()

        print('ci', '\t', load.constantCurrent(), end='\t')
        print('v', '\t', load.voltage(), '\t', __getVoltage(adc,1), end='\t')
        print('i', '\t', load.current(), '\t', __getCurrent(adc,0), end='\t')
        print('p', '\t', load.power(), '\t', (__getVoltage(adc,1)*__getCurrent(adc,0)), end='\n')

        file.write(str(time.time()) + '\t' + str(time.time()-load.startTime) + '\t')
        file.write('ci'+'\t'+str(load.constantCurrent())+'\t')
        file.write('v'+'\t'+str(load.voltage())+'\t'+str(__getVoltage(adc,1))+'\t')
        file.write('i'+'\t'+str(load.current())+'\t'+str(__getCurrent(adc,0))+'\t')
        file.write('p'+'\t'+str(load.power())+'\t'+str(__getVoltage(adc,1)*__getCurrent(adc,0))+'\t')
        file.write('e'+'\t'+str(__getVoltage(adc,1)-load.voltage())+'\t'+str(__getCurrent(adc,0)-load.current()))
        file.write('\n')
load.constantCurrent('0')
load.load('off')
print('End of test.')


