##!/usr/bin/env python3

# Fuel Cell Controller LCD display driver

# Copyright (C) 2013  Simon Howroyd
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
import pifacecad


# Define class
class FuelCellDisplay():
    # Code to run when class is created
    def __init__(self):
        # First define some pretty cutstom bitmaps!
        self.__temp_symbol_index = 7
        self.__temperature_symbol = pifacecad.LCDBitmap(
            [0x18, 0x18, 0x3, 0x4, 0x4, 0x4, 0x3, 0x0])

        # Screen data
        self.__name = ''
        self.__state = ''
        self.__temp = ''
        self.__volts = ''
        self.__amps = ''

    # Method to connect to CAD board
    def connect(self):
        # Define the CAD board
        try:
            self.__cad = pifacecad.PiFaceCAD()
        except Exception as e:
            # No CAD board found
            return -1

        # Save my pretty custom bitmaps to the memory (max 8 allowed)
        self.__cad.lcd.store_custom_bitmap(self.__temp_symbol_index, self.__temperature_symbol)

        # Start up the screen
        self.__on = False

        return 1

    # Method to turn the screen on
    @staticmethod
    def turnon(cad):
        # Start up the screen
        cad.lcd.blink_off()
        cad.lcd.cursor_off()
        cad.lcd.backlight_on()
        cad.lcd.clear()
        return True

    # Method to turn the screen off
    @staticmethod
    def turnoff(cad):
        # Close down the screen
        cad.lcd.home()
        cad.lcd.backlight_off()
        cad.lcd.clear()
        print('\n\nDisplay off\n\n')
        return False

    # Property - Is it on?
    @property
    def on(self):
        return self.__on

    # Property - Turn on
    @on.setter
    def on(self, switch):
        if self.__on is True and switch is False:
            self.__on = self.turnoff(self.__cad)
        elif self.__on is False and switch is True:
            self.__on = self.turnon(self.__cad)

    # Property - What's the name I'm displaying?
    @property
    def name(self):
        return self.__name

    # Property - Define my name
    @name.setter
    def name(self, text):
        self.__name = self._update(self.__cad, text, [0, 0], 4)

    # Property - What's the state I'm displaying?
    @property
    def state(self):
        return self.__state

    @state.setter
    def state(self, text):
        self.__state = self._update(self.__cad, text, [5, 0], 3)

    # Property - What's the temperature I'm displaying?
    @property
    def temperature(self):
        return self.__temp

    @temperature.setter
    def temperature(self, number):
        self._update(self.__cad, self.__temperature_symbol, [13, 0], index=self.__temp_symbol_index)
        self.__temp = self._update(self.__cad, number, [9, 0], 4)

    # Property - What's the voltage I'm displaying?
    @property
    def voltage(self):
        return self.__volts

    @voltage.setter
    def voltage(self, number):
        self._update(self.__cad, 'V', [4, 1], 1)
        self.__volts = self._update(self.__cad, number, [0, 1], 4)

    # Property - What's the current I'm displaying?
    @property
    def current(self):
        return self.__amps

    @current.setter
    def current(self, number):
        self._update(self.__cad, 'A', [10, 1], 1)
        self.__amps = self._update(self.__cad, number, [6, 1], 4)

#    @staticmethod
    def _update(self, cad, data, ptr, precision=1, index=-1):
        if self.__on is False: return

        # Move cursor to correct place (col, row)
        cad.lcd.set_cursor(ptr[0], ptr[1])

        if type(data) is str:
            data = data[:precision].center(precision)

        elif type(data) is float or int:
            # Convert number to string
            data = str(data)
            # Truncate
            if len(data.split('.')[0]) > precision:
                # Replace with 'x' if too long
                data = 'x' * precision
            else:
                # Truncate and justify
                data = data[:precision].rjust(precision)

        if index < 0 and type(data) is str:
            cad.lcd.write(data)
            return data
        elif index >= 0:
            cad.lcd.write_custom_bitmap(index)
            return index

        raise AttributeError
