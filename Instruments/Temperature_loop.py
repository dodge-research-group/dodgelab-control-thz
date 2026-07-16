import threading
from pathlib import Path
import time
import numpy as np
from temperature_stability import temperature_stability
class TemperatureLoop:

    def __init__(
        self,
        controller,
        temperature_arange,
        channels=("A", "B", "C", "D"),
        control_channel="A",
        sample_time=60,
        sampling_frequency=1,
        minimum_offset = 1,
        maximum_offset=0.1,
        maximum_std=0.05,
        timeout=600,
        logger=None):
        
        self.controller = controller
        self.channels = list(channels)
        self.temperature_arange = list(temperature_arange)
        self.control_channel = control_channel
        self.sample_time = sample_time
        self.sampling_frequency = sampling_frequency
        self.maximum_offset = maximum_offset
        self.maximum_std = maximum_std
        self.timeout = timeout
        self.minimum_offset = minimum_offset
        self.logger = logger
        self.stabilities = {
            channel: temperature_stability(
                minimum_sample_time=sample_time,
                sampling_frequency=sampling_frequency,
                maximum_offset=maximum_offset,
                maximum_std=maximum_std)
            for channel in self.channels}
        self.centinels = {
            channel:False
            for channel in self.channels}
        self.temperatures = {
            channel: np.nan
            for channel in self.channels}
        self._stop_event = threading.Event()
        self._next_temperature_event = threading.Event()
        self.thread = None
        self.current_temperature_index = 0
        self.current_setpoint = np.nan
        self.temperature_started = False
        self.experiment_finished = False
        
    def start(self):
        
        if self.thread is not None:
            if self.thread.is_alive():
                return
        self._stop_event.clear()
        self.thread = threading.Thread(target=self._run,daemon=True)
        self.thread.start()
        
    def stop(self):
        
        self._stop_event.set()
        if self.thread is not None:
            self.thread.join()
            
    def _run(self):
        
        self._start_temperature(self.temperature_arange[self.current_temperature_index])
        while not self._stop_event.is_set():
            self._run_temperature_point()
            if self.experiment_finished:
                break
            self._next_temperature_event.wait()
            self._next_temperature_event.clear()
            if self._stop_event.is_set():
                break
            self._advance_temperature()
            
    def _start_temperature(self, setpoint):

        self.current_setpoint = setpoint
        self.controller.set_heater_setpoint(setpoint)
        for stability in self.stabilities.values():
            stability.reset()
        for channel in self.centinels:
            self.centinels[channel] = False
        self.temperature_started = True
        if self.logger is not None:
            self.logger.log_event(event="Temperature Started",source="TemperatureLoop",message=(f"Setpoint changed to "f"{setpoint}"),)
            
    def _run_temperature_point(self):

        start_time = time.monotonic()
        while not self._stop_event.is_set():
            temperatures = {channel: self.controller.read_temperature(channel,self.temperature_arange[self.current_temperature_index]) for channel in self.channels}
            self.temperatures = temperatures
            self._update_stabilities(temperatures)
            if self.logger is not None:
                self.logger.log_data(temperatures=self.temperatures,stabilities=self.stabilities)
            if self._all_channels_stable():
                self._log_stability()
                return
            if (time.monotonic()-start_time>=self.timeout):
                self._log_timeout()
                return
            self._stop_event.wait(1 / self.sampling_frequency)
            
    def _update_stabilities(self,temperatures):
        
        for channel in self.channels:
            temperature = temperatures[channel]
            if np.isnan(temperature):
                continue
            temperature_difference = abs(temperature-self.current_setpoint)
            if (temperature_difference<=self.minimum_offset) or (self.centinels[channel]):
                self.centinels[channel] = True
                self.stabilities[channel].update( temperature=temperature,temperature_setpoint=(self.current_setpoint))
                
    def _all_channels_stable(self):

        return all(self.stabilities[channel].stable
                   for channel in self.channels)
        
    def _log_timeout(self):

        unstable_channels = [channel
            for channel in self.channels
            if not self.stabilities[channel].stable]
        if self.logger is not None:
            self.logger.log_event(event="Temperature Stability Timeout",source="TemperatureLoop",
                    message=(
                    f"Setpoint: "
                    f"{self.current_setpoint}; "
                    f"Unstable channels: "
                    f"{unstable_channels}"))
            
    def _log_stability(self):
        
        if self.logger is not None:
            self.logger.log_event(event="All Channels Stable",source="TemperatureLoop",
                message=(
                    f"Setpoint: "
                    f"{self.current_setpoint}"))
            
    def next_temperature(self):
        
        if self.experiment_finished:
            return False
        self._next_temperature_event.set()  
        return True
    
    def set_heater_range(self, heater_range):
        
        self.controller.write_heater_range(heater_range)
        if self.logger is not None:
            self.logger.log_event(event="Heater Range Changed",source="User",message=f"New range: {heater_range}")
        
    def set_heater_setpoint(self, setpoint):
        
        old_setpoint = self.current_setpoint
        self.controller.set_heater_setpoint(setpoint)
        self.current_setpoint = setpoint
        for stability in self.stabilities.values():
            stability.reset()
        for channel in self.centinels:
            self.centinels[channel] = False
        if self.logger is not None:
            self.logger.log_event(event="Heater Setpoint Changed",source="User",message=f"{old_setpoint} -> {setpoint}")
        
    def _advance_temperature(self):
        
        if (self.current_temperature_index>=len(self.temperature_arange) - 1):
            self.experiment_finished = True
            if self.logger is not None:
                self.logger.log_event(event="Experiment Finished",source="TemperatureLoop",message="Temperature range completed")
            return
        self.current_temperature_index += 1
        new_setpoint = (self.temperature_arange[self.current_temperature_index])
        self._start_temperature(new_setpoint)
        
    def comment(self, message):
        
        if self.logger is not None:
            self.logger.comment(message)
            
    def set_heater_mode(self, mode):
        
        self.controller.write_heater_status(mode)
        if self.logger is not None:
            self.logger.log_event(event="Heater Mode Changed",source="User",message=f"New mode: {mode}")