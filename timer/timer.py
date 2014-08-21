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

import time

class My_Time():

    def __init__(self):
        self.__start = time.time()
        self.__delta = 0
        self.__last = self.__start
        self.__timers = []
        self.run()

    def run(self):
        self.__delta = time.time() - self.__last
        self.__last = time.time()

    def create_timer(self):
        self.__timers.append(Timer())
        return len(self.__timers) - 1

    def get_timer(self, index):
        try:
            return self.__timers[index].elapsed
        except:
            return -1

    def reset_timer(self, index):
        return self.__timers[index].reset

    def remove_timer(self, index):
        self.__timers[index] = '' # This will leak!!!
		
    @property
    def start(self):
        return self.__start
	
    @property
    def last(self):
        return self.__last
		
    @property
    def delta(self):
        return self.__delta


class Timer(My_Time):

    def __init__(self):
        super().__init__()

    def reset(self):
        self.__start = time.time()
        
    @property
    def elapsed(self):
        return time.time() - self.__start
