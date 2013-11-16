#basic flight profile
#throttle is not considered at this stage but + 1 is added to altitude
#altitude will come fromg gps reading
#controller can be inputted into 'initialise' 'safety check' and 'shut down' stages

#Time
import time

#Global Variables
ground_alt = 2
alt = 0
cruise_alt = 15
cruise_time = 10

#Climb
def climb(alt):
    print ('Climbing')
    alt += 1
    time.sleep(1)
    print ('alt: ',alt)
    return alt

#Descend
def descend(alt):
    print ('Descending')
    alt = alt - 1
    time.sleep(1)
    print ('alt: ',alt)
    return alt

#Cruise
def cruise(alt, cruise_alt):
    t = 0
    print('Cruising for ', cruise_time, ' seconds')
    while (t<cruise_time):
        # adding a gust
        if (t==3):
            alt += 4
            print('Upgust')
            print('alt: ', alt)
        # adding a downgust
        if (t==5):
            alt += -5
            print('Downgust')
            print('alt: ', alt)
            
        if (alt == cruise_alt):
            t = t + 1
            time.sleep(1)
            print('Cruising')
            print ('alt: ',alt)
        elif (alt < cruise_alt):
            alt = climb(alt)
            t = t + 1
            time.sleep(1)
        elif (alt > cruise_alt):
            alt = descend(alt)
            t = t + 1
            time.sleep(1)
    return alt

#Initialise
def Initialise():
    print ('Initialising')
    return

#SafetyCheck
def SafetyCheck():
    print ('Safety Checks')
    return

#Shut Down
def Shutdown():
    print ('Shutting Down')
    #shut down
    print ('Shut Down Good Bye')
    return

#Takeoff
def Takeoff(alt, cruise_alt):
    print('Starting Takeoff')
    while (alt < cruise_alt):
        alt = climb(alt)
    return alt

#Landing
def Landing(alt, ground_alt):
    print('Starting Landing')
    while (alt > ground_alt):
        alt = descend(alt)
    return alt

#Flight

Initialise()

SafetyCheck()

#Possibly add in button to press to start

alt = Takeoff(alt, cruise_alt)

alt = cruise(alt, cruise_alt)

alt = Landing(alt, ground_alt)

Shutdown()


    













