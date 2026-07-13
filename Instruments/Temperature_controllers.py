import pyvisa
class TemperatureController():
    
    def connect(self,resource):
        self.rm = pyvisa.ResourceManager()
        self.inst = self.rm.open_resource(resource)
        self.inst.timeout = 5000 # Communication timeout in milliseconds
        self.inst.read_termination = '\n' #Defines how to end a lecture from the instrument. It will read until it finds a newline character.
        self.inst.write_termination = '\n'#Defines how to end a write command to the instrument. It will write until it finds a newline character.
        print(self.inst.query("*IDN?")) # Asks for the instrument identification (Just to check if the connection is working)
    
    def query(self, command):
        return self.inst.query(command)

    def write(self, command):
        self.inst.write(command)

    def close(self):
        self.inst.close()
