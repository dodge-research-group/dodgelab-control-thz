import numpy as np


class Fakecryocon34:
    def init(self):
        self.temperature = {
        "A": 0.0,
        "B": 0.0,
        "C": 0.0,
        "D": 0.0 }
        self.control_channel = "A"
        self.setpoint = 5.0
        self.heater_range = 0
        self.heater_status = "OFF"

    def read_temperature(self,channel):
        return float(self.temperature[channel])  
    
    def set_control_channel(self,control_channel):
        self.control_channel = control_channel
        
    def read_control_channel(self):
        return self.control_channel 
        
    def set_heater_setpoint(self, temperature_setpoint):
        self.setpoint = temperature_setpoint
        
    def read_heater_setpoint(self):
        return self.setpoint
     
    def write_heater_status(self,status):
        self.heater_status = status
               
    def read_heater_status(self):
        return self.heater_status
    
    def write_heater_range(self,range):
        self.heater_range = range
    
    def read_heater_range(self):
        return self.heater_range
        
        