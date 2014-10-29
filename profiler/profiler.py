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

class Profiler(TdiLoadbank):
    def __init__(self, filename):
        self.__filename = filename
        self.__fid = self._open(filename)
        self.__last_line = ''
        self.__this_line = ''
        self.__start_time = time.time()
        self.__out = out
        self.__running = 0
        self.__setpoint = 0
        self.__setpoint_last = -1

    @classmethod
    def _open(cls, filename):
        return open(filename)
        
    @classmethod
    def _close(cls, fid):
        fid.close()

    def _get_line(self, pointer=1):
        if pointer is -1:
            self.__fid.seek( self.__fid.tell() - len(self.__last_line) - 1)
            return list( map(float,self.__last_line.split()) )
        self.__last_line = self.__this_line
        self.__this_line = self.__fid.readline()
        return list( map(float,self.__this_line.split()) )

    # Find this time entry
    def _find_now(self):
        psuedo_time = time.time() - self.__start_time
        try:
           while self._get_line()[0] < psuedo_time:
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
        self.__start_time = time.time()
        self.__setpoint = 0
        self.load = True
        self.__log = open(('/media/usb0/'
                           + time.strftime('%y%m%d-%H%M%S')
                           + '-profile-' + self.__out + '.tsv'), 'w')
        self.__running = 1
        print("Chocks away!")

    def _stop(self):
        # Turn off
        print("Landing...")
        self.zero()
        self.load = False
        self.__log.close()
        self.__running = 0
        print("Back in hangar!\n")

    def _run(self):
        if self.__running:
            if self.__setpoint >= 0:
                setpoint = self._find_now()
                if setpoint >= 0:
                    if setpoint != self.__setpoint:
                        if "VOLTAGE" in self.mode:
                            self.voltage_constant = str(setpoint)
                        elif "CURRENT" in self.mode:
                            self.current_constant = str(setpoint)
                        elif "POWER" in self.mode:
                            self.power_constant = str(setpoint)
                        else:
                            print("Mode error in scheduler")
                            return False
                        self.__setpoint = setpoint
                    return True
                else:
                    print('End of profile')
                    return False
            else:
                print('Error: Loadbank setpoint below zero!')
                return False
        else:
            return False

    def run(self):
        # Do more running
        self.running = self._run()

        if self.__running:
            self.__log.write(str(time.time()) + '\t')
            self.__log.write(str(self.current_constant) + '\t')
            self.__log.write(str(self.voltage) + '\t')
            self.__log.write(str(self.current) + '\t')
            self.__log.write(str(self.power) + '\n')
