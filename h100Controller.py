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
import sys, time

import pifacedigitalio
from adc import adcpi
from temperature import tmp102
from switch import switch
from timer import timer
from mfc import mfc


# Function to mimic an 'enum'. Won't be needed after Python3.4 update
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
    def __init__(self, purge_control=0, purge_frequency=30, purge_time=0.5):

        # Adc
        self.__Adc = adcpi.AdcPi2(18)  # Start adc's
        # Temperature
        self.__Temperature = tmp102.Tmp102()  # Start temperature sensors
        # PiFace Interface
        self.__pfio = pifacedigitalio.PiFaceDigital()  # Start piface switch
        # Timer
        self.__timer = timer.My_Time()

        # Delays
        self.__start_time = 5  # Seconds
        self.__stop_time = 10  # Seconds
        self.__cutoff_temperature = 30  # Celsius
        self.__minimum_voltage = 10  # Volts
        self.__maximum_voltage = 30  # Volts

        # Purge settings
        self.__purge_control = purge_control
        self.__purge_frequency = purge_frequency
        self.__purge_time = purge_time
        self.__time_change = time.time()
        self.__pfio = pifacedigitalio.PiFaceDigital()  # Start piface
        self._switch_interrupt = self._switch_handler(self.__pfio, self._switch_on, self._switch_off,
                                                      self._switch_reset)
        self.__Mfc = mfc.mfc()
        self.__flow_rate = 0.0

        # State
        self.STATE = enum(startup='startup', on='on', shutdown='shutdown', off='off', error='error')
        self.__state = self.STATE.off

        # Switches
        self.__fan = switch.Switch(0)
        self.__h2 = switch.Switch(1)
        self.__purge = switch.Switch(2)

        # Variables
        self.__current = [0.0] * 8
        self.__voltage = [0.0] * 8
        self.__power = [0.0] * 4
        self.__energy = [0.0] * 2
        self.__temperature = [0.0] * 4

        # Button flags
        self.__on = 0
        self.__off = 0
        self.__reset = 0

        self.__state_change = 0

    ##############
    #    MAIN    #
    ##############
    def run(self):
        self.__timer.run()
        self._update_sensors()

        self._check_timers()
        self._check_switches()
        self._check_errors()

        # STATE MACHINE
        if self.__state is self.STATE.off:
            self._state_off()
        elif self.__state is self.STATE.on:
            self._state_on()
        elif self.__state is self.STATE.startup:
            self._state_startup()
        elif self.__state is self.STATE.shutdown:
            self._state_shutdown()
        elif self.__state is self.STATE.error:
            self._state_error()

        self.__state_change = 0  # Ignore property handler to force reset

        return

    def shutdown(self):
        # When the programme exits, call this shutdown routine
        print('\n\nFuel Cell shutting down...', end='')
        self.state = "off"
        while self.__state is not self.STATE.off:
            self._check_timers()
            self._check_switches()
            self._check_errors()

            # STATE MACHINE
            if self.__state is self.STATE.off:
                self._state_off()
            elif self.__state is self.STATE.on:
                self._state_on()
            elif self.__state is self.STATE.startup:
                self._state_startup()
            elif self.__state is self.STATE.shutdown:
                self._state_shutdown()
            elif self.__state is self.STATE.error:
                self._state_error()

        self._switch_interrupt.deactivate()
        print('...Fuel Cell successfully shut down\n\n')

        return

    # Get State String
    @property
    def state(self):
        return self.__state

    @state.setter
    def state(self, state):
        if "on" in state:
            self._switch_on()

        elif "off" in state:
            self._switch_off()
        elif "reset" in state:
            self._switch_reset()
        else:
            print("Invalid command [on, off, reset]")

    # Get Current
    @property
    def current(self):
        return self.__current

    # Get Voltage
    @property
    def voltage(self):
        return self.__voltage

    # Get Power
    @property
    def power(self):
        return self.__power

    # Get Energy
    @property
    def energy(self):
        return self.__energy

    # Get Temperature
    @property
    def temperature(self):
        return self.__temperature

    # Get Purge Frequency
    @property
    def purge_frequency(self):
        return self.__purge_frequency

    @purge_frequency.setter
    def purge_frequency(self, purge_frequency):
        if 0 < purge_frequency < 600:  # TODO max purge frequency
            self.__purge_frequency = purge_frequency

    # Get Purge Time
    @property
    def purge_time(self):
        return self.__purge_time

    @purge_time.setter
    def purge_time(self, purge_time):
        if 0 < purge_time < 10:  # TODO max purge time
            self.__purge_time = purge_time

    def _state_change(self, state):
        if state and not self.__state_change:
            self.__time_change = time.time()  # Update timer
            self.__state_change = 1

    def _switch_on(self):
        self.__on = True
        self.__off = False
        self.__reset = False
        return

    def _switch_off(self):
        self.__on = False
        self.__off = True
        self.__reset = False

    def _switch_reset(self):
        self.__on = False
        self.__off = False
        self.__reset = True

    ##############
    #  ROUTINES  #
    ##############
    # State Off Routine
    def _state_off(self):
        self.__h2.write(False)
        self.__fan.write(False)
        self.__purge.write(False)

    # State Startup Routine
    def _state_startup(self):
        self.__h2.timed(0, self.__start_time)
        self.__fan.timed(0, self.__start_time)
        self.__purge.timed(0, self.__start_time)

    # State On Routine
    def _state_on(self):
        self._purge_controller()
        self.__h2.write(True)
        self.__fan.write(True)
        self.__purge.timed(self.purge_frequency, self.__purge_time)

    # State Shutdown Routine
    def _state_shutdown(self):
        self.__h2.write(False)
        self.__fan.timed(0, self.__stop_time)
        self.__purge.timed(0, self.__stop_time)

    # State Error Routine
    def _state_error(self):
        self.__h2.write(False)
        self.__purge.write(False)
        if max(self.__temperature) > self.__cutoff_temperature:
            self.__fan.write(True)
        else:
            self.__fan.write(False)

    # Get Flow Rate
    @property
    def flow_rate(self):
        return self.__flow_rate

    ##############
    #INT. GETTERS#
    ##############
    # Get Current
    @staticmethod
    def _get_current(adc, channel):
