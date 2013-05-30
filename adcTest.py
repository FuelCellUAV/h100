import smbus
import time
import sys

ADC1 = 0x68
ADC2 = 0x69

ch1 = 0x98
ch2 = 0xB8
ch3 = 0xD8
ch4 = 0xF8

bus = smbus.SMBus(0)

def read(add,ch):
	bus.write_byte(add,ch)
	dataIn = bus.read_i2c_block_data(add,ch,3)
	msb = dataIn[0]
	lsb = dataIn[1]
	config = dataIn[2]
	
	#while (config & 128):
	#	dataIn = bus.read_i2c_block_data(add,ch,3)
	#	msb = dataIn[0]
	#	lsb = dataIn[1]
	#	config = dataIn[2]

	adc = (msb<<8) | lsb
	return adc

while True:
	print '\r',
	#print '\t1={}'.format(read(ADC1,ch1)),
	#print '\t2={}'.format(read(ADC1,ch2)),
	#print '\t3={}'.format(read(ADC1,ch3)),
	#print '\t4={}'.format(read(ADC1,ch4)),
	#print '\t5={}'.format(read(ADC2,ch1)),
	#print '\t6={}'.format(read(ADC2,ch2)),
	#print '\t7={}'.format(read(ADC2,ch3)),
	print '\t8={}'.format(read(ADC2,ch4)),
		
