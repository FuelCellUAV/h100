#!/usr/bin/python3

# Simple common timer

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
import time


# Define class
class My_Time():
    # Code to run when class is created
    def __init__(self):
        self.__start = time.time()
        self.__delta = 0
        self.__last = self.__start
        self.__timers = []
        self.run()

    # Method to run the timer
    def run(self):
    	# Update dt
        self.__delta = time.time() - self.__last
        
        # Update last time
        self.__last = time.time()

    # Method to create a new timer
    def create_timer(self):
    	# Append a new timer to the list of timers
        self.__timers.append(Timer())
        
        # Return the timer index in the list of timers
        return len(self.__timers) - 1

    # Method to get a timer from the list
    def get_timer(self, index):
    	# Try to get the timer from the list
        try:
            return self.__timers[index].elapsed
            
        # Index error means timeer isn't there, return error code -1
        except IndexError as e:
            return -1

    # Reset a timer
    def reset_timer(self, index):
        return self.__timers[index].reset

    #Remove a timer
    def remove_timer(self, index):
        self.__timers[index] = '' # This will leak!!!
		
    # Property - Is the timer started?
    @property
    def start(self):
        return self.__start
	
    # Property - What's the last time?
    @property
    def last(self):
        return self.__last

    # Property - What's the dt?
    @property
    def delta(self):
        return self.__delta


# Define class
class Timer(My_Time):
    # Code to run when class is created
    def __init__(self):
    	# Initialise base class
        super().__init__()

    # Reset the timer
    def reset(self):
        self.__start = time.time()
        
    # Property - What's the elapsed time?
    @property
    def elapsed(self):
        return time.time() - self.__start
        
