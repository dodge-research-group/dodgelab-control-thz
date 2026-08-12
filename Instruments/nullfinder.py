import csv
import threading
import pyvisa
import time
from datetime import datetime
import numpy as np

def agilent(x): 
    r"""
    Simulated voltage for testing. The function contains a root at 
    :math:`x \approx 554859 = 1.084 \text{ in}`.

    Parameters
    ----------
    x : int
        Microsteps from internal zero reference.

    Returns
    -------
    dv : np.float64
        Simulated voltage value.
    """
    
    dv = -np.exp((x / 512_000) - 2) + 0.4 
    return dv

class NullFinder:
    r"""
    Class for finding the null position of the sample positioner.

    Parameters
    ----------
    _min : float, optional
        Minimum motor position with respect to the zero of the motor 
        division, in inches. The default is 0.500".
     _max : float, optional
        Maximum motor position with respect to the zero of the motor 
        division, in inches. The default is 4.000".
    _home : float, optional
        Relative zero position for internal Zaber movement. The default is 0.500".
    filename : string or None, optional
        Filename for logging documentation. When None is given, the
        default name is  ``nullfinder_log.csv``.
    """
    
    def __init__(
        self,  
        *, 
        _min: float = 0.50, 
        _max: float = 4.00, 
        _home: float = 0.50,
        filename: str | None = "nullfinder_log.csv",
    ):
        self.min = _min
        self.max = _max
        self.home = _home
        self.filename = filename
        self.null = None
        self.running = False
        self.pending_comment = ""

    def start(self):
        rm = pyvisa.ResourceManager()
        daq = rm.open_resource('USB0::0x3923::0x717B::00E15690::RAW')
        inst = rm.open_resource('ASRL5::INSTR')
        inst.read_termination = '\n'
        inst.write_termination = '\n'
        inst.baud_rate = 115200
        inst.timeout = 5000

        self.rm = rm
        self.inst = inst
        self.daq = daq

        with open(self.filename, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Motor Status", "Position (in)", "Voltage (V)", "Comments"])

    def stop(self):
        self.inst.close()
        self.daq.close()
        self.rm.close()
    
    def add_comment(self, text):
        self.pending_comment = str(text).strip()
   
    def set_home(self, val) -> np.float64 | None:
        try:
            self.home == val
            print(f"The home position has been reset to {val} in.")
            return self.home
        except Exception as e:
            print(f"Error setting home position as {val}: {e}")
            return None
    
    def get_home(self) -> np.float64:
        return self.home

    def get_pos(self) -> str | None:
        try:
            command = self.inst.query('/0 0 get pos\r')
            if "BUSY" not in command and '!' not in command:
                val = command
            else:
                
                while "BUSY" in command or '!' in command:
                    time.sleep(0.005)
                    command = self.inst.query('/0 0 get pos\r')
                    
                val = self.inst.read()
            return val
        except Exception as e:
            print(f"Error reading position: {e}")
            return None
    
    def pos_in_microsteps(self) -> int:
        return int(self.get_pos().split()[-1]) 
    
    def pos_in_inches(self) -> np.float64:
        return self.pos_in_microsteps() / 512_000
    
    def write_pos(self):
        timestamp = datetime.now().isoformat()

        comments = self.pending_comment
        self.pending_comment = ""

        with open(self.filename, "a", newline="") as f:
            writer = csv.writer(f)
            status = self.get_pos()
            position = self.pos_in_inches() + self.home
            voltage = agilent(position * 512_000)
            writer.writerow([timestamp, status, f"{position:.2f}", f"{voltage:.5f}", comments])
            if comments != "":
                print(f"Logged at {timestamp}:, Comment='{comments}'")
    
    def get_min(self) -> np.float64:
        return self.min
    
    def get_max(self) -> np.float64:
        return self.max

    def set_min(self, val) -> np.float64 | None:
        try:
            self.min == val
            print(f"The minimum position has been reset to {val} in.")
            return self.min
        except Exception as e:
            print(f"Error setting minimum position as {val} in: {e}")
            return None

    def set_max(self, val) -> np.float64 | None:
        try:
            self.max == val
            print(f"The maximum position has been reset to {val} in.")
            return self.max
        except Exception as e:
            print(f"Error setting maximum position as {val} in: {e}")
            return None
        
    def get_voltage(self) -> np.float64:
        position = self.pos_in_microsteps() + (self.home * 512_000)
        return agilent(position)

    def move_abs(self, pos) -> str | None:
        try:
            steps = int((pos - self.home) * 512_000)
            return self.inst.query(f'/0 0 move abs {steps}\r')
        except Exception as e:
            print(f"Error moving motor to {pos} in: {e}")
            return None
    
    def move_rel(self, pos) -> str | None:
        try:
            steps = int(pos * 512_000)
            return self.inst.query(f'/0 0 move rel {steps}\r')
        except Exception as e:
            print(f"Error moving motor to {pos} in: {e}")
            return None

    def set_null(self) -> np.float64:
        self.null = self.pos_in_inches() + self.home
        return self.null
    
    def get_null(self) -> np.float64:
        return self.null
    
    def find_null(
        self, 
        *,
        stepsize0: float = 0.200, 
        precision: float = 0.001,
    ) -> callable:
        r"""
        Automatic null position finder.

        Moves motor by ``stepsize0`` searching for a voltage range 
        comprising a change in sign. Null position is then found within
        this range to ``precision`` through an additional bisective search.

        Parameters
        ----------
        stepsize0: float, optional
            Step size for initial voltage search. The default is 0.200".

        precision: float, optional
            Precision for bisective search. The default is 0.001".

        Returns
        -------
        callable 
            Sets final found position as ``self.null`` 
            via :meth:`~Nullfinder.set_null`.

        """
        self.errorstatus = False

        self.write_pos()
        pos0 = self.pos_in_microsteps() + (self.home * 512_000)
        dv0 = agilent(pos0)
        dv = dv0

        while not self.errorstatus:
            pos = self.pos_in_microsteps() + ((self.home + stepsize0) * 512_000 )

            if pos > int(self.max * 512_000):
                self.errorstatus = True
                break
            else:
                self.move_rel(stepsize0)
                self.write_pos()
                dv = agilent(pos)

                if (dv * dv0) <= 0:
                    dv0 = dv
                    break

                dv0 = dv

        a = (pos / 512_000) - stepsize0 
        b = pos / 512_000 
        
        while ((b - a) >= precision) and self.errorstatus == False:
            self.move_abs(a)
            self.write_pos()

            dv_min = agilent(a * 512_000)

            c = (a + b)/2
            self.move_abs(c)
            self.write_pos()
            dv_max = agilent(c * 512_000)

            if np.isclose(dv_max, 0, atol=precision, rtol=0):
                break
            elif (dv_max * dv_min < 0):
                b = c
            else:
                a = c
        
        self.set_null()
