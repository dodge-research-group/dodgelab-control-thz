import threading
from collections import deque
from pathlib import Path
import time

class TemperatureLoop:

    def __init__(
        self,
        controller,
        channels=("A", "B", "C", "D"),
        control_channel="A",
        sample_time=60,
        sampling_frequency=1,
        maximum_offset=0.1,
        maximum_std=0.05,
        timeout=600,
        ):
        self.controller = controller
        self.channels = list(channels)
        self.control_channel = control_channel

        self.sample_time = sample_time
        self.sampling_frequency = sampling_frequency
        self.maximum_offset = maximum_offset
        self.maximum_std = maximum_std
        self.timeout = timeout
   
