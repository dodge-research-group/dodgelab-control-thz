from Instruments.Temperature_controllers import TemperatureController
import numpy as np


class FakeCryocon34(TemperatureController):
    """
    Restructured to take queries in the same structure as Cryocon, through TemperatureController
    """

    def __init__(self):
        self.temperature = {
            "A": 0.0,
            "B": 0.0,
            "C": 0.0,
            "D": 0.0
        }

        self.control_channel = "A"
        self.setpoint = 5.0
        self.heater_range = 0
        self.heater_status = "OFF"


    def query(self, command):

        if command.startswith("INPUT?"):
            channel = command.split()[1]
            return str(self.read_temperature(channel, self.setpoint))

        elif command == "HEATER:SETPT?":
            return str(self.read_heater_setpoint())

        elif command == "HEATER:SOURCE?":
            return self.read_control_channel()

        elif command == "HEATER:TYPE?":
            return self.read_heater_status()

        elif command == "HEATER:RANGE?":
            return str(self.read_heater_range())


    def write(self, command):

        if command.startswith("HEATER:SETPT"):
            value = float(command.split()[1])
            self.set_heater_setpoint(value)

        elif command.startswith("HEATER:SOURCE"):
            channel = command.split()[1]
            self.set_control_channel(channel)

        elif command.startswith("HEATER:TYPE"):
            status = command.split()[1]
            self.write_heater_status(status)

        elif command.startswith("HEATER:RANGE"):
            value = int(command.split()[1])
            self.write_heater_range(value)


    def read_temperature(self, channel, setpoint, noise=0.01):
        self.temperature[channel] += (
            (setpoint - self.temperature[channel])*0.05
            + np.random.normal(0, noise)
        )

        return float(self.temperature[channel])


    def set_control_channel(self, channel):
        self.control_channel = channel


    def read_control_channel(self):
        return self.control_channel


    def set_heater_setpoint(self, value):
        self.setpoint = value


    def read_heater_setpoint(self):
        return self.setpoint


    def write_heater_status(self, status):
        self.heater_status = status


    def read_heater_status(self):
        return self.heater_status


    def write_heater_range(self, value):
        self.heater_range = value


    def read_heater_range(self):
        return self.heater_range