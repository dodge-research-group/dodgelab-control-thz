import csv
import time
from datetime import datetime
class temperature_logger():
    def __init__(
        self,
        filename,
        channels):

        self.filename = filename
        self.channels = channels
        self.data_file = open(filename,"w",newline="")
        self.event_file = open(filename.replace(".csv","_events.csv"),"w",newline="")
        self.writer = csv.writer(self.data_file)
        self.event_writer = csv.writer(self.event_file)
        self.write_headers()
        
    def write_headers(self):
        header = ["time"]
        for ch in self.channels:
            header.append(f"T_{ch}")
        for ch in self.channels:
            header.append(f"std_{ch}")
        for ch in self.channels:
            header.append(f"average_temperature_{ch}")
        for ch in self.channels:
            header.append(f"std_stable_{ch}")
        for ch in self.channels:
            header.append(f"offset_stable_{ch}")
        for ch in self.channels:
            header.append(f"stable_{ch}")
        self.writer.writerow(header)
        
    def log_data(self,temperatures,stabilities):
        row = [time.time() ]
        for ch in self.channels:
            row.append(temperatures[ch])
        for ch in self.channels:
            row.append(stabilities[ch].std)
        for ch in self.channels:
            row.append(stabilities[ch].average_temperature)
        for ch in self.channels:
            row.append(stabilities[ch].std_stable)
        for ch in self.channels:
            row.append(stabilities[ch].offset_stable)
        for ch in self.channels:
            row.append(stabilities[ch].stable)
        self.writer.writerow(row)
  

    def log_event(self,event,source="System",message=""
    ):

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.event_writer.writerow(
            [
                timestamp,
                event,
                source,
                message
            ]
        )

        self.event_file.flush()