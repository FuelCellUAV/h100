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

# Class to enable controlled switching
class Switch:
    def __init__(self, function_on, function_off):
        self.on  = function_on
        self.off = function_off
        self.state = False
        self.lastTime = 0
        self.lastOff = 0
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
            self.on()
        else:
            self.off()
        self.lastTime = time()
        self.state = state
        return self.state

    def __del__(self):
        self.write(False)
        print('\nSwitch %d off\n' % self.pin)
