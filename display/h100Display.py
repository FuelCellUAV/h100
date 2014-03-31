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
        self.__cad = pifacecad.PiFaceCAD()

        # First define some pretty cutstom bitmaps!
        self.__temp_symbol_index = 7
        self.__temperature_symbol = pifacecad.LCDBitmap(
            [0x18, 0x18, 0x3, 0x4, 0x4, 0x4, 0x3, 0x0])

        # Save my pretty custom bitmaps to the memory (max 8 allowed)
        self.__cad.lcd.store_custom_bitmap(self.__temp_symbol_index, self.__temperature_symbol)

        # Start up the screen
        self.__on = False

        # Screen data
        self.__name = ''
        self.__state = ''
        self.__temp = ''
        self.__volts = ''
        self.__amps = ''


    @staticmethod
    def turnon(cad):

        # Start up the screen
        cad.lcd.blink_off()
        cad.lcd.cursor_off()
        cad.lcd.backlight_on()
        cad.lcd.clear()
        return True

    @staticmethod
    def turnoff(cad):

        # Close down the screen
        cad.lcd.home()
        cad.lcd.backlight_off()
        cad.lcd.clear()
        print('\n\nDisplay off\n\n')
        return False


    @property
    def on(self):
        return self.__on

    @on.setter
    def on(self, switch):
        if self.__on is True and switch is False:
            self.__on = self.turnoff(self.__cad)
        elif self.__on is False and switch is True:
            self.__on = self.turnon(self.__cad)

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, text):
        self.__name = self._update(self.__cad, text, [0, 0], 4)

    @property
    def state(self):
        return self.__state

    @state.setter
    def state(self, text):
        self.__state = self._update(self.__cad, text, [5, 0], 3)

    @property
    def temperature(self):
        return self.__temp

    @temperature.setter
    def temperature(self, number):
        self._update(self.__cad, self.__temperature_symbol, [13, 0], index=self.__temp_symbol_index)
        self.__temp = self._update(self.__cad, number, [9, 0], 4)

    @property
    def voltage(self):
        return self.__volts

    @voltage.setter
    def voltage(self, number):
        self._update(self.__cad, 'V', [4, 1], 1)
        self.__volts = self._update(self.__cad, number, [0, 1], 4)

    @property
    def current(self):
        return self.__amps

    @current.setter
    def current(self, number):
        self._update(self.__cad, 'A', [10, 1], 1)
        self.__amps = self._update(self.__cad, number, [6, 1], 4)

    @staticmethod
    def _update(cad, data, ptr, precision=1, index=-1):

        # Move cursor to correct place (col, row)
        cad.lcd.set_cursor(ptr[0], ptr[1])

        if type(data) is str:
            data = data[:precision].center(precision)

        elif type(data) is float or int:
            # Convert number to string
            data = str(data)
            # Truncate
            if len(data.split('.')[0]) > precision:
                # Replace with 'x' if too long
                data = 'x' * precision
            else:
                # Truncate and justify
                data = data[:precision].rjust(precision)

        if index < 0 and type(data) is str:
            cad.lcd.write(data)
            return data
        elif index >= 0:
            cad.lcd.write_custom_bitmap(index)
            return index

        raise AttributeError




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
