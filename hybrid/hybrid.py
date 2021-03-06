##!/usr/bin/env python3
# Re-written by Simon Howroyd 2015 for Loughborough University

# Must call the update method on each loop of the main code

import sys
sys.path.append("..") # Adds higher directory to python modules path.
import quick2wire.i2c as i2c
from adc.adcpi import MCP3424

class HybridIo:
    def __init__(self):
        self.__address = 0x20
        
        self.__bit_register       = [0b01000100, 0b00000000]
        self.__direction_register = [0b00011100, 0b00000000] # Output is 0, input is 1

        try:
            with i2c.I2CMaster(1) as bus:
                bus.transaction(
                    i2c.writing(self.__address, [6, self.__direction_register[0], self.__direction_register[1]]))
        except IOError:
            print("Err: No hybridIO detected")
            return

        self.change_output()


        # IO register. > means output, < means input.
        # Port 0:       Port 1:
        # 0: 3C4C>      12V>
        # 1: CHEM>      12V>
        # 2: <LOBAT     12V>
        # 3: <ICL       5V>
        # 4: <ACP       3V3>
        # 5: SHDN>      GND>
        # 6: <FAULT     GND>
        # 7: <CHG       GND>
        
    def update(self):
        try:
            with i2c.I2CMaster(1) as bus:
                data = bus.transaction(
                        i2c.writing_bytes(self.__address, 0),
                        i2c.reading(self.__address, 2))[0]
            self.__bit_register = data
            return self.__bit_register
        except IOError:
 #           print("Err: No hybridIO detected")
            return -1

    def get_charger_state_string(self):
        x = "Chg: "
        if self.CHG or self.SHDN: x += "OFF ["
        else : x += "CHARGING ["
#        if self.SHDN: x += "SHDN "
        if not self.LOBAT: x += "LOBAT "
        if not self.ICL: x += "I-LIMITING "
        if not self.ACP: x += "DCIN-TOO-LOW "
        if not self.FAULT: x += "HOT-OR-TOO-LOBAT "
        x += "] "
        if self.CELLS: x += "4cell "
        else: x += "3cell "
        if self.CHEM: x += "4.2V/cell "
        else: x += "4.1V/cell "
        return x

    @property
    def power1(self):
        return self._get_bit(self.bit_register[1], 0)
    @power1.setter
    def power1(self, state):
        self.bit_register = [1, 0, state]
    @property
    def power2(self):
        return self._get_bit(self.bit_register[1], 1)
    @power2.setter
    def power2(self, state):
        self.bit_register = [1, 1, state]
    @property
    def power3(self):
        return self._get_bit(self.bit_register[1], 2)
    @power3.setter
    def power3(self, state):
        self.bit_register = [1, 2, state]
    @property
    def power4(self):
        return self._get_bit(self.bit_register[1], 3)
    @power4.setter
    def power4(self, state):
        self.bit_register = [1, 3, state]
    @property
    def power5(self):
        return self._get_bit(self.bit_register[1], 4)
    @power5.setter
    def power5(self, state):
        self.bit_register = [1, 4, state]
        
    @property
    def SHDN(self):
        # High is shutdown, low is OK to start charging
        return self._get_bit(self.bit_register[0], 5)
    @SHDN.setter
    def SHDN(self, state):
        # High is shutdown, low is OK to start charging
        self.bit_register = [0, 5, state]
    @property
    def CELLS(self):
        # High is 4cell, low is 3cell
        return self._get_bit(self.bit_register[0], 0)
    @CELLS.setter
    def CELLS(self, state):
        # High is 4cell, low is 3cell
        self.bit_register = [0, 0, state]
    @property
    def CHEM(self):
        # High is 4.2v/cell, low is 4.1v/cell
        return self._get_bit(self.bit_register[0], 1)
    @CHEM.setter
    def CHEM(self, state):
        # High is 4.2v/cell, low is 4.1v/cell
        self.bit_register = [0, 1, state]
    @property
    def LOBAT(self):
        # High is OK, low is very low v/cell
        return self._get_bit(self.bit_register[0], 2)
    @property
    def ICL(self):
        # High is unlimited, low is internal current limiting
        return self._get_bit(self.bit_register[0], 3)
    @property
    def ACP(self):
        # High is OK, low is DCIN is too low to charge battery
        return self._get_bit(self.bit_register[0], 4)
    @property
    def FAULT(self):
        # High is OK, low is charging stopped (too hot or LOBAT error)
        return self._get_bit(self.bit_register[0], 6)
    @property
    def CHG(self):
        # High is not charging, low is charging
        return self._get_bit(self.bit_register[0], 7)
       
    @property
    def bit_register(self):
        return self.__bit_register
    @bit_register.setter
    def bit_register(self, data):#port, bit, state):
        try:
            port, bit, state = data
        except ValueError:
            raise ValueError("Invalid HybridIO register command")
        else:
            if state is 1:
                # Set bit high
                if port is 0:
                    self.__bit_register = [self.__bit_register[0] | (1 << bit), self.__bit_register[1]]
                elif port is 1:
                    self.__bit_register = [self.__bit_register[0], self.__bit_register[1] | (1 << bit)]
                else:
                    print("Bad port request")
            elif state is 0:
                if bool( (self.__bit_register[port] >> bit) & 0b00000001) is True:
                    # Set bit low
                    if port is 0:
                        self.__bit_register = [self.__bit_register[0] ^ (1 << bit), self.__bit_register[1]]
                    elif port is 1:
                        self.__bit_register = [self.__bit_register[0], self.__bit_register[1] ^ (1 << bit)]
                    else:
                        print("Bad port request")
                else:
                    # Bit already set
                    return
            else:
                # State must be 1 or 0
                print("Error in bit register setter")
            self.change_output()

    def change_output(self):
        try:
            with i2c.I2CMaster(1) as bus:
                bus.transaction(
                    i2c.writing(self.__address, bytearray([2, self.__bit_register[0], self.__bit_register[1]])))
            return self.__bit_register
        except IOError:
