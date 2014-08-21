#!/usr/bin/python3

# Simple software timer for a switch on the piface digital io

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

from time import time

import pifacedigitalio


# Class to enable controlled switching
class Switch:
    def __init__(self, pin):
        self.pin = pin
        self.state = False
        self.lastTime = 0
        self.lastOff = 0
        self.pfio = pifacedigitalio.PiFaceDigital()
        self.state = False
        self.lastTime = time()

    def timed(self, freq, duration):
        # Deactivate if time is up
        if (time() - self.lastTime) >= duration and self.state == True:
            return self.write(False)
        # Activate
        elif (time() - self.lastTime) >= freq and self.state == False:
            return self.write(True)

    def write(self, state):
        if state:
            self.pfio.output_pins[self.pin].turn_on()
        else:
            self.pfio.output_pins[self.pin].turn_off()
        self.lastTime = time()
        self.state = self.pfio.output_pins[self.pin].value
        return self.state

    def __del__(self):
        self.write(False)
        print('\nSwitch %d off\n' % self.pin)
