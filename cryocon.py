import time
import csv
from datetime import datetime
import pyvisa
import threading
import random

def connect_cryocon(resource):
    rm = pyvisa.ResourceManager()
    inst = rm.open_resource(resource)
    inst.timeout = 5000
    inst.read_termination = '\n'
    inst.write_termination = '\n'

    print(inst.query("*IDN?"))
    return inst

def read_temp(inst, channel):
    try:
        return float(inst.query(f"INPUT? {channel}").strip())
    except Exception as e:
        print(f"Error reading channel {channel}: {e}")
        return None


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