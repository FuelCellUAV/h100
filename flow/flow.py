#!/usr/bin/env python3

import multiprocessing
import serial
import time

class FlowBus232:
	def __init__(self):
		self.bus = serial.Serial("/dev/ttyAMA0",38400,timeout=5)

	def readLine(self):
		msg = ""
		ch = bus.read()
			if ch == ':':
				while ch != '\r':
					msg += ch
					# Dump the ':' and restart message if a new ':'
					# 	is received before last finishes
					if ch == ':':
						msg = ""
					ch = bus.read()
				return msg
			else:
				return False
				
	def decoder(self, msg, pointer):
		# import binascii
		return binascii.a2b_hex(msg[pointer:pointer+4])
				
	def parse232(self, msg):
		data[0] = decoder(msg,0)
		length = int(data[0],16)
		
		if length is 1:
			# Special error message
			return -1*int(decoder(msg,2), 16)
		
		for thisByte in range(1, length):
			data[thisByte] = decoder(msg,thisByte*4)
		
		return data
	
	def getValue(self, data, pointer):
		dataType = data[pointer]
		
		if b'00' in dataType:
			#char
			return int(data[pointer+2:pointer+4], 16)
		elif b'20' in dataType:
			#int
			return int(data[pointer+2:pointer+6], 16)
		elif b'40' in dataType:
			#float
		elif b'40' in dataType:
			#long
			return int(data[pointer+2:pointer+10], 16)
		elif b'60' in dataType:
			#string
			length = int(data[pointer+2:pointer+4], 16)
			mystring = ""
			for x in range(5, 5+length-1, 2):
				mystring += chr(int(data[x:x+2],16))
			
	
	def parse(self, data):
		length = int(data[0],16)
		node   = data[1]
		cmd    = data[2]
		
		if cmd is 0:
			#status message
			status = data[3]
			if status != 0:
				index = data[4]
				
		elif cmd is 2:
			#incoming data
			return getValue(data, 4)
		
		
		
		
		
		
		
		
		
		
		

class FlowBus232Daemon( FlowBus232 , multiprocessing.Process):
	val = multiprocessing.Array('d',range(8))

	def __init__(self):
		multiprocessing.Process.__init__(self)
		self.threadId = 1
		self.Name = 'FlowBus232'