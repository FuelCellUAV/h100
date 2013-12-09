#!/usr/bin/env python3
# read abelectronics ADC Pi V2 board inputs with repeating reading from each channel.
# # Requries Python 2.7
# Requires SMBus 
# I2C API depends on I2C support in the kernel

# Version 1.0  - 06/02/2013
# Version History:
# 1.0 - Initial Release

#
# Usage: changechannel(address, hexvalue) to change to new channel on adc chips
# Usage: getadcreading(address, hexvalue) to return value in volts from selected channel.
#
# address = adc_address1 or adc_address2 - Hex address of I2C chips as configured by board header pins.

from smbus import SMBus
import re
from time import sleep

DSPi_address1 = 0x68
DSPi_address2 = 0x69

varDivisor    = 64 # from pdf sheet on adc addresses and config
varMultiplier = 2.4705882/1000;

bus = SMBus(1)
 
def getadcreading(address, adcConfig):
#	bus.write_i2c_block_data(address,0x00,[adcConfig])
	h, m, l, s = bus.read_i2c_block_data(address,adcConfig,4)

	# wait for new data
	while (s & 128):
	        h, m, l, s = bus.read_i2c_block_data(address,adcConfig,4)
		data = bus.read_i2c_block_data(address,adcConfig,4)
	
	print data
	return -1
	# shift bits to product result
	t = ((h & 0b00000001) << 16) | (m << 8) | l
	print ("h:%d m:%d l:%d s:%d" % (h, m, l, s)),

	# check if positive or negative number and invert if needed
	if (h > 128):
		t = ~(0x020000 - t)
	# return result
	return t * (varMultiplier / varDivisor)

while True:
        print ("1:%02.2f " % getadcreading(DSPi_address1, 0x8C))
        print ("2:%02.2f " % getadcreading(DSPi_address1, 0xAC))
        #print ("3:%02.2f " % getadcreading(DSPi_address1, 0xDC)),
        #print ("4:%02.2f " % getadcreading(DSPi_address1, 0xFC)),
        #print ("5:%02.2f " % getadcreading(DSPi_address2, 0x9C)),
        #print ("6:%02.2f " % getadcreading(DSPi_address2, 0xBC)),
        #print ("7:%02.2f " % getadcreading(DSPi_address2, 0xDC)),
        #print ("8:%02.2f " % getadcreading(DSPi_address2, 0xFC))
	sleep(1)
