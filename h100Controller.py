##!/usr/bin/python3

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
    ##############
    # INITIALISE #
    ##############
    def __init__(self, purgeControl=0, purgeFreq=30, purgeTime=0.5):

        # Actions
        self.__on = 0
        self.__off = 1
        self.__reset = 2

        # Adc
        self.__Adc = adcpi.AdcPi2(18)

        # Delays
        self.__startTime = 3  # Seconds
        self.__stopTime = 10  # Seconds
        self.__cutoffTemp = 30  # Celsius

        # PiFace Interface
        self.__pfio = pifacedigitalio.PiFaceDigital()  # Start piface

        # Purge settings
        self.__purgeCtrl = purgeControl
        self.__purgeFreq = purgeFreq
        self.__purgeTime = purgeTime
        self.__timeChange = time()
        self.__pfio = pifacedigitalio.PiFaceDigital()  # Start piface

        # State
        self.STATE = enum(startup='startup', on='on', shutdown='shutdown', off='off', error='error')
        self.__state = self.STATE.off

        # Switches
        self.__fan = switch.Switch(0)
        self.__h2 = switch.Switch(1)
        self.__purge = switch.Switch(2)

        # Temperature
        self.__Temp = tmp102.Tmp102()

        # Variables
        self.__amps = [0.0] * 8
        self.__volts = [0.0] * 8
        self.__power = [0.0] * 4
        self.__temp = [0.0] * 4

        self.__timeChange = time()

    ##############
    #    MAIN    #
    ##############
    def run(self):

        # BUTTONS
        if self._getButton(self.__off):  # Turn off
            if self.__state == self.STATE.startup or self.__state == self.__STATE.on:
                self.__state = self.STATE.shutdown
                self.__timeChange = time()

        elif self._getButton(self.__on):  # Turn on
            if self.__state == self.STATE.off:
                self.__state = self.STATE.startup
                self.timeChange = time()

        elif self._getButton(self.__reset):  # Reset error
            if self.__state == self.STATE.error:
                self.__state = self.STATE.off
                self.__timeChange = time()

        # OVER TEMPERATURE
        if max(self.__temp) > self.__cutoffTemp:
            self.__state = self.STATE.error

            # OVER/UNDER VOLTAGE
            # todo, not important

        # SENSORS
        self.__amps[0] = self._getCurrent(self.__Adc, 0)
        self.__volts[0] = self._getVoltage(self.__Adc, 4)
        self.__power[0] = self.__volts[0] * self.__amps[0]
        self.__temp = self._getTemperature(self.__Temp)

        # PURGE CONTROL
        if self.__purgeCtrl != 0:
            vTarget = -1.2 * self.__amps[0] + 21  # From polarisation curve
            vError = self.__volts[0] - vTarget
            self.purgeFreq = self.__purgeCtrl(vError)

        # STATE MACHINE
        if self.__state == self.STATE.off:
            self._stateOff()
        if self.__state == self.STATE.startup:
            self._stateStartup()
            if (time() - self.__timeChange) > self.__startTime:
                self.__state = self.STATE.on
        if self.__state == self.STATE.on:
            self._stateOn()
        if self.__state == self.STATE.shutdown:
            self._stateShutdown()
            if (time() - self.__timeChange) > self.__stopTime:
                self.__state = self.STATE.off
        if self.__state == self.STATE.error:
            self._stateError()

    def shutdown(self):
        # When the programme exits, put through the shutdown routine
        if self.__state != self.STATE.off:
            self.__timeChange = time()
            while (time() - self.__timeChange) < self.__stopTime:
                self._stateShutdown()
            self._stateOff()
            self.__state = self.STATE.off
            print('Fuel Cell Off')
        print('\n\n\nFuel Cell Shut Down\n\n')

    ##############
    #  ROUTINES  #
    ##############
    # State Off Routine
    def _stateOff(self):
        self.__h2.write(False)
        self.__fan.write(False)
        self.__purge.write(False)

    # State Startup Routine
    def _stateStartup(self):
        self.__h2.timed(0, self.__startTime)
        self.__fan.timed(0, self.__startTime)
        self.__purge.timed(0, self.__startTime)

    # State On Routine
    def _stateOn(self):
        self.__h2.write(True)
        self.__fan.write(True)
        self.__purge.timed(self.__purgeFreq, self.__purgeTime)

    # State Shutdown Routine
    def _stateShutdown(self):
        self.__h2.write(False)
        self.__fan.timed(0, self.__stopTime)
        self.__purge.timed(0, self.__stopTime)

    # State Error Routine
    def _stateError(self):
        self.__h2.write(False)
        self.__purge.write(False)
        if max(self.__temp) > self.__cutoffTemp:
            self.__fan.write(True)
        else:
            self.__fan.write(False)

    ##############
    #EXT. GETTERS#
    ##############
    # Get State String
    @property
    def state(self):
        return self.__state

    @state.setter
    def state(self, state):
        if state.strip() in list(self.STATE.reverse_mapping):
            self.__state = state
        else:
            print("State not found in ", list(self.STATE.reverse_mapping))

    # Get Current
    @property
    def current(self):
        return self.__amps

    # Get Voltage
    @property
    def voltage(self):
        return self.__volts

    # Get Power
    @property
    def power(self):
        return self.__power

    # Get Temperature
    @property
    def temperature(self):
        return self.__temp

    # Get Purge Frequency
    @property
    def purgefrequency(self):
        return self.__purgeFreq

    # Get Purge Time
    @property
    def purgetime(self):
        return self.__purgeTime

    ##############
    #INT. GETTERS#
    ##############
    # Get Current (internal)
    @staticmethod
    def _getCurrent(Adc, channel):
        #        current = abs(Adc.val[channel] * 1000 / 6.9) + 0.424 - 0.125
        current = abs(Adc.get(channel) * 1000 / 6.92) + 0.31  #inc divisor to lower error slope
        if current < 0.475: current = 0  # Account for opamp validity        return current
        return current

    # Get Voltage (internal)
    @staticmethod
    def _getVoltage(Adc, channel):
        #        voltage = abs(Adc.val[channel] * 1000 / 60.9559671563) + 0.029
        voltage = abs(Adc.get(channel) * 1000 / 47.5) - 5.74  #inc divisor to lower error slope
        return voltage

    # Get Temperature (internal)
    @staticmethod
    def _getTemperature(Temp):
        t = [0.0] * 4
        t[0] = Temp.get(0x48)
        t[1] = Temp.get(0x49)
        t[2] = Temp.get(0x4a)
        t[3] = Temp.get(0x4b)
        return t

    # Get Button (internal)
    def _getButton(self, button):
        return self.__pfio.input_pins[button].value

