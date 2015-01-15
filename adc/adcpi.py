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

# Import Libraries
from quick2wire.i2c import I2CMaster, writing_bytes, reading

class MCP3424:
        # Hybrid
        # Address 1 0xD0
        # Address 2 0xD8
        
        # AdcPi2
        # Address 1 0x68
        # Address 2 0x69
    def __init__(self, address, resolution=12):
        # Check if user inputed a valid resolution
        if resolution != 12 and resolution != 14 and resolution != 16 and resolution != 18:
            raise ValueError('Incorrect ADC Resolution')
        else:
            self.__res = resolution

        # Build default address and configuration register
        self.__config = [[address, 0x90],
                         [address, 0xB0],
                         [address, 0xD0],
                         [address, 0xF0]]

        # Set resolution in configuration register
        for x in range(len(self.__config)):
            self.__config[x][1] = self.__config[x][1] | int((resolution - 12) / 2) << 2

        # Set the calibration multiplier
        self.__varDivisor = 0b1 << (resolution - 12)
        self.__varMultiplier = (2.495 / self.__varDivisor) / 1000

        if self.__changechannel(self.__config[0])<0:
            print("Err: No ADC detected at " + format(address, '02x'))


    # Method to change the channel we wish to read from
    @staticmethod
    def __changechannel(config):
        try:
            # Using the I2C databus...
            with I2CMaster(1) as master:
                master.transaction(
                    writing_bytes(config[0], config[1]))
            return 1
                    
        # If I2C error return
        except IOError:
            return -1

    # Method to read adc
    @staticmethod
    def __getadcreading(config, multiplier, res):
        try:
            # Using the I2C databus...
            with I2CMaster(1) as master:
                # Calculate how many bytes we will receive for this resolution
                numBytes = int(max(0, res / 2 - 8) + 3)
    
                # Initialise the ADC
                adcreading = master.transaction(
                    writing_bytes(config[0], config[1]),
                    reading(config[0], numBytes))[0]
    
                # Wait for valid data **blocking**
                while (adcreading[-1] & 128):
                    adcreading = master.transaction(
                        writing_bytes(config[0], config[1]),
                        reading(config[0], numBytes))[0]
                
#                adcreading = [0, 0, 127]
                
                # Shift bits to product result
                if numBytes is 4:
                    t = ((adcreading[0] & 0b00000001) << 16) | (adcreading[1] << 8) | adcreading[2]
                else:
                    t = (adcreading[0] << 8) | adcreading[1]
    
                # Check if positive or negative number and invert if needed
                if adcreading[0] > 128:
                    t = ~(0x020000 - t)
    
                # Return result
                return t * multiplier
                
        # If I2C error return error code -1
        except IOError:
            return -1

    # External getter - call this to receive data
    def get(self, channel, gain=1):
        config = self.__config[channel]

        if gain is 8:
            config[1]  = config[1] | 0b11

        # Change adc setting to the channel we want to read
        self.__changechannel(config)
        
        # Read and return the data
        return self.__getadcreading(config, self.__varMultiplier, self.__res)
        
        

class AdcPi2:
    def __init__(self, res=12):
        self.__adc1 = MCP3424(0x68, res)
        self.__adc2 = MCP3424(0x69, res)
        
    def get(self, channel):
        if channel in range(0,4):
            return self.__adc1.get(channel)
        elif channel in range(4,8):
            return self.__adc2.get(channel)
        else:
            return -1 # Error in channel
