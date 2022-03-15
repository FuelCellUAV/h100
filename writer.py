##!/usr/bin/env python3

# IO Control Driver

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


# Define class
class MyWriter:
    # Code to run when class is created
    def __init__(self, stdout, filename):
        self.stdout = stdout
        self.logfile = open(filename, 'w')

    # Method to write data
    def write(self, text):
        self.stdout.write(text)
        self.logfile.write(text)

    # Method to close the IOs
    def close(self):
        self.stdout.close()
        self.logfile.close()

    # Method to force write anything in the buffers
    def flush(self):
        self.stdout.flush()
