#!/usr/bin/env python3
import re
from smbus import SMBus

class I2c(object):
    def __init__(self):
	    self.bus = self.getI2cBus()

    def getI2cBus(self):
        # detect i2C port number and assign to i2c_bus
        for line in open('/proc/cpuinfo').readlines():
            m = re.match('(.*?)\s*:\s*(.*)', line)
            if m:
                (name, value) = (m.group(1), m.group(2))
                if name == "Revision":
                    if value [-4:] in ('0002', '0003'):
                        i2c_bus = 0
                    else:
                        i2c_bus = 1
                    break
        return SMBus(i2c_bus)
