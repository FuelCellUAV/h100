##!/usr/bin/env python3

# Fuel Cell Controller LCD display driver

# Copyright (C) 2013  Simon Howroyd
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

# A 'threaded' driver to allow the PiFace Control & Display board for the
# raspberryPi to run cleanly in the background. Data can be updated by
# calling the correct functions. In the main programme which imports this
# module, the following code is required to start the process:
#
# display = FuelCellDisplay(1, "My Process Name")
# display.daemon = True  # To ensure process is killed on Ctrl+c
# display.start()

import ctypes, fcntl, multiprocessing, pifacecad, socket, struct
import os, sys, signal, shlex, math, lirc
from threading import Barrier  # must be using Python 3
import subprocess
import pifacecommon
from pifacecad.lcd import LCD_WIDTH
from .radio import Radio

class FuelCellDisplay():
    def __init__(self):
        # Define the CAD board
        self._cad = pifacecad.PiFaceCAD()

        # First define some pretty cutstom bitmaps!
        self._temp_symbol_index = 7
        self._temperature_symbol = pifacecad.LCDBitmap(
            [0x18, 0x18, 0x3, 0x4, 0x4, 0x4, 0x3, 0x0])

        # Save my pretty custom bitmaps to the memory (max 8 allowed)
        self._cad.lcd.store_custom_bitmap(self._temp_symbol_index, self._temperature_symbol)

        # Start up the screen
        self._cad.lcd.blink_off()
        self._cad.lcd.cursor_off()
        self._cad.lcd.backlight_on()
        self._cad.lcd.clear()

        self._isOn = 1

    def setName(self, text):
        return self.__setText(text, 3, [0,0])
    def setState(self, text):
        return self.__setText(text, 3, [4,0])
    def setTemp(self, number):
#        self.__setSymbol(self._temperature_symbol, 1, [12,0])
        self.__update(self._temperature_symbol, [12,0], 0)
        return self.__setFloat(number, 4, [8,0])
    def setVolts(self, number):
        self.__setText('V', 1, [4,1])
        return self.__setFloat(number, 4, [0,1])
    def setAmps(self, number):
        self.__setText('A', 1, [10,1])
        return self.__setFloat(number, 4, [6,1])

    def off(self):
        # Close down the screen
        self._cad.lcd.home()
        self._cad.lcd.backlight_off()
        self._cad.lcd.clear()
        print('\n\nDisplay off\n\n')

    def __setText(self, text, chars, ptr):
        # Truncate
        text = text[:chars].center(chars)
        # Update display
        return self.__update(text, ptr)

    def __setFloat(self, number, chars, ptr):
        # Convert number to string
        numstr = str(number)
        # Truncate
        if len(str(numstr).split('.')[0]) > chars:
            # Replace with 'x' if too long
            numstr = "x" * chars
        else:
            # Truncate and justify
            numstr = numstr[:chars].rjust(chars)
        # Update display
        return self.__update(numstr, ptr)

    def __setSymbol(self, symbol, chars, ptr):
        # Truncate, justify & update display
        return self.__update(symbol[:chars].ljust(chars), ptr)

    def __update(self, text, ptr, index=-1):
        # Move cursor to correct place (col, row)
        self._cad.lcd.set_cursor(ptr[0], ptr[1])
        # Write text to screen
        if self._isOn:
            if index < 0: self._cad.lcd.write(text)
            else: self._cad.lcd.write_custom_bitmap(index)
        return text





