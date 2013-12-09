#!/usr/bin/env python3
import sys
import pifacecad

class FuelCellDisplay:
    cad = pifacecad.PiFaceCAD()
    temp_symbol_index = 0

    fcName  = 'H100'
    fcState = ''
    temp    = 10.0
    temperature_symbol = pifacecad.LCDBitmap(
        #[0x4, 0x4, 0x4, 0x4, 0xe, 0xe, 0xe, 0x0])
        [0x18,0x1b,0x4,0x4,0x4,0x4,0x3])
    power   = 000

    vFc     = 9.0
    iFc     = 10.0
    vBatt   = 0.0
    iBatt   = 0.0

    def __init__(self):
        self.cad.lcd.clear()
        self.cad.lcd.store_custom_bitmap(self.temp_symbol_index, self.temperature_symbol)
        self.cad.lcd.blink_off()
        self.cad.lcd.cursor_off()
        self.cad.lcd.backlight_on()

    def write(self):
        self.cad.lcd.home()
        self.cad.lcd.write('{:<4} {:^5} {:>4.1f}'.format(self.fcName, self.fcState, self.temp))
        self.cad.lcd.write_custom_bitmap(self.temp_symbol_index)
        self.cad.lcd.write('\n{:2.0f}V {:2.0f}A  {:>5.1f}W'.format(self.vFc, self.iFc, self.vFc*self.iFc))

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