#        current = abs(adc.get(channel) * 1000 / 6.89) + 0.507
        current = abs(adc.get(channel) * 1000 / 6.89) + 0.374
        if current < 0.475:  # TODO can this be improved?
            current = 0  # Account for opamp validity
        return current

    # Get Voltage
    @staticmethod
    def _get_voltage(adc, channel):
#        voltage = abs(adc.get(channel) * 1000 / 60.7) - 0.05
        voltage = abs(adc.get(channel) * 1000 / 60.7) - 0.096
        return voltage

    # Get Energy
    @staticmethod
    def _get_energy(my_timer, power):
        energy = my_timer.delta * power
        return energy

    # Get Temperature
    @staticmethod
    def _get_temperature(temperature):
        t = [0.0] * 4
        t[0] = temperature.get(0x48)
        t[1] = temperature.get(0x49)
        t[2] = temperature.get(0x4a)
        t[3] = temperature.get(0x4b)
        return t

    def _switch_handler(self, pifacedigital, switch_on, switch_off, switch_reset):
        handler = pifacedigitalio.InputEventListener(chip=pifacedigital)
        handler.register(0, pifacedigitalio.IODIR_FALLING_EDGE, switch_on, self)
        handler.register(1, pifacedigitalio.IODIR_FALLING_EDGE, switch_off, self)
        handler.register(2, pifacedigitalio.IODIR_FALLING_EDGE, switch_reset, self)
        handler.activate()
        return handler

    # See if any timers have expired
    def _check_timers(self):
        delta = time.time() - self.__time_change
        if self.__state is self.STATE.startup:
            if delta >= self.__start_time:
                self.__state = self.STATE.on
                self._state_change(True)
                print('FC On\n')
        elif self.__state is self.STATE.shutdown:
            if delta >= self.__stop_time:
                self.__state = self.STATE.off
                self._state_change(True)
                print('FC Off\n')
        return

    # See if any flags have been activated
    def _check_switches(self):
        if self.__on:
            if self.__state is self.STATE.off:
                self.__state = self.STATE.startup
                self._state_change(True)
        elif self.__off:
            if (self.__state is not self.STATE.off) or (self.__state is not self.STATE.error):
                self.__state = self.STATE.shutdown
                self._state_change(True)
        elif self.__reset:
            if self.__state is self.STATE.error:
                self.__state = self.STATE.off
                self._state_change(True)
        self.__on = 0  # Force clear the flag
        self.__off = 0  # Force clear the flag
        self.__reset = 0  # Force clear the flag
        return

    # See if the fuel cell has an error
    def _check_errors(self):
        # OVER TEMPERATURE
        if max(self.__temperature) > self.__cutoff_temperature:
            self.__state = self.STATE.error
            self._state_change(True)
            print(time.asctime() + ' ' + "TEMPERATURE CUTOFF")
        # OVER/UNDER VOLTAGE
        if self.__voltage[0] > self.__maximum_voltage:
            self.__state = self.STATE.error
            self._state_change(True)
            print(time.asctime() + ' ' + "VOLTAGE MAXIMUM CUTOFF")
#        if self.__voltage[0] < self.__minimum_voltage:
#            self.__state = self.STATE.error
#            self._state_change(True)
#            sys.stderr.write(time.asctime() + ' ' + "VOLTAGE MINIMUM CUTOFF")
        return

    # Update sensors
    def _update_sensors(self):
        # SENSORS
        self.__current[0] = self._get_current(self.__Adc, 0)
        self.__voltage[0] = self._get_voltage(self.__Adc, 4)
        self.__power[0] = self.__voltage[0] * self.__current[0]
        self.__energy[0] = self._get_energy(self.__timer, self.__power[0])
        self.__energy[1] += self.__energy[0] # Cumulative
        self.__temperature = self._get_temperature(self.__Temperature)
        self.__flow_rate = self._getFlowRate(self.__Mfc)
        return

    def _purge_controller(self):
        # PURGE CONTROL TODO
        if self.__purge_control != 0:
            # Basic controller:
            self.purge_frequency = (30 - (self.__power[0] * 0.25))
            # PID controller:
            #vTarget = -1.2 * self.__current[0] + 21  # From polarisation curve
            #vError = self.__voltage[0] - vTarget
            #self.purge_frequency = self.__purge_control(vError)
            # Print results
            #print('Freq: ',self.purge_frequency,'  Time: ',self.purge_time)
        return self.__purge_frequency

    # Get Hydrogen Flow Rate
    @staticmethod
    def _getFlowRate(mfc):
       try:
          return mfc.get()
       except IOError as e:
          # No device connected
          return 0.0
