#!/usr/bin/env python3
import sys
import pifacecad
import threading
from time import sleep

class FuelCellDisplay (threading.Thread):
    cad = pifacecad.PiFaceCAD()
    temp_symbol_index = 0
    progress_symbol_1 = 1
    progress_symbol_2 = 2
    progress_symbol_3 = 3
    progress_symbol_4 = 4
    progress_symbol_5 = 5
    progress_symbol_6 = 6
    progress_symbol_7 = 7
    temperature_symbol = pifacecad.LCDBitmap(
        #[0x4, 0x4, 0x4, 0x4, 0xe, 0xe, 0xe, 0x0])
        [0x18,0x1b,0x4,0x4,0x4,0x3,0x0])
    progress_1 = pifacecad.LCDBitmap(
        [0x0,0x0,0x0,0x0,0x0,0x0,0x1f])
    progress_2 = pifacecad.LCDBitmap(
        [0x0,0x0,0x0,0x0,0x0,0x1f,0x1f])
    progress_3 = pifacecad.LCDBitmap(
        [0x0,0x0,0x0,0x0,0x1f,0x1f,0x1f])
    progress_4 = pifacecad.LCDBitmap(
        [0x0,0x0,0x0,0x1f,0x1f,0x1f,0x1f])
    progress_5 = pifacecad.LCDBitmap(
        [0x0,0x0,0x1f,0x1f,0x1f,0x1f,0x1f])
    progress_6 = pifacecad.LCDBitmap(
        [0x0,0x1f,0x1f,0x1f,0x1f,0x1f,0x1f])
    progress_7 = pifacecad.LCDBitmap(
        [0x1f,0x1f,0x1f,0x1f,0x1f,0x1f,0x1f])

    fcName  = 'H100'
    fcState = ''
    temp    = 10.0
    power   = 000
    vFc     = 9.0
    iFc     = 10.0
    vBatt   = 0.0
    iBatt   = 0.0

    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name     = name
        self.counter  = counter
        self.cad.lcd.clear()
        self.cad.lcd.store_custom_bitmap(self.temp_symbol_index, self.temperature_symbol)
        self.cad.lcd.store_custom_bitmap(self.progress_symbol_1, self.progress_1)
        self.cad.lcd.store_custom_bitmap(self.progress_symbol_2, self.progress_2)
        self.cad.lcd.store_custom_bitmap(self.progress_symbol_3, self.progress_3)
        self.cad.lcd.store_custom_bitmap(self.progress_symbol_4, self.progress_4)
        self.cad.lcd.store_custom_bitmap(self.progress_symbol_5, self.progress_5)
        self.cad.lcd.store_custom_bitmap(self.progress_symbol_6, self.progress_6)
        self.cad.lcd.store_custom_bitmap(self.progress_symbol_7, self.progress_7)
        self.cad.lcd.blink_off()
        self.cad.lcd.cursor_off()
        self.cad.lcd.backlight_on()

    def run(self):
        while(True):
#            self.counter = self.counter + 1
            self.cad.lcd.home()
            self.cad.lcd.write('{:<4} {:^3} {:>4.1f}'.format(self.fcName, self.fcState, self.temp))
            self.cad.lcd.write_custom_bitmap(self.temp_symbol_index)
            self.cad.lcd.write(' ')

            if self.counter is 1:
                self.cad.lcd.write_custom_bitmap(self.progress_symbol_1)
                #self.cad.lcd.write('{:1}'.format(self.counter))
                self.counter = self.counter + 1
            elif self.counter is 2:
                self.cad.lcd.write_custom_bitmap(self.progress_symbol_2)
                #self.cad.lcd.write('{:1}'.format(self.counter))
                self.counter = self.counter + 1
            elif self.counter is 3:
                self.cad.lcd.write_custom_bitmap(self.progress_symbol_3)
                #self.cad.lcd.write('{:1}'.format(self.counter))
                self.counter = self.counter + 1
            elif self.counter is 4:
                self.cad.lcd.write_custom_bitmap(self.progress_symbol_4)
                #self.cad.lcd.write('{:1}'.format(self.counter))
                self.counter = self.counter + 1
            elif self.counter is 5:
                self.cad.lcd.write_custom_bitmap(self.progress_symbol_5)
                #self.cad.lcd.write('{:1}'.format(self.counter))
                self.counter = self.counter + 1
            elif self.counter is 6:
                self.cad.lcd.write_custom_bitmap(self.progress_symbol_6)
                #self.cad.lcd.write('{:1}'.format(self.counter))
                self.counter = self.counter + 1
            elif self.counter is 7:
                self.cad.lcd.write_custom_bitmap(self.progress_symbol_7)
                #self.cad.lcd.write('{:1}'.format(self.counter))
                self.counter = 1

            self.cad.lcd.write(' {:1}'.format(self.counter))
            self.cad.lcd.write('\n{:2.0f}V {:2.0f}A  {:>5.1f}W'.format(self.vFc, self.iFc, self.vFc*self.iFc))
            #sleep(1)

    def stop(self):
        self._Thread__stop()

#    def name(self, fcName):
 #       self.fcName = fcName
  #      return

    def state(self, fcState):
        self.fcState = fcState[:5]
        return

    def temperature(self, temperature):
        self.temp = temperature
        return

    def voltage(self, voltage):
        self.vFc = voltage
        return

    def current(self, current):
        self.iFc = current
        return

    def __exit__(self):
        self.cad.lcd.clear()
        self.cad.lcd.backlight_off()        
