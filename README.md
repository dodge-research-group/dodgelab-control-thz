# General overview of the temperature control software as of 07/08/2026
## Idea
The purpose of this repository is to eventually replace the current temperature control software for THZ spectroscopy measurements. 
The software should be able to communicate with all temperature controllers and get all revelant information out of it as well be able to change the settings in the controller.
# Structure
In order to accomplish this it was decided that software would be divided in the following way:
## Temperature_controllers.py
This file is responsible for connecting to the instrument using PYVISA.
Should be careful with the connect function as the read and write termination could be not universal for all controllers.
This file will be called every time a query, a read or a write command is called somewhere else.
## Cryocon34.py
This file contains the cryocon34 class.
The class will initialize automatically with __init__ and temperature_controllers.py
It can read and set temperatures, read and set the control channels,read and write heater status, range and setpoint.
## Missing
Pending testing with the cryocon
Stronger error handling. Currently it justs raises and exception and print some message.
read_temperature takes temperature although it does not use it, it is done that way so the fake cryocon can work with exactly the same parameters.
We should think of a way of fixing that.
## Fake_cryocon34
This file contains the Fakecryocon34 class.
The class will initalize automatically with __init__ and will create a dictionary with all relevant variables that will update.
It can do everything the Cryocon34 class can without changing the temperature loop code. It uses setpoint in the read temperature in order to simulate a somewhat realistic version of
a temperature evolution during a measurement.
## Missing
You should be able to change the parameters of noise and the convergence for testing purposes.
## Temperature_stability.py
This file contains the temperature_stability class.
Auxilary class that helps to keep track of temperature stability for each channel, an object of this class is created for every temperature channel.
It will calculate the standard deviation and offset with respect to the temperature setpoint and decide whether it is stable or not based on the maximum allowed values for those quantities.
It will start calculating those values once it is close enough to temperature setpoint.
It has an exponential weight for taking the average and standard deviation.
## Missing
Set an appropiate weight.
## Temperature_logger.py
This file contains the temperature_logger class
This class will create 2 csv files for keeping track of everything that happens during a measurement.
One file will just keep everys ingle temperature of every single channel along with all stability variables.
The other file will keep every important event that happens during a measurement such as temperature stabilty reached or a timeout.
It allows the user to put comments if anything extra is needed
## Missing
Measurements experience is probably needed to know which events we should keep track of.
## Temperature_loop.py
Main file that will actually communicate with all other files.
Allows for changing parameters for the temperature control, will execute the temperature loop and retrieve its stabilities for each channel and 
will advance temperatures in the temperature arange.
Uses threading in order for the user to other things while the temperature loop runs.
## Missing
More extensive testing is needed to see that everything is actually working.



