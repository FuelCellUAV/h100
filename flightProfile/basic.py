#!/usr/bin/python2

# Basic Flight Profile

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

#basic flight profile
#throttle is not considered at this stage, constant rates are assumed
#altitude will come from gps reading in air tests

import time
import interface

class BasicProfile(Interface): # Inherits the functionality of "Interface"
	#Initialise
	def __init__(self):
		#Runs automatically at start of programme
		print ('Initialising flight profile')
		self.ground_alt = 2
		self.alt = 0
		self.cruise_alt = 15
		self.cruise_time = 10
		self.timeStart = time.time()
		self.timeRun = 0
		self.safetyChecks = False
		self.SafetyCheck()
		return

	#**FLIGHT PROFILE**
	def run(self):
		if self.safetyChecks == False:
			print ("Can't run, safety check failed at init")
			break # Don't allow this to run if not safe
			
		if self.runtime() < 5:
			# Do nothing yet, ready to go!
		elif self.runtime() < 15:
			# Takeoff
			self.alt = Interface.climb(self.alt, 2)# 2m/s climb
		elif self.runtime() < 360:
			# Cruise
			Interface.setClimbRate(1) # 1m/s climb
			Interface.setDecRate(1)   # 1m/s descent
			self.alt = Interface.cruise(self.alt, self.cruise_alt)
		elif self.runtime() < 420:
			# Land
			self.Landing
		else:
			self.Shutdown()

	#Safety Check
	def SafetyCheck(self):
		print ('Starting Safety Checks')
		try:
			# Do checks here #
			self.safetyChecks = True # All ok
		except Exception as e:
			self.safetyChecks = False # Went wrong
		return
		
	#Landing - special method needed to account for ground
	def Landing(self):
		Interface.setDecRate(1) # 1m/s
		if self.alt > self.ground_alt:
			print('Landing')
			self.alt = Interface.descend(self.alt)
		else:
			print ("On ground")
		return self.alt
		
	#Shut Down
	def Shutdown(self):
		print ('Shutting Down')
		#shut down
		print ('Shut Down Good Bye')
		return
		
	# Time since start of profile
	def runtime(self):
		# Calc real time since start
		self.timeRun = time.time() - self.timeStart
		return self.timeRun