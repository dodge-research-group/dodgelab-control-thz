import threading
from pathlib import Path
import time
import numpy as np
from Instruments.temperature_stability import temperature_stability
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
        # threading.Event() is a synchronization object that stores a boolean state: set or unset.
        # When the event is set, wait() returns immediately.
        # When the event is unset, wait() blocks until another part of the program sets the event.
        # This event is used to request that the temperature loop stops.
        self._stop_event = threading.Event()
        # This event is used to notify the temperature-loop thread that it may advance to the next temperature setpoint.
        # The event is initially unset. Therefore, when the temperature loop reaches _next_temperature_event.wait(), 
        # the thread pauses there until next_temperature() calls .set().
        self._next_temperature_event = threading.Event()
        # This variable will contain the Thread object responsible for running the temperature loop
        self.thread = None
        self.current_temperature_index = 0
        self.current_setpoint = np.nan
        self.temperature_started = False
        self.experiment_finished = False
        
    def start(self):
        """
        Starts the temperature-control loop in a separate thread.
        The main Python thread does not execute _run() directly. Instead, a
        new Thread object is created and instructed to execute _run().
        This allows the temperature loop to run in the background while the
        main program remains available for other actions,such as changing the 
        heater range or adding a comment to the logger.
        If a temperature-loop thread already exists and is still running,
        start() returns without creating a second thread.
        """
        
        if self.thread is not None:
            if self.thread.is_alive(): #Checks if the thread is still working.
                return
        self._stop_event.clear() # Clear the stop event before starting the experiment, allowing a new thread to run.
        # Creates a new thread
        # target tells you that the thread is going to run the function self._run()
        # daemon= True allows for the thread to close when the main program finishes running, even if the thread has not finished.
        self.thread = threading.Thread(target=self._run,daemon=True)
        self.thread.start()
        
    def stop(self):
        """
        Requests the temperature-loop thread to stop and waits for it to
        finish. stop() does not forcibly kill the thread. Instead, it sets
        _stop_event.
        """
        
        self._stop_event.set()
        if self.thread is not None:
            # join() blocks the thread that called stop() until the background temperature-loop thread has finished.
            self.thread.join()
            
    def _run(self):
        """
        This function is executed by the Thread created in start().
        The thread first starts the initial temperature point. It then
        runs the current temperature point until stability or timeout,
        waits until the user requests the next temperature,
        advances to the next temperature. Repeats for all temperatures.
        The loop can be interrupted at any point self_stop_event.set().
        """
        
        self._start_temperature(self.temperature_arange[self.current_temperature_index])
        while not self._stop_event.is_set():
            self._run_temperature_point() # gets the temperature and checks stability
            if self.experiment_finished:
                break
            if self._stop_event.is_set():
                break
            self._advance_temperature() # Advances to the next temperature
            
    def _start_temperature(self, setpoint):
        """
        This function sets the heater setpoint and documents it in the logger.
        It also resets the stability values for all channels that evaluate the 
        stability of all channels.It also resets the centinels that determine 
        when is the program actually using the temperature data to check for 
        stability.
        """
       
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
        """
        Acquires temperature data repeatedly for the current temperature
        setpoint.This function is executed inside the background 
        temperature thread.The loop continues until  
        conditions is met: The stop event is set.
        """
        centinel_1 = False
        centinel_2 = False
        start_time = time.monotonic()
        while not self._stop_event.is_set():
            temperatures = {channel: self.controller.read_temperature(channel,self.temperature_arange[self.current_temperature_index]) for channel in self.channels}
            self.temperatures = temperatures
            self._update_stabilities(temperatures)
            if self.logger is not None:
                self.logger.log_data(temperatures=self.temperatures,stabilities=self.stabilities)
            if self._all_channels_stable() and centinel_1== False:
                self._log_stability()
                centinel_1 = True
            if (time.monotonic()-start_time>=self.timeout)and centinel_2 == False:
                self._log_timeout()
                centinel_2 = True
            if self._next_temperature_event.is_set():
                self._next_temperature_event.clear()
                return
            self._stop_event.wait(1 / self.sampling_frequency) #Stops the thread for a time duration
            
    def _update_stabilities(self,temperatures):
        """
        Checks if for each channel the temperature is close enough (< self.minimum_offset) 
        to the set point to start checking for temperature stability.
        """
        for channel in self.channels:
            temperature = temperatures[channel]
            if np.isnan(temperature):
                continue
            temperature_difference = abs(temperature-self.current_setpoint)
            if (temperature_difference<=self.minimum_offset) or (self.centinels[channel]):
                self.centinels[channel] = True
                self.stabilities[channel].update( temperature=temperature,temperature_setpoint=(self.current_setpoint))
                
    def _all_channels_stable(self):
        """
        Checks if all channels are stable.
        """

        return all(self.stabilities[channel].stable
                   for channel in self.channels)
        
    def _log_timeout(self):
        """
        Generates a log that tells the user that a timeout has ocurred and which channels are causing issues.
        """

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
        """
        Generates a log that tells the user that all channels are stable. 
        """
        if self.logger is not None:
            self.logger.log_event(event="All Channels Stable",source="TemperatureLoop",
                message=(
                    f"Setpoint: "
                    f"{self.current_setpoint}"))
            
    def next_temperature(self):
        """
        Signals the background temperature-loop thread that it may advance
        to the next temperature setpoint.This function can be called from 
        another thread. It ideally would be called by a button in the GUI.

        The function does not directly change the temperature. Instead, it
        sets _next_temperature_event.The background thread is responsible 
        for detecting this event and calling _advance_temperature().
        """
        if self.experiment_finished:
            return False
        # Change the state of the event from unset to set.
        # If the background thread is currently blocked at:_next_temperature_event.wait()
        # it is released and continues execution.
        self._next_temperature_event.set()  
        return True
    
    def set_heater_range(self, heater_range):
        """
        Changes the heater_range can be called from another thread.
        It ideally could be called by a button in the GUI that shows
        all possible range values.
        """
        self.controller.write_heater_range(heater_range)
        if self.logger is not None:
            self.logger.log_event(event="Heater Range Changed",source="User",message=f"New range: {heater_range}")
        
    def set_heater_setpoint(self, setpoint):
        """
        Allows to change the heater setpoint without killing the program,
        it allow to run that setpoints and then it will return to the 
        next temperature arange.
        """
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
        """
        Updates the temperature index, creates a log if the experiment is finished,
        and will call start_temperature to update the set_point.
        """
        
        if (self.current_temperature_index>=len(self.temperature_arange) - 1):
            self.experiment_finished = True
            if self.logger is not None:
                self.logger.log_event(event="Experiment Finished",source="TemperatureLoop",message="Temperature range completed")
            return
        self.current_temperature_index += 1
        new_setpoint = (self.temperature_arange[self.current_temperature_index])
        self._start_temperature(new_setpoint)
        
    def comment(self, message):
        """
        Logs a comment from the user
        """
        
        if self.logger is not None:
            self.logger.comment(message)
            
    def set_heater_mode(self, mode):
        """
        Allows the user to change the heater_mode during the experiment. 
        Ideally it could be called through the GUI.
        """
        self.controller.write_heater_status(mode)
        if self.logger is not None:
            self.logger.log_event(event="Heater Mode Changed",source="User",message=f"New mode: {mode}")