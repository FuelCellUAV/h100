##!/usr/bin/python3

# Fuel Cell Controller for the Horizon H100 PEMFC

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

#############################################################################

# Import libraries
import sys, time
import pifacedigitalio
from hybrid import hybrid
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

# Define class
class PurgeControl():
    # Code to run when class is created
    def __init__(self):
        self.v = 0.0
        self.i = 0.0
        self.p = 0.0
        self.vLast = 0.0
        self.iLast = 0.0
        self.pLast = 0.0
        return

    # Method to update the class data
    def updateNow(self, v, i, p):
        self.v = v
        self.i = i
        self.p = p        

    # Method to update the class' last data
    def updateLast(self):
        self.vLast = self.v
        self.iLast = self.i
        self.pLast = self.p        

    # Method to return the Horizon control strategy
    def horizon(self):
        return 30.0

    # Method to return the derivative control strategy
    def derivative(self):
        return (self.v - self.vLast) \
                / (-0.03*self.v**4 + 1.94*self.v**3 - 46.5*self.v**2 + 421.2*self.v - 1489)

    # Method to return the power control strategy
    def power(self):
        return (30.0 - (self.p * 0.25))

    # Method to return the polar control strategy
    def polar(self):
        vTarget = -1.2 * self.i + 21  # From polarisation curve
        vError = self.v - vTarget
        return 10*vError


#############################################################################


# Define class
class H100():
    # Code to run when class is created
    def __init__(self):
        # Start the ADCPI
        self.__Adc1 = adcpi.MCP3424(0x6A)
        self.__Adc2 = adcpi.MCP3424(0x6B)

        self.__Adc3 = adcpi.MCP3424(0x68)
        self.__Adc4 = adcpi.MCP3424(0x6C)

        # Start the hybrid board
        self.__hybrid = hybrid.Hybrid()

        # Start temperature sensors
        self.__Temperature = tmp102.Tmp102()

        # Start the mass flow controller
        self.__Mfc = mfc.mfc()
        
        # Start timers
        self.__timer = timer.My_Time()

        # Set start and stop duration
        self.__start_time = 3  # Seconds
        self.__stop_time = 3  # Seconds
        
        # Set maximum temperature
        self.__cutoff_temperature = 30  # Celsius
        
        # Set maximum and minimum voltages
        self.__minimum_voltage = 10  # Volts
        self.__maximum_voltage = 30  # Volts

        # Start the purge controller
        self.__Purge_Controller = PurgeControl()
        
        # Define minimum and maximum purge frequencies
        self.__purge_frequency_minimum = 5
        self.__purge_frequency_maximum = 50
        
        # Set the default purge settings
        self.__purge_frequency = 30
        self.__purge_time = 0.5
        
        # Set the current time
        self.__time_change = time.time()
        
        # Start the piface for input switch functionality
#        self.__pfio = pifacedigitalio.PiFaceDigital()
#        self._switch_interrupt = self._switch_handler(self.__pfio, self._switch_on, self._switch_off,
#                                                      self._switch_reset)
                                                      
        # Define state
        self.STATE = enum(startup='startup', on='on', shutdown='shutdown', off='off', error='error')

        # Define output switches
        self.__fan   = switch.Switch(self.__hybrid.fan_on,   self.__hybrid.fan_off)
        self.__h2    = switch.Switch(self.__hybrid.h2_on,    self.__hybrid.h2_off)
        self.__purge = switch.Switch(self.__hybrid.purge_on, self.__hybrid.purge_off)

        # Define variables
        self.__currentHybrid = [0.0] * 3
        self.__voltageHybrid = [0.0] * 3
        self.__current       = [0.0] * 3
        self.__voltage       = [0.0] * 3
        self.__power         = [0.0] * 3
        self.__energy        = [0.0] * 3
        self.__temperature   = [0.0] * 6
        self.__flow_rate     = 0.0
        self.__state         = self.STATE.off

        # Software switches
        self.__on    = 0
        self.__off   = 0
        self.__reset = 0

        # State change flag
        self.__state_change = 0

    # Method to run the controller
    def run(self):
        # Update the hybrid
        self.__hybrid.update()

        # Update the timer
        self.__timer.run()
        
        # Update the sensors
        self._update_sensors()

        # Have any timers changed?
        self._check_timers()
        
        # Have any switches been pressed?
        self._check_switches()
        
        # Have any errors occured?
        self._check_errors()

        # STATE MACHINE
        if self.__state is self.STATE.off:
            # Run the off method
            self._state_off()
        elif self.__state is self.STATE.on:
            # Run the on method
            self._state_on()
        elif self.__state is self.STATE.startup:
            # Run the startup method
            self._state_startup()
        elif self.__state is self.STATE.shutdown:
            # Run the shutdown method
            self._state_shutdown()
        elif self.__state is self.STATE.error:
            # Run the error method
            self._state_error()

        # Reset state change flag
        self.__state_change = 0

    # Method to shutdown
    def shutdown(self):
        # Tell the user we are shutting down
        print('...Fuel Cell shutting down...', end='')
        
        # Set state to off
        self.state = "off"
        
        # Wait until turned off **blocking**
        while self.__state is not self.STATE.off:
            self.run()

        self.__hybrid.shutdown()

        # Deactivate user switches
