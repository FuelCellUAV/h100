#!/usr/bin/env python3
# Re-written by Simon Howroyd 2014 for Loughborough University

# Must call the update method on each loop of the main code

import quick2wire.i2c as i2c
import adcpi.MCP3424 as MCP3424

class HybridIo:
    def __init__(self):
        self.__address = 0x20
        
        self.__bit_register       = [0b01000100, 0b00000000]
        self.__direction_register = [0b00111011, 0b00000000] # Output is 0, input is 1

        with i2c.I2CMaster() as bus:
            bus.transaction(
                i2c.write_word_data(self.__address, 6, ((self.__direction_register[0] << 8) | self.__direction_register[1]))
                
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
        with i2c.I2CMaster() as bus:
            data = bus.transaction(
                    i2c.writing_bytes(config[0], config[1]),
                    i2c.reading(self.__address, 2))[0]
        self.__bit_register = data
        return
    
    def change_output(self):
        with i2c.I2CMaster() as bus:
            bus.transaction(
                i2c.write_word_data(self.__address, 2, ((self.__bit_register[0] << 8) | self.__bit_register[1]))
        return
        
    @staticmethod
    def _get_bit(register, bit):
        return bool((register >> bit) & 0b00000001)
        
    @property
    def power1(self):
        return self._get_bit(self.bit_register[1], 0)
    @power1.setter
    def power1(self, state):
        self.bit_register = ( 1, 0, state)
    @property
    def power2(self):
        return self._get_bit(self.bit_register[1], 1)
    @power2.setter
    def power2(self, state):
        self.bit_register = ( 1, 1, state)
    @property
    def power3(self):
        return self._get_bit(self.bit_register[1], 2)
    @power3.setter
    def power3(self, state):
        self.bit_register = ( 1, 2, state)
    @property
    def power4(self):
        return self._get_bit(self.bit_register[1], 3)
    @power4.setter
    def power4(self, state):
        self.bit_register = ( 1, 3, state)
    @property
    def power5(self):
        return self._get_bit(self.bit_register[1], 4)
    @power5.setter
    def power5(self, state):
        self.bit_register = ( 1, 4, state)
        
        
    @property
    def CELLS(self):
        return self._get_bit(self.bit_register[0], 0)
    @CELLS.setter
    def CELLS(self, state):
        self.bit_register = (0, 0, state)
    @property
    def CHEM(self):
        return self._get_bit(self.bit_register[0], 1)
    @CHEM.setter
    def CHEM(self, state):
        self.bit_register = (0, 1, state)
    @property
    def LOBAT(self):
        return self._get_bit(self.bit_register[0], 2)
    @property
    def ICL(self):
        return self._get_bit(self.bit_register[0], 3)
    @property
    def ACP(self):
        return self._get_bit(self.bit_register[0], 4)
    @property
    def SHDN(self):
        return self._get_bit(self.bit_register[0], 5)
    @SHDN.setter
    def SHDN(self, state):
        self.bit_register = (0, 5, state)
    @property
    def FAULT(self):
        return self._get_bit(self.bit_register[0], 6)
    @property
    def CHG(self):
        return self._get_bit(self.bit_register[0], 7)
        
    @property
    def bit_register(self):
        return self.__bit_register
    @bit_register.setter
    def bit_register(self, port, bit, state):
        if state is 1:
            # Set bit high
            self.__bit_register[port] = self.__bit_register[port] | (1 << bit)
        elif state is 0:
            if bool( (self.__bit_register[port] >> bit) & 0b00000001) is True:
                # Set bit low
                self.__bit_register = self.__bit_register[port] ^ (1 << bit)
            else:
                # Bit already set
                return
        else:
            # State must be 1 or 0
            print("Error in bit register setter")
        self.change_output()

class Adc:
    def __init__(self, res=12):
        self.__adc1 = MCP3424(0xD0, res)
        self.__adc2 = MCP3424(0xD8, res)
        
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
        self.__t1              = self.__adc1.get(3)
        self.__t2              = self.__adc2.get(3)
        self.__fc_voltage      = self.__adc2.get(2)
        self.__battery_voltage = self.__adc2.get(0)
        self.__output_voltage  = self.__adc2.get(1)
        self.__fc_current      = self.__adc1.get(2)
        self.__charge_current  = self.__adc1.get(0)
        self.__output_current  = self.__adc1.get(1)
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
        self.__io  = HybridIo()
        self.__adc = Adc()
        
    def update(self):
        # Input/Outputs
        self.__io.update()
        # ADCs
        self.__adc.update()
        
    @property
    def charger_info(self):
        return [self.__io.LOBAT,
                self.__io.ICL,
                self.__io.ACP,
                self.__io.FAULT,
                self.__io.CHG]
        
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
        return self.__adc.fc_current + self.__adc.charge_current
    @property
    def battery_current(self):
        return self.__adc.output_current - self.fc_current_total
    @property
    def charge_current(self):
        return self.__adc.charge_current
    @property
    def output_current(self):
        return self.__adc.output_current
    
    @property
    def cells(self):
        if self.__io.CELLS is False:
            return 3
        else:
            return 4
    @cells.setter
    def cells(self, cells):
        if cells is 3:
            self.__io.CELLS = False
        elif cells is 4:
            self.__io.CELLS = True
        else:
            print("Wrong cell count selected")
    
    @property
    def charged_voltage(self):
        if self.__io.CHEM is False:
            return 4.1
        else:
            return 4.2
    @charged.voltage.setter
    def charged_voltage(self, voltage):
        if cells is 4.1:
            self.__io.CHEM = False
        elif cells is 4.2:
            self.__io.CHEM = True
        else:
            print("Wrong cell chemistry selected")
    
    @property
    def shutdown(self):
        if self.__io.SHDN is False:
            return True
        else:
            return False
    @shutdown.setter
    def shutdown(self, state):
        if state is False:
            self.__io.SHDN = True
        elif state is True:
            self.__io.SHDN = False
    