from Temperature_controllers import TemperatureController

class Cryocon34(TemperatureController):
    
    def init(self):
        self.connect("GPIB0::7::INSTR")
    
    def read_temperature(self,channel):
        try:
            return float(self.query(f"INPUT? {channel}").strip())
        except Exception:
            print(f"Error reading channel {channel}")
            return None 
        
    def set_control_channel(self,channel):
        try:
            self.write(f"HEATER:SOURCE {channel}")
        except Exception:
            print("Error setting the control for the Heater")
            
    def read_control_channel(self):
        try: 
            return self.query(f"HEATER:SOURCE?").strip()
        except Exception:
            print("Error reading the control channel for the Heater")
            return None
            
    def set_heater_setpoint(self,temperature_setpoint):
        try:
            self.write(f"HEATER:SETPT {temperature_setpoint}")
        except Exception:
            print(f"Error setting temperature for Heater")   
            
    def read_heater_setpoint(self):
        try:
            return float(self.query(f"HEATER:SETPT?").strip())
        except Exception:
            print(f"Error reading temperature setpoint for Heater")
            return None
        
    def write_heater_status(self,status):
        try:
            self.write(f"HEATER:TYPE {status}")
        except Exception:
            print(f"Error writing Heater status")   
            
    def read_heater_status(self):
        try:
            return self.query("HEATER:TYPE?").strip()
        except Exception:
            print("Error reading the heater status")
            return None
        
    def write_heater_range(self,range):
        try:
            self.write(f"HEATER:RANGE {range}")
        except Exception:
            print("Error setting heater range")
    
    def read_heater_range(self):
        try:
            return self.query("HEATER:RANGE?").strip()
        except Exception:
            print("Error reading heater_range")
            return None
            