#        self._switch_interrupt.deactivate()
        
        # Tell the user we have shut down
        print('done')

    # Property - What's the current state?
    @property
    def state(self):
        return self.__state

    # Property - Set a new state
    @state.setter
    def state(self, state):
        # Check the state with reset arguments
        if "on" in state:
            # Turn on
            self._switch_on()
            
        elif "off" in state:
            # Turn off
            self._switch_off()
            
        elif "reset" in state:
            # Reset
            self._switch_reset()
            
        else:
            # Invalid command
            print("Invalid command [on, off, reset]")

    # Property - What's the current?
    @property
    def current(self):
        return self.__current

    # Property - What's the voltage?
    @property
    def voltage(self):
        return self.__voltage

    # Property - What's the current?
    @property
    def currentHybrid(self):
        return self.__currentHybrid

    # Property - What's the voltage?
    @property
    def voltageHybrid(self):
        return self.__voltageHybrid

    # Property - What's the power?
    @property
    def power(self):
        return self.__power

    # Property - What's the energy consumed?
    @property
    def energy(self):
        return self.__energy

    # Property - What's the temperature?
    @property
    def temperature(self):
        return self.__temperature

    # Property - What's the purge frequency?
    @property
    def purge_frequency(self):
        return self.__purge_frequency

    # Property - Set a new purge frequency 
    @purge_frequency.setter
    def purge_frequency(self, purge_frequency):
        # Sanity check the requested purge frequency
        if purge_frequency < self.__purge_frequency_minimum:
            # Requested frequency is too short
            print('Purge frequency too low: ', purge_frequency)
            purge_frequency = self.__purge_frequency_minimum
            
        elif purge_frequency > self.__purge_frequency_maximum:
            # Requested frequency is too long
            print('Purge frequency too high: ', purge_frequency)
            purge_frequency = self.__purge_frequency_maximum
            
        # Set new purge frequency
        self.__purge_frequency = purge_frequency

    # Property - What's the purge duration?
    @property
    def purge_time(self):
        return self.__purge_time

    # Property - Set a new purge duration
    @purge_time.setter
    def purge_time(self, purge_time):
        if 0 < purge_time < 10:  # TODO max purge time
            self.__purge_time = purge_time

    # Method to change state
    def _state_change(self, state):
        # Check if we want to change state and that we haven't already changed
        if state and not self.__state_change:
            self.__time_change = time.time()  # Update timer
            self.__state_change = 1

    # Method to switch on
    def _switch_on(self):
        self.__on = True
        self.__off = False
        self.__reset = False
        return

    # Method to switch off
    def _switch_off(self):
        self.__on = False
        self.__off = True
        self.__reset = False

    # Method to reset
    def _switch_reset(self):
        self.__on = False
        self.__off = False
        self.__reset = True

    ##############
    #  ROUTINES  #
    ##############
    # State Off Routine
    def _state_off(self):
#       self._purge_controller() # not needed #
#       self.__h2.write(False)
       self.__fan.write(False)
       self.__purge.write(False)

    # State Startup Routine
    def _state_startup(self):
#        self.__h2.timed(0, self.__start_time)
        self.__fan.timed(0, self.__start_time)
        self.__purge.timed(0, self.__start_time)

    # State On Routine
    def _state_on(self):
        self._purge_controller()
#        self.__h2.write(True)
        self.__fan.write(True)
        self.__purge.timed(self.purge_frequency, self.__purge_time)

    # State Shutdown Routine
    def _state_shutdown(self):
