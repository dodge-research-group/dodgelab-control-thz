import numpy as np
import random
import time

class temperature_stability():
    def _init_(self,controller,
                channel,
                sample_time,
                sampling_frequency,
                maximum_offset,
                maximum_std,
                timeout):
        self.controller = controller
        self.channels = channel
        self.sample_time = sample_time
        self.sampling_frequency = sampling_frequency
        self.maximum_offset = maximum_offset
        self.maximum_std = maximum_std
        self.timeout = timeout
        self.offset_centinel = False
        self.std_centinel = False
        
    def Check_for_stable_temperature(self,Temperature_setpoint,Temperature_array):
        """
        Changed with respect to the original version. Now it uses a weighted average and weighted std to check for stability. 
        The weights are exponential, with a decay factor that depends on the sampling time and frequency. 
        This way, more recent measurements have more weight in the calculation of the average and std.
        Outputs are also changed,it returns two boolean values, one for the average offset and one for the std,
        as well as the average temperature and std found.
        """
        T_difference = Temperature_array-Temperature_setpoint
        weight_parameter = 1/self.sample_time
        w = np.exp(-weight_parameter*(len(Temperature_array)-np.arange(len(Temperature_array))))
        w = w/np.sum(w)
        average_offset = np.sum(w*T_difference)
        std = np.sqrt(np.sum(w*(T_difference-average_offset)**2))
        self.offset_centinel = (abs(average_offset) < self.maximum_offset)
        self.std_centinel = (std < self.maximum_std)
        self.average_temperature = average_offset+Temperature_setpoint
        self.std = std
        return self.offset_centinel,self.std_centinel,self.average_temperature,self.std

        
