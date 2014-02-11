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

# Includes
from time import time
import pifacedigitalio
from adc import adcpi
from temperature import tmp102
from switch import switch

# Function to mimic an 'enum'. Won't be needed in Python3.4
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in list(enums.items()))
    enums['reverse_mapping'] = reverse
    return type('Enum', (), enums)

##############
# CONTROLLER #
##############
class H100():
    # Define Sensors
    Adc = adcpi.AdcPi2Daemon()
    Temp = tmp102.Tmp102Daemon()
    Temp = tmp102.Tmp102()

    # Define Switches
    pfio = pifacedigitalio.PiFaceDigital() # Start piface
    fan = switch.Switch(0)
    h2 = switch.Switch(1)
    purge = switch.Switch(2)
    on = 0 # Switch numbers on the pfio
    off = 1
    reset = 2

    # Define Variables
    amps = [0.0] * 8
    volts = [0.0] * 8
    power = [0.0] * 4
    temp = [0.0] * 4

    # Define Controllables
    startTime = 3   # Seconds
    stopTime = 10  # Seconds
    purgeTime = 0.5 # Seconds
    purgeFreq = 30  # Seconds
    cutoffTemp = 30  # Celsius
    purgeCtrl = 0

    # Define States
    STATE = enum(startup='startup', on='on', shutdown='shutdown', off='off', error='error')
    state = STATE.off

    ##############
    # INITIALISE #
    ##############
    def __init__(self, purgeControl=0):
        self.Adc.daemon = True
        self.Adc.start()
        self.purgeCtrl = purgeControl

    ##############
    #    MAIN    #
    ##############
    def run(self):
        timeChange = time()
        self.state = self.STATE.off

        # BUTTONS
        if self.__getButton(self.off): # Turn off
            if self.state == self.STATE.startup or self.state.value == self.STATE.on:
                self.state = self.STATE.shutdown
                timeChange = time()
        elif self.__getButton(self.on): # Turn on
            if self.state == self.STATE.off:
                self.state = self.STATE.startup
                timeChange = time()
        elif self.__getButton(self.reset): # Reset error
            if self.state == self.STATE.error:
                self.state = self.STATE.off
                timeChange = time()
                # OVER TEMPERATURE
        if max(self.temp) > self.cutoffTemp:
            self.state = self.STATE.error

        # OVER/UNDER VOLTAGE
            # todo, not important

        # SENSORS
        self.amps[0]  = self.__getCurrent(0)
        self.volts[0] = self.__getVoltage(1)
        self.power[0] = self.volts[0] * self.amps[0]
        self.temp = self.__getTemperature()

        # PURGE CONTROL
        if self.purgeCtrl != 0:
            vTarget = -1.2*self.amps[0] + 21 # From polarisation curve
            vError = self.volts[0] - vTarget
            self.purgeFreq = self.purgeCtrl(vError)

        # STATE MACHINE
        if self.state == self.STATE.off:
            self.stateOff()
        if self.state == self.STATE.startup:
            self.stateStartup()
            if (time() - timeChange) > self.startTime:
                self.state = self.STATE.on
        if self.state == self.STATE.on:
            self.stateOn()
        if self.state == self.STATE.shutdown:
            self.stateShutdown()
            if (time() - timeChange) > self.stopTime:
                self.state = self.STATE.off
        if self.state == self.STATE.error:
            self.stateError()

    def shutdown(self):
        # When the programme exits, put through the shutdown routine
        if self.state != self.STATE.off:
            timeChange = time()
            while (time() - timeChange) < self.stopTime:
                self.stateShutdown()
            self.stateOff()
            self.state = self.STATE.off
            print('Fuel Cell Off')
        print('\n\n\nFuel Cell Shut Down\n\n')

    ##############
    #  ROUTINES  #
    ##############
    # State Off Routine
    def stateOff(self):
        self.h2.switch(False)
        self.fan.switch(False)
        self.purge.switch(False)

    # State Startup Routine
    def stateStartup(self):
        self.h2.timed(0, self.startTime)
        self.fan.timed(0, self.startTime)
        self.purge.timed(0, self.startTime)

    # State On Routine
    def stateOn(self):
        self.h2.switch(True)
        self.fan.switch(True)
        self.purge.timed(self.purgeFreq, self.purgeTime)

    # State Shutdown Routine
    def stateShutdown(self):
        self.h2.switch(False)
        self.fan.timed(0, self.stopTime)
        self.purge.timed(0, self.stopTime)

    # State Error Routine
    def stateError(self):
        self.h2.switch(False)
        self.purge.switch(False)
        if max(self.temp) > self.cutoffTemp:
            self.fan.switch(True)
        else:
            self.fan.switch(False)

    ##############
    #EXT. GETTERS#
    ##############
    # Get State String (global)
    def getState(self):
        return self.state

    # Get Current (global)
    def getCurrent(self):
        return self.amps

    # Get Voltage (global)
    def getVoltage(self):
        return self.volts

    # Get Power (global)
    def getPower(self):
        return self.power

    # Get Temperature (global)
    def getTemperature(self):
        return self.temp

    # Get Purge Frequency (global)
    def getPurgeFrequency(self):
        return self.purgeFreq

    # Get Purge Time (global)
    def getPurgeTime(self):
        return self.purgeTime

    ##############
    #INT. GETTERS#
    ##############
    # Get Current (internal)
    def __getCurrent(self, channel):
        return (abs(self.Adc.val[channel] * 1000 / 4.2882799485) + 0.6009) / 1.6046

    # Get Voltage (internal)
    def __getVoltage(self, channel):
        return (abs(self.Adc.val[channel] * 1000 / 60.9559671563))

    # Get Temperature (internal)
    def __getTemperature(self):
        t = [0.0]*4
        t[0] = self.Temp.get(0x48)
        t[1] = self.Temp.get(0x49)
        t[2] = self.Temp.get(0x4a)
        t[3] = self.Temp.get(0x4b)
        return t

    # Get Button (internal)
    def __getButton(self, button):
        return self.pfio.input_pins[button].value