#        self.__h2.write(False)
        self.__fan.timed(0, self.__stop_time)
        self.__purge.timed(0, self.__stop_time)

    # State Error Routine
    def _state_error(self):
#        self.__h2.write(False)
        self.__purge.write(False)
        
        # Wait for temperature to cool down before turning fan off
        if max(self.__temperature) > self.__cutoff_temperature:
            self.__fan.write(True)
        else:
            self.__fan.write(False)

    # Property - What's the mass flow rate?
    @property
    def flow_rate(self):
        return self.__flow_rate

    ##############
    #INT. GETTERS#
    ##############
    # Method to get Current
    @staticmethod
    def _get_currentHybrid(Hybrid):
        current = [Hybrid.fc_current_to_motor,
                    Hybrid.fc_current_total,
                    Hybrid.battery_current,
                    Hybrid.charge_current,
                    Hybrid.output_current]
        for x in range(5):
            if current[x] >= 0.0:
                current[x] = abs(current[x] * 1000 / 6.89) + 0.374
            
        return current

    # method to get Voltage
    @staticmethod
    def _get_voltageHybrid(Hybrid):
        voltage = [Hybrid.fc_voltage,
                Hybrid.battery_voltage,
                Hybrid.output_voltage]
        return voltage
        for x in range(3):
            if voltage[x] >= 0.0:
                voltage[x] = abs(voltage[x] * 1000 / 60.7) - 0.096
        return voltage

    # Method to get Current
    @staticmethod
    def _get_current(adc, channel):
        # Get current and calibrate
        current = abs(adc.get(channel) * 1000 / 6.89) * 1.075
        if current > 1000.0: current = 0.0 #TODO
        
        # Sensor only valid above a certain value
#        if current < 0.475:  # TODO can this be improved?
#            current = 0  # Account for opamp validity
            
        return current

    # method to get Voltage
    @staticmethod
    def _get_voltage(adc, channel):
        voltage = abs(adc.get(channel) * 1000 / 60.7)
        if voltage > 1000.0: voltage = 0.0 #TODO
        return voltage

    # Method to get Current
    @staticmethod
    def _get_current2(adc, channel):
        # Get current and calibrate
        current = abs(adc.get(channel))# * 1000 / 1)
        if current > 1000.0: current = 0.0 #TODO
        
        # Sensor only valid above a certain value
#        if current < 0.475:  # TODO can this be improved?
#            current = 0  # Account for opamp validity
            
        return current

    # method to get Voltage
    @staticmethod
    def _get_voltage2(adc, channel):
        voltage = abs(adc.get(channel))# * 1000.0 / 186.0) - 0.096
        if voltage > 1000.0: voltage = 0.0 #TODO
        return voltage

    # Method to get Energy
    @staticmethod
    def _get_energy(my_timer, power):
        # Energy is power x time
        energy = my_timer.delta * power
        return energy

    # Method to get Temperature
    @staticmethod
    def _get_temperature(Hybrid, temperature):
        t = [Hybrid.t1,
             Hybrid.t2,
             temperature.get(0x48),
             temperature.get(0x49),
             temperature.get(0x4a),
             temperature.get(0x4b)]
        return t

    # Method to get mass flow rate
    @staticmethod
    def _getFlowRate(mfc):
        return mfc.get()
        
    # Method to check if any timers have expired
    def _check_timers(self):
        # Calculate time since last state change
        delta = time.time() - self.__time_change
        
        # If currently in startup...
        if self.__state is self.STATE.startup:
            
            # and we have expired the startup duration...
            if delta >= self.__start_time:
                # Change state to on
                self.__state = self.STATE.on
                self._state_change(True)
                
                # Tell the user the fuel cell is now on
                print('FC On\n')
                
        # or if we are in shutdown...
        elif self.__state is self.STATE.shutdown:
            
            # and we have expired the shutdown duration...
            if delta >= self.__stop_time:
                # # Change state to off
                self.__state = self.STATE.off
                self._state_change(True)
                
                # Tell the user the fuel cell is now off
                print('FC Off\n')

    # Method to check if any software switches have been activated
    def _check_switches(self):
        # If the on switch has been triggered...
        if self.__on:
            
            # and we are currently off...
            if self.__state is self.STATE.off:
                # Change state to startup
                self.__state = self.STATE.startup
                
                # Flag that there has been a state change
                self._state_change(True)
                
        # or the off switch has been triggered...
        elif self.__off:
            
            # and we are currently no off or in error...
            if (self.__state is not self.STATE.off) or (self.__state is not self.STATE.error):
                
                # Change state to shutdown
                self.__state = self.STATE.shutdown
                
                # Flag that there has been a state change
                self._state_change(True)
                
        # or the reset switch has been triggered...     
        elif self.__reset:
            
            # and we are currently in error...
            if self.__state is self.STATE.error:
                
                # Clear the error by setting state to off
                self.__state = self.STATE.off
                
                # Flag that there has been a state change
                self._state_change(True)
        
        # Clear all state change request flags
        self.__on = 0
        self.__off = 0
        self.__reset = 0

    # Method to check if the fuel cell has an error
    def _check_errors(self):
        # If the temperature is above the cutoff...
        if max(self.__temperature) > self.__cutoff_temperature:
            
            # Change state to error
            self.__state = self.STATE.error
            self._state_change(True)
            
            # Tell user there is a temperature error
            print(time.asctime() + ' ' + "TEMPERATURE CUTOFF")
            
        # If the voltage is too high...
        if self.__voltage[0] > self.__maximum_voltage:
            
            # Change state to error
            self.__state = self.STATE.error
            self._state_change(True)
            
            # Tell user there is an overvoltage error
            print(time.asctime() + ' ' + "VOLTAGE MAXIMUM CUTOFF")
        
