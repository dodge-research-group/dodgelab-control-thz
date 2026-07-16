import numpy as np

class temperature_stability():
    def __init__(self, minimum_sample_time,sampling_frequency,maximum_offset,maximum_std,):
        
        self.minimum_sample_time = minimum_sample_time
        self.sampling_frequency = sampling_frequency
        self.maximum_offset = maximum_offset
        self.maximum_std = maximum_std
        self.temperature_history = []
        self.offset_ok = False
        self.std_ok = False
        self.stable = False
        self.average_temperature = np.nan
        self.std = np.nan
        
    def reset(self):

        self.temperature_history = []
        self.offset_ok = False
        self.std_ok = False
        self.stable = False
        self.average_temperature = np.nan
        self.std = np.nan
    
    def update (self,temperature,temperature_setpoint):
        """
        updates the temperature array and calls checks_for_stable_temperature.
        """
        self.temperature_history.append(temperature)
        elapsed_time = len(self.temperature_history)/self.sampling_frequency
        if elapsed_time < self.minimum_sample_time:
            return
        self.Check_for_stable_temperature(temperature_setpoint)

    
    def Check_for_stable_temperature(self,Temperature_setpoint):
        """
        Changed with respect to the original version. Now it uses a weighted average and weighted std to check for stability. 
        The weights are exponential, with a decay factor that depends on the sampling time and frequency. 
        This way, more recent measurements have more weight in the calculation of the average and std.
        Outputs are also changed,it returns two boolean values, one for the average offset and one for the std,
        as well as the average temperature and std found.
        """
        Temperature_array = np.array(self.temperature_history)
        T_difference = Temperature_array-Temperature_setpoint
        weight_parameter = 1/(self.sampling_frequency*self.minimum_sample_time)
        w = np.exp(-weight_parameter*(len(Temperature_array)-np.arange(len(Temperature_array))))
        w = w/np.sum(w)
        average_offset = np.sum(w*T_difference)
        std = np.sqrt(np.sum(w*(T_difference-average_offset)**2))
        self.offset_ok = (abs(average_offset) < self.maximum_offset)
        self.std_ok = (std < self.maximum_std)
        self.average_temperature = average_offset+Temperature_setpoint
        self.std = std
        if self.offset_ok == True and self.std_ok == True:
            self.stable = True
    
        
