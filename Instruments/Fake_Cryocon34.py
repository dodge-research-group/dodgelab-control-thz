import numpy as np


class Fakecryocon34:
    def init(self):
        self.temperature = {
        "A": 300.0,
        "B": 300.0,
        "C": 300.0,
        "D": 300.0 }
        self.control_channel = "A"
        self.setpoint = 300.0
        self.heater_power = 0
        self.control = False
        
    def set_heater_setpoint(self, temperature):
        self.setpoint = temperature
        
    def read_heater_setpoint(self):
        return self.setpoint
    
    def read_temperature(self,channel):
        return float(self.temperature[channel])
    
    def set_control_channel(self,control_channel):
        self.control_channel = control_channel
    
    def read_control_channel(self):
        return self.control_channel 
    
    def start_control(self):
        self.control = True
        
    def stop_control(self):
        self.control = False
        
    def read_control(self):
        return self.control
        
        