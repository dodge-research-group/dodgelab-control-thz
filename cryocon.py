import time
import csv
from datetime import datetime
import pyvisa
import threading
import random
import numpy as np

def connect_cryocon(resource):
    rm = pyvisa.ResourceManager()
    inst = rm.open_resource(resource)
    inst.timeout = 5000 # Communication timeout in milliseconds
    inst.read_termination = '\n' #Defines how to end a lecture from the instrument. It will read until it finds a newline character.
    inst.write_termination = '\n'#Defines how to end a write command to the instrument. It will write until it finds a newline character.
    print(inst.query("*IDN?")) # Asks for the instrument identification (Just to check if the connection is working)
    return inst

def read_temp(inst, channel):
    try:
        return float(inst.query(f"INPUT? {channel}").strip())
    except Exception:
        print(f"Error reading channel {channel}")
        return None
    
def set_heater_setpoint(inst,Temperature_setpoint):
    try:
        inst.write(f"HEATER:SETPT {Temperature_setpoint}")
    except Exception:
        print(f"Error setting temperature for Heater")

def read_heater_setpoint(inst):
    try:
        return float(inst.query(f"HEATER:SETPT?").strip())
    except Exception:
        print(f"Error reading temperature setpoint for Heater")
        return None

def Check_for_stable_temperature(Maximum_offset,Maximum_std,Temperature_setpoint,Temperature_array,sampling_time,sampling_frequency):
    T_difference = Temperature_array-Temperature_setpoint
    weight_parameter = sampling_frequency/sampling_time
    w = np.exp(-weight_parameter*(len(Temperature_array)-np.arange(len(Temperature_array))))
    w = w/np.sum(w)
    average_offset = np.sum(w*T_difference)
    std = np.sqrt(np.sum(w*(T_difference-average_offset)**2))
    Centinel_1 = (abs(average_offset) < Maximum_offset)
    Centinel_2 = (std < Maximum_std)
    return (Centinel_1,Centinel_2,average_offset+Temperature_setpoint,std)

    


class CryoconLogger:
    def __init__(self, inst, channels=("A","B","C", "D"), filename="cryocon_log.csv", interval=10):
        self.inst = inst
        self.channels = list(channels)
        self.filename = filename
        self.interval = interval #in seconds
        self.running = False
        self.pending_comment = ""
        with open(self.filename, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", *[f"T_{ch}" for ch in self.channels], "comments"])

    def add_comment(self, text):
        self.pending_comment = str(text).strip()

    def stop(self):
        self.running = False
        if hasattr(self, "thread"):
            self.thread.join()
        print("Logging stopped.")

    def start(self):
        self.thread = threading.Thread(target=self._run)
        self.running = True
        self.thread.start()

    def _run(self):
        while self.running:
            timestamp = datetime.now().isoformat()
            temps = [read_temp(self.inst, channel) for channel in self.channels]
            comments = self.pending_comment
            self.pending_comment = ""

            #print(timestamp, temps, comments)

            with open(self.filename, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, *temps, comments])
                if comments != "":
                    print(f"Logged at {timestamp}:, Comment='{comments}'")

            time.sleep(self.interval)

#class that pretends to be the connected crycon so i can open the pyside window from home. Generates random temperatures

class FakeCryocon:

    def query(self, command):

        if command == "*IDN?":
            return "Fake Cryocon"

        if command.startswith("INPUT?"):
            return str(20 + random.uniform(-0.05, 0.05))