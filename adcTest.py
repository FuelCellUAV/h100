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

adc_address1 = 0x68
adc_address2 = 0x69

# create byte array and fill with initial values to define size
adcreading = bytearray()

adcreading.append(0x00)
adcreading.append(0x00)
adcreading.append(0x00)
adcreading.append(0x00)

varDivisior = 64 # from pdf sheet on adc addresses and config
varMultiplier = (2.4705882/varDivisior)/1000

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
               

bus = SMBus(i2c_bus)
 
def changechannel(address, adcConfig):
	tmp= bus.write_byte(address, adcConfig)

def getadcreading(address, adcConfig):
	adcreading = bus.read_i2c_block_data(address,adcConfig)
	h = adcreading[0]
	m = adcreading[1]
	l = adcreading[2]
	s = adcreading[3]
	# wait for new data
	while (s & 128):
		adcreading = bus.read_i2c_block_data(address,adcConfig)
		h = adcreading[0]
		m = adcreading[1]
		l = adcreading[2]
		s = adcreading[3]

	# shift bits to product result
	t = ((h & 0b00000001) << 16) | (m << 8) | l
	# check if positive or negative number and invert if needed
	if (h > 128):
		t = ~(0x020000 - t)
	return t * varMultiplier

while True:
	changechannel(adc_address1, 0x9C)
	print ("Channel 1: %02f" % getadcreading(adc_address1,0x9C))
	changechannel(adc_address1, 0xBC)
	print ("Channel 2: %02f" % getadcreading(adc_address1,0xBC))
	changechannel(adc_address1, 0xDC)
	print ("Channel 3 :%02f" % getadcreading(adc_address1, 0xDC))
	changechannel(adc_address1, 0xFC)
	print ("Channel 4: %02f" % getadcreading(adc_address1, 0xFC))
	changechannel(adc_address2, 0x9C)
	print ("Channel 5: %02f" % getadcreading(adc_address2, 0x9C))
	changechannel(adc_address2, 0xBC)
	print ("Channel 6: %02f" % getadcreading(adc_address2, 0xBC))
	changechannel(adc_address2, 0xDC)
	print ("Channel 7: %02f" % getadcreading(adc_address2, 0xDC))
	changechannel(adc_address2, 0xFC)
	print ("Channel 8: %02f" % getadcreading(adc_address2, 0xFC))
