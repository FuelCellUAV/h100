#!/usr/bin/python2

# Flight Profile Control Interface

# Copyright (C) 2013  India Barber
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

#Time
import time

class FlightInterface:
	def __init__(self)
		# This function runs automatically when programme started
		self.climbRate = 1 # m/s
		self.decRate   = 1 # m/s
		self.timeLast = time.time() # Time at last computation
		self.delta = 0 # Time since last computation
	
	# Time delta
	def delta(self):
		# Calc real time since last computational cycle
		self.delta = time.time() - self.timeLast
		self.timeLast = time.time()
		return self.delta
	
	#Climb
	def climb(self, alt, rate):
		print ('Climbing')
		self.delta()
		alt += (self.climbRate=rate) * self.delta # Calc real alt change
		#time.sleep(1)
		print ('alt: ',alt)
		return alt

	#Descend
	def descend(self, alt, rate):
		print ('Descending')
		self.delta()
		alt -= (self.decRate=rate) * self.delta # Calc real alt change
		#time.sleep(1)
		print ('alt: ',alt)
		return alt

	#Cruise
	def cruise(self, alt, cruise_alt):
		print ('Cruising')
		if alt > cruise_alt:
			print("Above cruise alt")
			self.descend()
		elif alt < cruise_alt:
			print("Below cruise alt")
			self.climb()
		else
			self.delta()
		return alt
		
    # Change Climb Rate "on the fly"
	def setClimbRate(self, climbRate)
		self.climbRate = climbRate
		
	# Change Descent Rate "on the fly"
	def setDecRate(self, decRate)
		self.decRate = decRate