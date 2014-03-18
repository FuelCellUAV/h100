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

load=scheduler.PowerScheduler('./tdiLoadbank/test.txt','158.125.152.225',10001,'fuelcell')

setpoint = 0
setpointLast = -1
input('Press any key to start')
startTime = time.time()
load.load('on')

# Get Current (internal)
def __getCurrent(Adc, channel):
    return ((abs(Adc.val[channel] * 1000 / 4.2882799485) + 0.6009) / 1.6046) - 0.01 ### 0.01 added
# Get Voltage (internal)
def __getVoltage(Adc, channel):
    return (abs(Adc.val[channel] * 1000 / 60.9559671563) + 0.025) ### 0.025 added

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

        file.write(str(time.time()) + '\t' + str(time.time()-startTime) + '\t')
        file.write('ci'+'\t'+str(load.constantCurrent())+'\t')
        file.write('v'+'\t'+str(load.voltage())+'\t'+str(__getVoltage(adc,1))+'\t')
        file.write('i'+'\t'+str(load.current())+'\t'+str(__getCurrent(adc,0))+'\t')
        file.write('p'+'\t'+str(load.power())+'\t'+str(__getVoltage(adc,1)*__getCurrent(adc,0))+'\t')
        file.write('e'+'\t'+str(load.voltage()-__getVoltage(adc,1))+'\t'+str(load.current()-__getCurrent(adc,0)))
        file.write('\n')
load.constantCurrent('0')
load.load('off')
print('End of test.')


