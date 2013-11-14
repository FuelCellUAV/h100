#!/usr/bin/python2
# A class to configure and read the AdcPi V1 by abElectronics
# Written by Simon Howroyd, with assistance from abElectronics

from   time import time
import smbus
import math

# Class to read ADC
class AdcPiV1:
        # create byte array and fill with initial values to define size
        adcreading = bytearray()
        adcreading.append(0x00)
        adcreading.append(0x00)
        adcreading.append(0x00)
        adcreading.append(0x00)
        
        # Default ADC configuration
        config = 0b10010000
        
        def __init__(self, bus, channel, resolution, gain, calibration):
                self.bus = bus
                if   channel in [1,2,3,4]:
                        self.address = 0x68
                elif channel in [5,6,7,8]:
                        self.address = 0x69
                self.config = self.config | ((channel-1) << 5) | (((resolution/2)-6) << 2) | int(math.log(gain,2))
                self.gain   = gain 
                self.resolution = resolution
                self.calibration= calibration

        def get(self):
                try:
                        self.bus.write_byte(self.address, self.config)
                        self.adcreading = self.bus.read_i2c_block_data(self.address,self.config)

                        if self.resolution is 18:
                                h = self.adcreading[0]
                                m = self.adcreading[1]
                                l = self.adcreading[2]
                                s = self.adcreading[3]
                                # wait for new data ***BLOCKING FUNCTION***
                                while (s & 128):
                                        self.adcreading = self.bus.read_i2c_block_data(self.address,self.config)
                                        h = self.adcreading[0]
                                        m = self.adcreading[1]
                                        l = self.adcreading[2]
                                        s = self.adcreading[3]
                        else:
                                h = self.adcreading[0]
                                m = self.adcreading[1]
                                l = self.adcreading[2]
                                # wait for new data ***BLOCKING FUNCTION***
                                while (l & 128):
                                        self.adcreading = self.bus.read_i2c_block_data(self.address,self.config)
                                        h = self.adcreading[0]
                                        m = self.adcreading[1]
                                        l = self.adcreading[2]

                        # shift bits to product result
                        if self.resolution is 18:
                                t = ((h & 0b00000001) << 16) | (m << 8) | l
                                # check if positive or negative number and invert if needed
                                if (h > 128):
                                        t = ~(131072 - t)
                                t = t * 0.000015625 * self.calibration
                        elif self.resolution is 16:
                                t = ((h & 0b01111111) << 8) | m
                                # check if positive or negative number and invert if needed
                                        if (h > 128):
                                        t = ~(32768 - t)
                                t = t * 0.0000625 * self.calibration
                        elif self.resolution is 14:
                                t = ((h & 0b00011111) << 8) | m
                                # check if positive or negative number and invert if needed
                                if (h > 128):
                                        t = ~(8192 - t)
                                t = t * 0.000250 * self.calibration
                        elif self.resolution is 12:
                                t = ((h & 0b00000111) << 8) | m
                                # check if positive or negative number and invert if needed
                                if (h > 128):
                                        t = ~(2048 - t)
                                t = t * 0.001 * self.calibration
                        return t/self.gain
                except Exception as e:
                      #print ("I2C ADC Error")
                   return -1