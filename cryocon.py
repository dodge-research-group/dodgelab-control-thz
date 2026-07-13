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
    """
    Changed with respect to the original version. Now it uses a weighted average and weighted std to check for stability. 
    The weights are exponential, with a decay factor that depends on the sampling time and frequency. 
    This way, more recent measurements have more weight in the calculation of the average and std.
    Outputs are also changed,it returns two boolean values, one for the average offset and one for the std,
    as well as the average temperature and std found.
    """
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
    def __init__(self, inst, channels=("A","B","C", "D"),temperature_control_settings={"Sample_Time":120,"Maximum_offset":0.1,"Maximum_std":0.05,"Timeout":600} ,filename="cryocon_log.csv", interval=0.001):
        self.inst = inst
        self.channels = list(channels)
        self.filename = filename
        self.interval = interval #in seconds
        self.running = False
        self.pending_comment = ""
        self.temperature_control_settings = temperature_control_settings
        self.minimum_data_points = 300
        #with open(self.filename, mode="w", newline="") as f:
            #writer = csv.writer(f)
            #writer.writerow(["timestamp", *[f"T_{ch}" for ch in self.channels], "comments"])

    def add_comment(self, text):
        self.pending_comment = str(text).strip()

    def stop(self):
        self.running = False
        if hasattr(self, "thread"):
            self.thread.join()
        print("Logging stopped.")

    def start(self):
        #self.thread = threading.Thread(target=self.Wait_for_stable_temperature, args=(self, 20))
        self.Wait_for_stable_temperature(20)
        #self.running = True
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
    def Wait_for_stable_temperature(self,setpoint):
        initial_time = time.perf_counter()
        current_time = time.perf_counter()
        centinel = False
        data = [[] for _ in range (len(self.channels))]
        counter = 0
        offset_centinel = [False for _ in range (len(self.channels))]
        std_centinel = [False for _ in range (len(self.channels))]
        counter_2 =0
        temp_array = np.zeros((len(self.channels),100000))
        for i in range (len(self.channels)):
            a = FakeCryocon.fake_temperature_data_set(10,setpoint,a=np.random.normal(0, 0.1),n=10000)
            temp_array[i, :] = a
        while (current_time - initial_time) < self.temperature_control_settings["Timeout"] or (current_time - initial_time)<1:
            #temps = [read_temp(self.inst, channel) for channel in self.channels]
            temps = temp_array[:,counter_2]
            counter_2 +=1
            if any(abs(temps-setpoint)<1) or centinel:
                centinel = True
                for i in range (len(self.channels)):
                    data[i].append(temps[i])
                counter +=1
                if counter >= self.minimum_data_points:
                    data_array = np.array(data)
                    for j in range (len(self.channels)):
                        Centinel_offset, Centinel_std, average_temperature, std = Check_for_stable_temperature(self.temperature_control_settings["Maximum_offset"], self.temperature_control_settings["Maximum_std"], setpoint, data_array[j], self.temperature_control_settings["Sample_Time"], 1/self.interval)
                        offset_centinel[j] = Centinel_offset
                        std_centinel[j] = Centinel_std
                if all(offset_centinel) and all(std_centinel):
                    print("Temperatures stabilized within the specified time.")
                    return (offset_centinel, std_centinel)
                #time.sleep(self.interval)
                current_time = time.perf_counter()
            else:
                #time.sleep(self.interval)
                current_time = time.perf_counter()
        print("Timeout reached. Temperatures did not stabilize within the specified time.")
        return (offset_centinel, std_centinel)
        

#class that pretends to be the connected crycon so i can open the pyside window from home. Generates random temperatures

class FakeCryocon:

    def query(self, command):

        if command == "*IDN?":
            return "Fake Cryocon"

        if command.startswith("INPUT?"):
            return str(20 + random.uniform(-0.05, 0.05))
    def fake_temperature_data_set(initial_temp,setpoint,a=0.05,n=1000,noise=0.1):
        """
        Generates a fake temperature data set that simulates a temperature stabilizing around a setpoint.
        The temperature will start at a random value and will converge to the setpoint over time.
        The parameter 'a' controls the rate of convergence, and 'n' is the number of data points.
        """
        temperature_array = np.zeros(n)

        temperature_array[0] = initial_temp          # Initial Temperature
        Temperature_setpoint = setpoint        # Setpoint Temperature
        alpha = a        # Response velocity

        for i in range(n-1):
            temperature_array[i+1] = temperature_array[i] + alpha * (Temperature_setpoint  - temperature_array[i])+ np.random.normal(0, noise) 
        return temperature_array