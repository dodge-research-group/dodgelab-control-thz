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
            
    def set_heater_setpoint(self,Temperature_setpoint):
        try:
            self.write(f"HEATER:SETPT {Temperature_setpoint}")
        except Exception:
            print(f"Error setting temperature for Heater")   
            
    def read_heater_setpoint(self):
        try:
            return float(self.query(f"HEATER:SETPT?").strip())
        except Exception:
            print(f"Error reading temperature setpoint for Heater")
            return None
        
    def start_control(self):
        try: 
            self.write("CONTROL")
        except Exception:
            print("Error activating the control loop")
            
    def stop_control(self):
        try:
            self.write("STOP")
        except Exception:
            print("Error stopping the control loop")
    def read_control(self):
        try:
            return self.query("CONTROL?").strip()
        except Exception:
            print("Error reading the control loop")
            return None
            