#!/usr/bin/python3

# Power demand scheduler for a loadbank

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

# Import libraries
import time

class Profiler():
    def __init__(self, filename):
        self.__filename = filename
        self.__last_line = ''
        self.__this_line = ''
        self.__start_time = time.time()
        self.__running = 0
        self.__setpoint = 0
        self.__setpoint_last = -1

    def _get_line(self, pointer=1):
        if pointer is -1:
            self.__fid.seek( self.__fid.tell() - len(self.__this_line) )
        self.__last_line = self.__this_line
        self.__this_line = self.__fid.readline()
        return list( map(float,self.__this_line.split()) )

    # Find this time entry
    def _find_now(self):
        psuedo_time = time.time() - self.__start_time
        try:
            if list( map(float,self.__this_line.split()) )[0] > psuedo_time:
                return list( map(float,self.__this_line.split()) )[1]
        except (IndexError):
            pass
        try:
           x = self._get_line()[0]
           while float(x) < psuedo_time:
               x = self._get_line()[0]
               pass  # Check next line
        except (IndexError, ValueError):
            return -1  # End of test
        return self._get_line(-1)[1]  # Set pointer to the line before

    @property
    def running(self):
        return self.__running

    @running.setter
    def running(self, state):
        if state and not self.__running:
            self._start()
        elif not state and self.__running:
            self._stop()

    def _start(self):
        # Turn on
        print("Firing up the engines...")
        self.__fid = open(self.__filename)
        self.__start_time = time.time()
        self.__setpoint = 0
        self.__running = 1
        print("Chocks away!")

    def _stop(self):
        # Turn off
        print("Landing...")
        self.__running = 0
        self.__fid.close()
        print("Back in hangar!\n")

    def _run(self):
        if self.__running:
            if self.__setpoint >= 0:
                setpoint = self._find_now()
                if setpoint >= 0:
                    if setpoint != self.__setpoint:
                        self.__setpoint = setpoint
                        return self.__setpoint
                    return self.__setpoint
                else:
                    return -1
            else:
                print('Error: Loadbank setpoint below zero!')
                return -1
        else:
            return -1

    def run(self):
        # Do more running
        running = self._run()
        if self.__running and running is -1:
            self._stop()
        return running