#            print("Err: No hybridIO detected")
            return -1
        
    @staticmethod
    def _get_bit(register, bit):
        return bool((register >> bit) & 0b00000001)
        


class Charge_Controller:
    def __init__(self):
        self.__address = 0x2F
        self.__current = 0.0
        self.current   = 0.0

    @staticmethod
    def current_to_hex(current):
        return 0xFF # TODO remove this blocker
        resistance = (1.19 * 3010) / (current*0.025 + 0.035)
        if resistance > 50000: resistance = 50000
        return hex(resistance/50000 * 255)

    @property
    def current(self):
        return self.__current
    @current.setter
    def current(self, cur):
        if (cur > 4.0 or cur < 0.0):
            raise ValueError
        else:
            if self.__changecurrent([self.__address,
                                     self.current_to_hex(cur)]) >= 0:
                self.__current = cur
            
    # Method to change the I2C POT resistance
    @staticmethod
    def __changecurrent(config):
        try:
            # Using the I2C databus...
            with i2c.I2CMaster(1) as master:
                master.transaction(
                    i2c.writing_bytes(config[0], config[1]))
            return config[1]
                    
        # If I2C error return
        except IOError:
            print("Err: No POT detected")
            return -1

class Adc:
    def __init__(self, res=12):
        self.__adc1 = MCP3424(0x68, res)
        self.__adc2 = MCP3424(0x6C, res)

        self.__voltage_scale   = 5.458;
        self.__charge_i_scale  = 1 / 33.36 / 0.025
        self.__fc_i_scale      = -220.0 / 40.21 / 0.01

        self.__t1              = 0.0
        self.__t2              = 0.0
        self.__fc_voltage      = 0.0
        self.__battery_voltage = 0.0
        self.__output_voltage  = 0.0
        self.__fc_current      = 0.0
        self.__charge_current  = 0.0
        self.__output_current  = 0.0
        
        self.update()
        
    def update(self):
        # ADC 1
        self.__charge_current  = self.__adc1.get(0) #* self.__charge_i_scale
        self.__output_current  = self.__adc1.get(1,8)# - 5.1 # * 0.0267 # Must subtract Vcc/2 scaled
        self.__fc_current      = (self.__adc1.get(2) * 3.817)# - 2.04) / -0.0157
        self.__t1              = self.__adc1.get(3)

#        print(str(self.__fc_current)[:5] + ' ' + str(self.__charge_current)[:5] + ' ' + str(self.__output_current)[:5])

        # ADC 2
        self.__battery_voltage = self.__adc2.get(0) * self.__voltage_scale
        self.__output_voltage  = self.__adc2.get(1) * self.__voltage_scale
        self.__fc_voltage      = self.__adc2.get(2) * self.__voltage_scale
        self.__t2              = self.__adc2.get(3) * self.__voltage_scale