class FuelCellDisplayRadio(FuelCellDisplay):
    def __init__(self):
        # Initialise the fuel cell display
        super().__init__()
        
        self.UPDATE_INTERVAL = 1
        self.STATIONS = [
            {'name': "6 Music",
             'source': 'http://www.bbc.co.uk/radio/listen/live/r6_aaclca.pls',
             'info': 'http://www.bbc.co.uk/radio/player/bbc_6music'},
            {'name': "Radio 2",
             'source': 'http://www.bbc.co.uk/radio/listen/live/r2_aaclca.pls',
             'info': None},
            {'name': "Radio 4",
             'source': 'http://www.bbc.co.uk/radio/listen/live/r4_aaclca.pls',
             'info': None},
            {'name': "5 Live",
             'source': 'http://www.bbc.co.uk/radio/listen/live/r5l_aaclca.pls',
             'info': None},
            {'name': "Radio 4 Extra",
             'source': 'http://www.bbc.co.uk/radio/listen/live/r4x_aaclca.pls',
             'info': None},
            {'name': "Planet Rock",
             'source': 'http://tx.sharp-stream.com/icecast.php?i=planetrock.mp3',
             'info': None},
        ]
        
        # Custom radio symbols
        self.PLAY_SYMBOL = pifacecad.LCDBitmap(
            [0x10, 0x18, 0x1c, 0x1e, 0x1c, 0x18, 0x10, 0x0])
        self.PAUSE_SYMBOL = pifacecad.LCDBitmap(
            [0x0, 0x1b, 0x1b, 0x1b, 0x1b, 0x1b, 0x0, 0x0])
        self.INFO_SYMBOL = pifacecad.LCDBitmap(
            [0x6, 0x6, 0x0, 0x1e, 0xe, 0xe, 0xe, 0x1f])
        self.MUSIC_SYMBOL = pifacecad.LCDBitmap(
            [0x2, 0x3, 0x2, 0x2, 0xe, 0x1e, 0xc, 0x0])

        self.PLAY_SYMBOL_INDEX = 0
        self.PAUSE_SYMBOL_INDEX = 1
        self.INFO_SYMBOL_INDEX = 2
        self.MUSIC_SYMBOL_INDEX = 3

    def radio_preset_switch(event):
        global radio
        radio.change_station(event.pin_num)

    def startRadio(self):
        # test for mpalyer
        try:
            subprocess.call(["mplayer"], stdout=open('/dev/null'))
        except OSError as e:
            if e.errno == os.errno.ENOENT:
                print(
                    "MPlayer was not found, install with "
                    "`sudo apt-get install mplayer`")
                #sys.exit(1)
                return -1
            else:
                raise  # Something else went wrong while trying to run `mplayer`

        global radio
        radio = Radio(self._cad)
        radio.play()
    
        # listener cannot deactivate itself so we have to wait until it has
        # finished using a barrier.
        global end_barrier
        end_barrier = Barrier(2)
    
        # wait for button presses
        self.switchlistener = pifacecad.SwitchEventListener(chip=self._cad)
        for pstation in range(4):
            self.switchlistener.register(
                pstation, pifacecad.IODIR_ON, self.radio_preset_switch)
        self.switchlistener.register(4, pifacecad.IODIR_ON, end_barrier.wait)
        self.switchlistener.register(5, pifacecad.IODIR_ON, radio.toggle_playing)
        self.switchlistener.register(6, pifacecad.IODIR_ON, radio.previous_station)
        self.switchlistener.register(7, pifacecad.IODIR_ON, radio.next_station)
    
        self.switchlistener.activate()

    def stopRadio(self):
        try:
            # exit
            radio.close()
            switchlistener.deactivate()
            if irlistener_activated:
                irlistener.deactivate()
        except NameError: pass

    def off(self):
        self.stopRadio()
        # Close down the screen
        self._cad.lcd.home()
        self._cad.lcd.backlight_off()
        self._cad.lcd.clear()
        print('\n\nDisplay off\n\n')


# Fuel Cell Display Module
class FuelCellDisplayDaemon(FuelCellDisplay, multiprocessing.Process):
    # This runs once when the class is created
    def __init__(self, threadID, name):
        # Initialise the multiprocess utility
        multiprocessing.Process.__init__(self)
        self.threadID = threadID
        self.name = name

        super().__init__()
        # If the user presses button 5 display the ip address

    #        self.ip_display_flag = False
     #   self.listener = pifacecad.SwitchEventListener(chip=self.cad)
    #    self.listener.register(0, pifacecad.IODIR_OFF,self.cad.lcd.write('Hello world!'))
    #     self.listener.register(0, pifacecad.IODIR_ON, self.cad.lcd.clear())
    #    self.listener.activate()

    # This is the main process loop called by start()
    def run(self):
        counter = 0
        try:
            while True: pass
                # A statement for my pretty bitmap animation
#                self.cad.lcd.write_custom_bitmap(self.progress_index[counter])
#                if counter < 6:
#                    counter += 1
#                else:
#                    counter = 0
        finally:
            self.off()

    # The following is all TODO

    # Get my current ip address, takes 'lo' or 'eth0' or 'wlan0' etc
    def get_ip_address(self, ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15])
        )[20:24])

    def print_ip_address(self):
        self.cad.lcd.home()
        #        self.cad.lcd.clear()
        self.cad.lcd.write('Hello world!')
        return
        self.cad.lcd.write('e{:}\n'.format(self.get_ip_address('eth0')))
        self.cad.lcd.write('w{:}\n'.format(self.get_ip_address('wlan0')))

    def ip_on(self):
        self.ip_display_flag = True
        self.print_ip_address()

    def ip_off(self):
        self.ip_display_flag = False
