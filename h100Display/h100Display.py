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

# A 'threaded' driver to allow the PiFace Control & Display board for the
# raspberryPi to run cleanly in the background. Data can be updated by
# calling the correct functions. In the main programme which imports this
# module, the following code is required to start the process:
#
# display = FuelCellDisplay(1, "My Process Name")
# display.daemon = True  # To ensure process is killed on Ctrl+c
# display.start()

import sys
import multiprocessing
import ctypes

import pifacecad # Follow install instructions on their website


# Fuel Cell Display Module
class FuelCellDisplay(multiprocessing.Process):
    # First define some pretty cutstom bitmaps!
    temp_symbol_index = 0
    progress_index = [1, 2, 3, 4, 5, 6, 7]
    temperature_symbol = pifacecad.LCDBitmap(
        [0x18, 0x18, 0x3, 0x4, 0x4, 0x4, 0x3, 0x0])
    progress_symbol = [
        pifacecad.LCDBitmap([0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x1f]),
        pifacecad.LCDBitmap([0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x1f, 0x1f]),
        pifacecad.LCDBitmap([0x0, 0x0, 0x0, 0x0, 0x0, 0x1f, 0x1f, 0x1f]),
        pifacecad.LCDBitmap([0x0, 0x0, 0x0, 0x0, 0x1f, 0x1f, 0x1f, 0x1f]),
        pifacecad.LCDBitmap([0x0, 0x0, 0x0, 0x1f, 0x1f, 0x1f, 0x1f, 0x1f]),
        pifacecad.LCDBitmap([0x0, 0x0, 0x1f, 0x1f, 0x1f, 0x1f, 0x1f, 0x1f]),
        pifacecad.LCDBitmap([0x0, 0x1f, 0x1f, 0x1f, 0x1f, 0x1f, 0x1f, 0x1f]),
    ]

    # Define the CAD board
    cad = pifacecad.PiFaceCAD()

    # Define our variables to display
    fcName = multiprocessing.Value(ctypes.c_char_p, 'H100')
    fcState = multiprocessing.Value(ctypes.c_char_p, '')
    temp = multiprocessing.Value('d', 10.0)
    power = multiprocessing.Value('d', 000)
    vFc = multiprocessing.Value('d', 9.0)
    iFc = multiprocessing.Value('d', 10.0)

    # This runs once when the class is created
    def __init__(self, threadID, name):
        # Initialise the multiprocess utility
        multiprocessing.Process.__init__(self)
        self.threadID = threadID
        self.name = name

        # Save my pretty custom bitmaps to the memory (max 8 allowed)
        self.cad.lcd.store_custom_bitmap(self.temp_symbol_index, self.temperature_symbol)
        for x in range(len(self.progress_index)):
            self.cad.lcd.store_custom_bitmap(self.progress_index[x], self.progress_symbol[x])

        # Clear the display screen and turn the backlight on
        self.cad.lcd.clear()
        self.cad.lcd.blink_off()
        self.cad.lcd.cursor_off()
        self.cad.lcd.backlight_on()

    # This is the main process loop called by start()
    def run(self):
        counter = 0
        try:
            while True:
                self.cad.lcd.home() # Set the cursor to the beginning

                # Write the top line
                self.cad.lcd.write('{:<4} {:^3} {:>4.1f}'
                    .format(self.fcName.value[:4], self.fcState.value[:3], self.temp.value))
                self.cad.lcd.write_custom_bitmap(self.temp_symbol_index)
                self.cad.lcd.write(' ')

                # A statement for my pretty bitmap animation
                self.cad.lcd.write_custom_bitmap(self.progress_index[counter])
                if counter < 6:
                    counter += 1
                else:
                    counter = 0

                    # Write the bottom line
                self.cad.lcd.write('\n{:2.0f}V {:2.0f}A  {:>5.1f}W'
                    .format(self.vFc.value, self.iFc.value, self.vFc.value * self.iFc.value))
        finally:
            self.cad.lcd.clear()
            self.cad.lcd.backlight_off()
            print('\nPiFace CAD Shut Down\n')

    # Call this function to change the fuel cell name (max 4x char will be displayed)
    def name(self, fcName):
        self.fcName.value = fcName
        return

    # Call this function to change the fuel cell state (max 3x char will be displayed)
    def state(self, fcState):
        self.fcState.value = fcState
        return

    # Call this function to change the fuel cell temperature
    def temperature(self, temperature):
        self.temp.value = temperature
        return

    # Call this function to change the fuel cell voltage
    def voltage(self, voltage):
        self.vFc.value = voltage
        return

    # Call this function to change the fuel cell current
    def current(self, current):
        self.iFc.value = current
        return
