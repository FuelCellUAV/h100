import ctypes, fcntl, multiprocessing, pifacecad, socket, struct
import os, sys, signal, shlex, math, lirc
from threading import Barrier  # must be using Python 3
import subprocess
import pifacecommon
from pifacecad.lcd import LCD_WIDTH


class Radio(object):
    def __init__(self, cad, start_station=0):
        self.current_station_index = start_station
        self.playing_process = None

        # set up cad
        cad.lcd.blink_off()
        cad.lcd.cursor_off()
        cad.lcd.backlight_on()

        cad.lcd.store_custom_bitmap(PLAY_SYMBOL_INDEX, PLAY_SYMBOL)
        cad.lcd.store_custom_bitmap(PAUSE_SYMBOL_INDEX, PAUSE_SYMBOL)
        cad.lcd.store_custom_bitmap(INFO_SYMBOL_INDEX, INFO_SYMBOL)
        self.cad = cad

    @property
    def current_station(self):
        """Returns the current station dict."""
        return STATIONS[self.current_station_index]

    @property
    def playing(self):
        return self._is_playing

    @playing.setter
    def playing(self, should_play):
        if should_play:
            self.play()
        else:
            self.stop()

    @property
    def text_status(self):
        """Returns a text represenation of the playing status."""
        if self.playing:
            return "Now Playing"
        else:
            return "Stopped"

    def play(self):
        """Plays the current radio station."""
        print("Playing {}.".format(self.current_station['name']))
        play_command = "mplayer -quiet {stationsource}".format(
            stationsource=self.current_station['source'])
        self.playing_process = subprocess.Popen(
            play_command,
            #stdout=subprocess.PIPE,
            #stderr=subprocess.PIPE,
            shell=True,
            preexec_fn=os.setsid)
        self._is_playing = True
        self.update_display()

    def stop(self):
        """Stops the current radio station."""
        print("Stopping radio.")
        os.killpg(self.playing_process.pid, signal.SIGTERM)
        self._is_playing = False
        self.update_playing()

    def change_station(self, new_station_index):
        """Change the station index."""
        was_playing = self.playing
        if was_playing:
            self.stop()
        self.current_station_index = new_station_index % len(STATIONS)
        if was_playing:
            self.play()

    def next_station(self, event=None):
        self.change_station(self.current_station_index + 1)

    def previous_station(self, event=None):
        self.change_station(self.current_station_index - 1)

    def update_display(self):
        self.update_station()
        self.update_playing()
        # self.update_volume()

    def update_playing(self):
        """Updated the playing status."""
        #message = self.text_status.ljust(LCD_WIDTH-1)
        #self.cad.lcd.write(message)
        if self.playing:
            char_index = PLAY_SYMBOL_INDEX
        else:
            char_index = PAUSE_SYMBOL_INDEX

        self.cad.lcd.set_cursor(0, 0)
        self.cad.lcd.write_custom_bitmap(char_index)

    def update_station(self):
        """Updates the station status."""
        message = self.current_station['name'].ljust(LCD_WIDTH-1)
        self.cad.lcd.set_cursor(1, 0)
        self.cad.lcd.write(message)

    def toggle_playing(self, event=None):
        if self.playing:
            self.stop()
        else:
            self.play()

    def close(self):
        self.stop()
        self.cad.lcd.clear()
        self.cad.lcd.backlight_off()