#        # If the voltage is too low...
#        if self.__voltage[0] < self.__minimum_voltage:
#
#            # Change state to error
#            self.__state = self.STATE.error
#            self._state_change(True)
#            
#            # Tell user there is an undervoltage error
#            sys.stderr.write(time.asctime() + ' ' + "VOLTAGE MINIMUM CUTOFF")

    # Method to update sensor data
    def _update_sensors(self):
        # ADC
        self.__voltage[0] = self._get_voltage(self.__Adc1, 0)
        self.__voltage[1] = self._get_voltage(self.__Adc1, 2)
        self.__voltage[2] = self._get_voltage(self.__Adc2, 0)
        self.__current[0] = self._get_current(self.__Adc1, 1)
        self.__current[1] = self._get_current(self.__Adc1, 3)
        self.__current[2] = self._get_current(self.__Adc2, 1)

        self.__voltageHybrid[0] = self._get_voltage2(self.__Adc4, 2)
        self.__voltageHybrid[1] = self._get_voltage2(self.__Adc4, 0)
        self.__voltageHybrid[2] = self._get_voltage2(self.__Adc4, 1)
        self.__currentHybrid[0] = self._get_current2(self.__Adc3, 2)
        self.__currentHybrid[1] = self._get_current2(self.__Adc3, 0)
        self.__currentHybrid[2] = self._get_current2(self.__Adc3, 1)

        return
        # HYBRID
#        self.__voltageHybrid = self._get_voltageHybrid(self.__hybrid)
#        self.__currentHybrid = self._get_currentHybrid(self.__hybrid)

        # Power FC
        if self.__voltage[0] >=0.0 and  self.__current[1] >=0.0:
            self.__power[0] = self.__voltage[0] * self.__current[1]
        else:
            self.__power[0] = -1

        # Power Batt
        if self.__voltage[1] >=0.0 and  self.__current[2] >=0.0:
            self.__power[1] = self.__voltage[1] * self.__current[2]
        else:
            self.__power[1] = -1

        # Power Out
        if self.__voltage[2] >=0.0 and  self.__current[4] >=0.0:
            self.__power[2] = self.__voltage[2] * self.__current[4]
        else:
            self.__power[2] = -1

        for x in range(3):
            energy = self._get_energy(self.__timer, self.__power[x])
            self.__energy[x] += energy # Cumulative

        self.__temperature = self._get_temperature(self.__hybrid, self.__Temperature)
#        self.__flow_rate = self._getFlowRate(self.__Mfc)
        
    # Method to run the purge controller
    def _purge_controller(self):
        # Update the purge controller sensor data
        self.__Purge_Controller.updateNow(self.__voltage[0], self.__current[0], self.__power[0])
        
        # Pick one of these four controllers
        self.purge_frequency = self.__Purge_Controller.horizon()
#        self.purge_frequency = self.__Purge_Controller.derivative()
#        self.purge_frequency = self.__Purge_Controller.power()
#        self.purge_frequency = self.__Purge_Controller.polar()

        # Print results
#        print('Freq: ',self.purge_frequency,'  Time: ',self.purge_time)

        # Return the new purge frequency
        return self.purge_frequency