#        if self.__battery_voltage >= 0.0: self.__battery_voltage *= self.__voltage_scale
#        if self.__output_voltage >= 0.0:  self.__output_voltage  *= self.__voltage_scale
#        if self.__fc_voltage >= 0.0:      self.__fc_voltage      *= self.__voltage_scale_fc
#        if self.__t2 >= 0.0:              self.__t2              *= self.__voltage_scale

        return
        
    @property # Charging current
    def charge_current(self):
        return self.__charge_current
    @property # Hybrid output current
    def output_current(self):
        return self.__output_current
    @property # Fuel Cell output current
    def fc_current(self):
        return self.__fc_current
    @property # PCB Temperature sensor 1
    def pcb_temp1(self):
        return self.__t1
    @property # Battery voltage
    def battery_voltage(self):
        return self.__battery_voltage
    @property # Hybrid output voltage
    def output_voltage(self):
        return self.__output_voltage
    @property # Fuel Cell voltage
    def fc_voltage(self):
        return self.__fc_voltage
    @property # PCB Temperature sensor 2
    def pcb_temp2(self):
        return self.__t2

class Hybrid:
    def __init__(self):
        self.__io      = HybridIo()
        self.__adc     = Adc()
        self.__charger = Charge_Controller()
        self.__charger.current = 1.0 # Probably not needed
        self.__charger_state = False
        self.cells = 3
        self.chem  = 4.2
        self.__io.CHEM = 1


    def shutdown(self):
        self.__io.SHDN = 1
        
    def update(self):
        # Input/Outputs
        if not self.__io.update(): return -1
        # ADCs
        self.__adc.update()

#        if self.__charger_state is True:
#            print("High")
#            self.__io.SHDN = 1
#            self.cells = 4
#            self.__charger_state = False
#        elif self.__charger_state is False:
#            print("Low")
#            self.__io.SHDN = 0
#            self.cells = 3
#            self.__charger_state = True
#        return

        # Charger
#        if self.__charger_state and self.battery_voltage > 5.0:
#            self.__io.SHDN = 0
#        else: self.__io.SHDN = 1
        # Charger controller
        if self.fc_current_total>=0.0:
            overhead = 8.5 - self.fc_current_total
            if (overhead < 0.0): overhead = 0.0
            if (overhead >= 4.0 and self.__charger.current <= 3.8):
                self.__charger.current = self.__charger.current + 0.2 # Is this ramp necessary?
            # TODO: Need checks of charger IO here

        self.charger_state = False

#        print(self.charger_state)
        
    def fan_on(self):    self.__io.power1 = 1
    def fan_off(self):   self.__io.power1 = 0
    def h2_on(self):     self.__io.power2 = 1
    def h2_off(self):    self.__io.power2 = 0
    def purge_on(self):  self.__io.power3 = 1
    def purge_off(self): self.__io.power3 = 0
        
    # Turn charger on/off
    @property
    def charger_state(self):
        if self.battery_voltage > 5.0:
            return self.__io.get_charger_state_string()
        else: return "Chg: BATT NOT PLUGGED IN"
    @charger_state.setter
    def charger_state(self, state):
        if state is True:
            self.__io.SHDN = 0
            self.__charger_state = True
        else:
            self.__io.SHDN = 1
            self.__charger_state = False

    @property
    def t1(self):
        return self.__adc.pcb_temp1
    @property
    def t2(self):
        return self.__adc.pcb_temp2
    @property
    def fc_voltage(self):
        return self.__adc.fc_voltage
    @property
    def battery_voltage(self):
        return self.__adc.battery_voltage
    @property
    def output_voltage(self):
        return self.__adc.output_voltage
    @property
    def fc_current_to_motor(self):
        return self.__adc.fc_current
    @property
    def fc_current_total(self):
        if (self.__adc.fc_current<0 or self.__adc.charge_current<0):
            return -1
        else:
            return self.__adc.fc_current + self.__adc.charge_current
    @property
    def battery_current(self):
        if (self.__adc.output_current<0 or self.fc_current_total<0):
            return -1
        else:
            return self.__adc.output_current - self.fc_current_total
    @property
    def charge_current(self):
        return self.__adc.charge_current
    @property
    def output_current(self):
        return self.__adc.output_current
    
    @property
    def cells(self):
        if self.__io.CELLS is True:
            return 4
        else:
            return 3
    @cells.setter
    def cells(self, cells):
        if int(cells) is 4:
            self.__io.CELLS = 1
        elif int(cells) is 3:
            self.__io.CELLS = 0
        else:
            print("Wrong cell count selected: " + str(cells))
    
    @property
    def charged_voltage(self):
        if self.__io.CHEM is True:
            return 4.2
        else:
            return 4.1
    @charged_voltage.setter
    def charged_voltage(self, voltage):
        if abs(voltage-4.2)<0.01: # Comparing floats
            self.__io.CHEM = 1
        elif abs(voltage-4.1)<0.01:
            self.__io.CHEM = 0
        else:
            print("Wrong cell chemistry selected: " + str(voltage))
