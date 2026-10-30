import numpy as np
import pyqtgraph as pg
import time
import json

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QHBoxLayout,
    QSpinBox,
    QCheckBox,
    QMessageBox,
    QGridLayout,
    QFrame,
    QDoubleSpinBox,
    QTabWidget,
    QGroupBox
)

from Instruments.nullfinder import (agilent,NullFinder)
from Instruments.Cryocon34 import Cryocon34
from Instruments.Fake_Cryocon34 import FakeCryocon34
from Instruments.Temperature_controllers import TemperatureController
from Instruments.temperature_logger import temperature_logger
from Instruments.Temperature_loop import TemperatureLoop
from Instruments.temperature_stability import temperature_stability
import json

from PySide6.QtCore import (QTimer, Qt, Signal)


class TestWindow(QWidget):

    temperature_stabilized = Signal(float)

    def __init__(self):
        super().__init__()

        with open("config/mdc.json", "r") as f:
            mdc = json.load(f)

        #Graph plotting
        self.plotA = pg.PlotWidget(title="Temperature v Time")
        # self.plotB = pg.PlotWidget(title="Channel B")
        # self.plotC = pg.PlotWidget(title="Channel C")
        # self.plotD = pg.PlotWidget(title="Channel D")
        # self.showA = QCheckBox("Hide Graph A")
        # self.showB = QCheckBox("Hide Graph B")
        # self.showC = QCheckBox("Hide Graph C")
        # self.showD = QCheckBox("Hide Graph D")

        self.times = []

        self.tempAData = []
        self.tempBData = []
        self.tempCData = []
        self.tempDData = []

        # for plot in [self.plotA, self.plotB, self.plotC, self.plotD]:
        #     plot.setLabel("left", "Temperature", units="K")
        #     plot.setLabel("bottom", "Time", units="s")
        self.plotA.setLabel("left", "Temperature", units="K")
        self.plotA.setLabel("bottom", "Time", units="s")
        legend = self.plotA.addLegend()
        legend.anchor((1, 0), (1, 0))  # top-right

        self.curveA = self.plotA.plot(name="Channel A",pen='r')
        self.curveB = self.plotA.plot(name="Channel B",pen='g')
        self.curveC = self.plotA.plot(name="Channel C",pen='b')
        self.curveD = self.plotA.plot(name="Channel D",pen='white')

        self.start_time = None

        self.times = []

        self.auto_proceed = False #Initialize the automatic temperature advancement

        self.setWindowTitle("Cryocon Logger")

        self.connectStatus = QLabel("Disconnected")
        self.runStatus = QLabel("Stopped")
        self.tempA = QLabel("--")
        self.tempB = QLabel("--")
        self.tempC = QLabel("--")
        self.tempD = QLabel("--")

        self.stableA = QLabel("Unknown")
        self.stableB = QLabel("Unknown")
        self.stableC = QLabel("Unknown")
        self.stableD = QLabel("Unknown")

        self.comment = QLineEdit()

        self.filename = QLineEdit()
    
        # self.interval = QSpinBox()
        # self.interval.setRange(1, 3600)
        # self.interval.setValue(10)

        #to optionally truncate old graph data
        self.truncate = QSpinBox()
        self.truncate.setRange(1,10000)
        self.truncate.setValue(10000)


        self.startButton = QPushButton("Start Logging")
        self.stopButton = QPushButton("Stop Logging")
        self.connectButton = QPushButton("Connect to Cryocon")
        self.commentButton = QPushButton("Save Comment")
        self.simcheck = QCheckBox("Simulate Random Data?")
        self.setRangeButton = QPushButton("Set Temperature Range")

        #channel optional buttons
        self.channelA = QCheckBox('Channel A')
        self.channelB = QCheckBox('Channel B')
        self.channelC = QCheckBox('Channel C')
        self.channelD = QCheckBox('Channel D')

        #timer to continuously update temperatures
        self.guiTimer = QTimer()
        self.guiTimer.timeout.connect(self.update_temperatures)
        self.guiTimer.start(1000)   # Update every 500 ms


        #Layout and tabs
        tabs = QTabWidget()

        airTab = QWidget()
        sampleTab = QWidget()
        tcontTab = QWidget()


        # Tab 1:Temperature Controller
    
        loggerTab = QWidget()

        mainLayout = QHBoxLayout()

        controlsLayout = QVBoxLayout()
        tempcontLayout = QVBoxLayout()
        graphLayout = QVBoxLayout()

        #seperator lines to help visual clarity
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setFrameShadow(QFrame.Sunken)

        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setFrameShadow(QFrame.Sunken)

        #Temperature range stuff
        self.startTemp = QDoubleSpinBox()
        self.startTemp.setRange(0, 400)
        self.startTemp.setDecimals(3)
        self.startTemp.setValue(4.0)

        self.endTemp = QDoubleSpinBox()
        self.endTemp.setRange(0, 400)
        self.endTemp.setDecimals(3)
        self.endTemp.setValue(10.0)

        self.stepTemp = QDoubleSpinBox()
        self.stepTemp.setRange(0.001, 100)
        self.stepTemp.setDecimals(3)
        self.stepTemp.setValue(1.0)

        self.rangeLabel = QLabel("Range: Not Set")

        self.proceedButton = QPushButton("Proceed to Next Temperature")

        controlsLayout.addWidget(self.simcheck)
        controlsLayout.addWidget(self.connectButton)
        
        buttons = QHBoxLayout()
        buttons.addWidget(self.startButton)
        buttons.addWidget(self.stopButton)
        controlsLayout.addLayout(buttons)

        controlsLayout.addWidget(self.connectStatus)
        controlsLayout.addWidget(self.runStatus) 

        tempALayout = QHBoxLayout()
        tempALayout.addWidget(QLabel("Temperature A   -"))
        tempALayout.addWidget(self.stableA)
        controlsLayout.addLayout(tempALayout)
        controlsLayout.addWidget(self.tempA)

        tempBLayout = QHBoxLayout()
        tempBLayout.addWidget(QLabel("Temperature B    -"))
        tempBLayout.addWidget(self.stableB)
        controlsLayout.addLayout(tempBLayout)
        controlsLayout.addWidget(self.tempB)

        tempCLayout = QHBoxLayout()
        tempCLayout.addWidget(QLabel("Temperature C   -"))
        tempCLayout.addWidget(self.stableC)
        controlsLayout.addLayout(tempCLayout)
        controlsLayout.addWidget(self.tempC)

        tempDLayout = QHBoxLayout()
        tempDLayout.addWidget(QLabel("Temperature D   -"))
        tempDLayout.addWidget(self.stableD)
        controlsLayout.addLayout(tempDLayout)
        controlsLayout.addWidget(self.tempD)

        controlsLayout.addWidget(QLabel("Comment"))
        controlsLayout.addWidget(self.comment)

        # controlsLayout.addWidget(QLabel("Interval"))
        # controlsLayout.addWidget(self.interval)

        controlsLayout.addWidget(QLabel("Truncate old graph data after X seconds"))
        controlsLayout.addWidget(self.truncate)          

        buttons2 = QVBoxLayout()
        buttons2.addWidget(self.commentButton)
        controlsLayout.addLayout(buttons2)

        #Here starts the buttons that send requests to cryocon including setp, etc.
        tempcontLayout.addWidget(QLabel("Temperature Range"))

        #temperature Range Layout

        rangeLayout = QHBoxLayout()

        rangeLayout.addWidget(QLabel("Start"))
        rangeLayout.addWidget(QLabel("End"))
        rangeLayout.addWidget(QLabel("Step"))

        rangeLayout2 = QHBoxLayout()
        rangeLayout2.addWidget(self.startTemp)
        rangeLayout2.addWidget(self.endTemp)
        rangeLayout2.addWidget(self.stepTemp)


        tempcontLayout.addLayout(rangeLayout)
        tempcontLayout.addLayout(rangeLayout2)

        tempcontLayout.addWidget(self.setRangeButton)

        tempcontLayout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        tempcontLayout.addWidget(QLabel("Filename"))
        tempcontLayout.addWidget(self.filename)

        # Active Channels
        tempcontLayout.addWidget(QLabel("Active Channels"))

        channelcontLayout1 = QHBoxLayout()
        channelcontLayout1.addWidget(self.channelA)
        channelcontLayout1.addWidget(self.channelB)
        channelcontLayout2 = QHBoxLayout() 
        channelcontLayout2.addWidget(self.channelC)
        channelcontLayout2.addWidget(self.channelD)
        tempcontLayout.addLayout(channelcontLayout1)
        tempcontLayout.addLayout(channelcontLayout2)

        # Proceed to next temperature
        tempcontLayout.addWidget(self.proceedButton)

        graphLayout.addWidget(self.plotA)


        mainLayout.addLayout(controlsLayout, 0)
        mainLayout.addWidget(separator1)
        mainLayout.addLayout(tempcontLayout, 0)
        mainLayout.addWidget(separator2)
        mainLayout.addLayout(graphLayout, 1)

        loggerTab.setLayout(mainLayout)

        #Tab 2: Going to be the motor control
        motorTab = QWidget()
        motorLayout = QHBoxLayout()
        parent_start = QVBoxLayout()
        parent_auto = QVBoxLayout()
        parent_manual = QVBoxLayout()
        parent_stop = QVBoxLayout()

    
        self.connectStatus_motor = QLabel("Status: <b> Disconnected </b>")

        self.comment_motor = QLineEdit()
        self.filename_motor = QLineEdit()

        self.connectButton_motor = QPushButton("Connect to Zaber X-MCA-S")
        self.commentButton_motor = QPushButton("Save Comment")

        self.variableButton = QPushButton("Confirm Set Variables")
        self.variableStatus = QLabel("Status: <b> Unconfirmed </b>")

        self.home = QDoubleSpinBox()
        self.home.setRange(0.500, 1.000)
        self.home.setDecimals(3)
        self.home.setSingleStep(0.050)
        self.home.setValue(0.500)
        self.home.setReadOnly(True)

        self.min = QDoubleSpinBox()
        self.min.setRange(0, 1.000)
        self.min.setDecimals(3)
        self.min.setSingleStep(0.050)
        self.min.setValue(0)
        self.min.setReadOnly(True)

        self.max = QDoubleSpinBox()
        self.max.setRange(0.750, 4.000)
        self.max.setDecimals(3)
        self.max.setSingleStep(0.050)
        self.max.setValue(4.000)
        self.max.setReadOnly(True)

        self.lockvariables = QCheckBox("Lock Variables")
        self.lockvariables.setChecked(True)

        self.abs = QDoubleSpinBox()
        self.abs.setRange(0.500, 4.000)
        self.abs.setDecimals(3)
        self.abs.setSingleStep(0.050)
        self.abs.setValue(0.500)

        self.rel = QDoubleSpinBox()
        self.rel.setRange(-3.000, 3.000)
        self.rel.setDecimals(3)
        self.rel.setSingleStep(0.050)
        self.rel.setValue(0.000)

        self.stepsize0 = QDoubleSpinBox()
        self.stepsize0.setRange(0.100, 0.500)
        self.stepsize0.setDecimals(3)
        self.stepsize0.setSingleStep(0.010)
        self.stepsize0.setValue(0.200)

        self.precision = QDoubleSpinBox()
        self.precision.setRange(0.001, 0.100)
        self.precision.setDecimals(3)
        self.precision.setSingleStep(0.001)
        self.precision.setValue(0.001)

        self.vdisplay = QDoubleSpinBox()
        self.vdisplay.setDecimals(3)
        self.vdisplay.setSpecialValueText("--")
        self.vdisplay.setReadOnly(True)
        self.vdisplay.setButtonSymbols(QDoubleSpinBox.NoButtons)

        self.confirmation = False

        self.autofindButton = QPushButton("Find Null Position")
        self.nullStatus = QLabel("Status: <b> Disconnected </b>")
        self.gethomeButton = QPushButton("Get Home Position")
        self.homeStatus = QLabel("Status: <b> Disconnected </b>")
        self.getposButton = QPushButton("Get Position")
        self.posStatus = QLabel("Status: <b> Disconnected </b>")
        self.absButton = QPushButton("Enter")
        self.relButton = QPushButton("Enter")
        self.setnullButton = QPushButton("Set Null Position")
        self.setnullStatus = QLabel("Status: <b> Disconnected </b>")
        self.rehomeButton = QPushButton("Return motor to home")
        self.rehomeStatus = QLabel("Status: <b> Disconnected </b>")
        self.stopButton_motor = QPushButton("Stop logging")
        self.stopStatus_motor = QLabel("Run Status: <b> Disconnected </b>")

        # MetaData
        self.mdc_min_label = QLabel("min_inch:")
        self.mdc_min = QLabel(str(mdc["min_inch"]))
        self.mdc_max_label = QLabel("max_inch:")
        self.mdc_max = QLabel(str(mdc["max_inch"]))
        self.mdc_step_conversion_label = QLabel("steps_per_inch:")
        self.mdc_step_conversion = QLabel(str(mdc["steps_per_inch"]))
        # Layout
        parent_start.addWidget(self.connectStatus_motor)
        parent_start.addWidget(self.connectButton_motor)

        parent_start.addWidget(QLabel("Filename"))
        parent_start.addWidget(self.filename_motor)

        parent_start.addWidget(QLabel("Comment"))
        parent_start.addWidget(self.comment_motor)

        buttons = QVBoxLayout()
        buttons.addWidget(self.commentButton_motor)
        parent_start.addLayout(buttons)

        var_box = QGroupBox()
        var_layout = QHBoxLayout()
        var_layout1 = QVBoxLayout()
        var_layout1.addWidget(QLabel("Reference position (in)"))
        var_layout1.addWidget(self.home)
        var_layout1.addStretch()
        var_layout2 = QVBoxLayout()
        #var_layout2.addWidget(QLabel("Min (in)"))
        #var_layout2.addWidget(self.min)
        var_layout2.addStretch()
        var_layout3 = QVBoxLayout()
        #var_layout3.addWidget(QLabel("Max (in)"))
        #var_layout3.addWidget(self.max)
        var_layout3.addStretch()
        var_layout4 = QVBoxLayout()
        var_layout4.addWidget(self.variableStatus)
        var_layout4.addWidget(self.variableButton)
        var_layout4.addWidget(self.lockvariables)
        var_layout4.addStretch()
        var_layout.addLayout(var_layout1)
        var_layout.addLayout(var_layout2)
        var_layout.addLayout(var_layout3)
        var_layout.addLayout(var_layout4)
        var_box.setLayout(var_layout)
        parent_start.addWidget(var_box)
        parent_start.addStretch()

        motorLayout.addLayout(parent_start)

        auto_box = QGroupBox("Automatic Null Finder")
        auto_layout = QVBoxLayout()
        #auto_layout.addWidget(QLabel("<b> Automatic Null Finder </b>"))
        auto_layout.addWidget(QLabel("Initial Step Size (in)"))
        auto_layout.addWidget(self.stepsize0)
        auto_layout.addWidget(QLabel("Precision (in)"))
        auto_layout.addWidget(self.precision)
        auto_layout.addWidget(self.nullStatus)
        auto_layout.addWidget(self.autofindButton)
        auto_box.setLayout(auto_layout)
        parent_auto.addWidget(auto_box)
        parent_auto.addStretch()

        motorLayout.addLayout(parent_auto)

        manual_box = QGroupBox("Manual Null Finder")
        manual_layout = QVBoxLayout()
        #manual_layout.addWidget(QLabel("<b> Manual Null Finder </b>"))
        manual_layout.addWidget(self.homeStatus)
        manual_layout.addWidget(self.gethomeButton)
        manual_layout.addWidget(self.posStatus)
        manual_layout.addWidget(self.getposButton)
        manual_layout.addWidget(QLabel("Move abs (in)"))
        manual_abs = QHBoxLayout()
        manual_abs.addWidget(self.abs)
        manual_abs.addWidget(self.absButton)
        manual_layout.addLayout(manual_abs)
        manual_layout.addWidget(QLabel("Move rel (in)"))
        manual_rel = QHBoxLayout()
        manual_rel.addWidget(self.rel)
        manual_rel.addWidget(self.relButton)
        manual_layout.addLayout(manual_rel)
        manual_layout.addWidget(QLabel("Voltage (V)"))
        manual_layout.addWidget(self.vdisplay)
        manual_layout.addWidget(self.setnullStatus)
        manual_layout.addWidget(self.setnullButton)
        manual_box.setLayout(manual_layout)
        parent_manual.addWidget(manual_box)
        parent_manual.addStretch()

        motorLayout.addLayout(parent_manual)

        completion_box = QVBoxLayout()
        completion_box.addWidget(self.rehomeStatus)
        completion_box.addWidget(self.rehomeButton)
        completion_box.addWidget(self.stopStatus_motor)
        completion_box.addWidget(self.stopButton_motor)
        parent_stop.addLayout(completion_box)


        metadata = QVBoxLayout()
        metadata1 = QHBoxLayout()
        metadata1.addWidget(self.mdc_min_label)
        metadata1.addWidget(self.mdc_min)
        metadata.addLayout(metadata1)
        metadata2 = QHBoxLayout()
        metadata2.addWidget(self.mdc_max_label)
        metadata2.addWidget(self.mdc_max)
        metadata.addLayout(metadata2)
        metadata3 = QHBoxLayout()
        metadata3.addWidget(self.mdc_step_conversion_label)
        metadata3.addWidget(self.mdc_step_conversion)
        metadata.addLayout(metadata3)
        metadata_box = QGroupBox("MDC Metadata")
        metadata_box.setLayout(metadata)
        parent_stop.addWidget(metadata_box)
        parent_stop.addLayout(metadata)
        parent_stop.addStretch()


        motorLayout.addLayout(parent_stop)

        self.setLayout(motorLayout)

        #FINAL SETUP
        motorTab.setLayout(motorLayout)

        #new tabs setup (not finished)
        waveTab = QWidget()

        tabs.addTab(airTab, "Air Scans")
        tabs.addTab(sampleTab, "Sample Scans")
        tabs.addTab(tcontTab, "T-Controlled Scans")
        tabs.addTab(loggerTab, "Temperature Logger")
        tabs.addTab(motorTab, "Motor Control")
        tabs.addTab(waveTab, "Waveform Aquisition")

        windowLayout = QVBoxLayout()
        windowLayout.addWidget(tabs)

        self.setLayout(windowLayout)

        #connect buttons to functions
        self.startButton.clicked.connect(self.start_logging)
        self.stopButton.clicked.connect(self.stop_logging)
        self.connectButton.clicked.connect(self.setup_instrument)
        self.commentButton.clicked.connect(self.add_comment)
        self.setRangeButton.clicked.connect(self.set_temperature_range)
        self.temperature_stabilized.connect(self.show_stabilized_popup)
        self.proceedButton.clicked.connect(self.next_temp)

        #connect buttons for motor control
        self.connectButton_motor.clicked.connect(self.setup_instrument_motor)
        self.commentButton_motor.clicked.connect(self.add_comment_motor)
        self.variableButton.clicked.connect(self.set_variables)
        self.autofindButton.clicked.connect(self.auto_null)
        self.gethomeButton.clicked.connect(self.get_home)
        self.getposButton.clicked.connect(self.get_pos)
        self.gethomeButton.clicked.connect(self.get_home)
        self.relButton.clicked.connect(self.move_rel)
        self.absButton.clicked.connect(self.move_abs)
        self.setnullButton.clicked.connect(self.set_null)
        self.rehomeButton.clicked.connect(self.rehome)
        self.stopButton_motor.clicked.connect(self.stop_logging_motor)
        self.lockvariables.checkStateChanged.connect(self.unlock)

    #FUNCTIONS THAT INTERACT WITH CRYOCON START HERE
    def setup_instrument(self):
        if not self.filename.text().strip():
            QMessageBox.critical(
                self,
                "Error",
                "File name is empty or contains only spaces"
            )
            return
        active_channels = self.get_active_channels()

        if not active_channels:
            QMessageBox.warning(
                self,
                "No Active Channels",
                "Please select at least one active channel."
            )
            return

        print("Active channels:", active_channels) #remove this line later, just using to check if active channels is working

        if self.simcheck.isChecked():
            self.inst = FakeCryocon34()
            self.connectStatus.setText("Using Fake Cryocon")
        else:
            try:
                self.inst = Cryocon34()
                self.connectStatus.setText("Ready")
            except Exception as e:
                QMessageBox.critical(self, "Connection Error", str(e))
                return

        self.logger = temperature_logger(
            filename=self.filename.text(),
            channels=active_channels,
        )
        self.temperature_loop = TemperatureLoop(
            controller=self.inst,
            temperature_arange=self.temperature_arange,
            channels=active_channels,
            logger=self.logger,
            stability_callback=self.temperature_stabilized.emit,


    )


    def start_logging(self):

        self.ask_auto_proceed()

        if not self.logger:
            self.connectStatus.setText("No logger initialized")
            return
        else:
            self.start_time = time.monotonic()
            # Clear old graph data
            self.times.clear()
            self.tempAData.clear()
            self.tempBData.clear()
            self.tempCData.clear()
            self.tempDData.clear()

            # Clear graphs
            self.curveA.clear()
            self.curveB.clear()
            self.curveC.clear()
            self.curveD.clear()

            self.logger.interval = 10
            self.temperature_loop.start()
            self.runStatus.setText("Logging...")

    def stop_logging(self):
        self.temperature_loop.stop()
        self.logger.close() 
        self.runStatus.setText("Stopped")

    def add_comment(self):
        self.logger.add_comment(self.comment.text())
    
    def file_name(self):
        self.filename

    def update_temperatures(self):

        if not hasattr(self, "temperature_loop"):
            return

        temps = self.temperature_loop.temperatures
        stabilities = self.temperature_loop.stabilities
        active_channels = self.temperature_loop.channels

        # Update temperature and stability indicators
        if "A" in active_channels:
            self.tempA.setText(
                "--" if np.isnan(temps["A"])
                else f"{temps['A']:.3f} K"
            )

            self.stableA.setText(
                "Stable" if stabilities["A"].stable
                else "Not Stable"
                )

        if "B" in active_channels:
            self.tempB.setText(
                "--" if np.isnan(temps["B"])
                else f"{temps['B']:.3f} K"
            )

            self.stableB.setText(
                "Stable" if stabilities["B"].stable
                else "Not Stable"
            )

        if "C" in active_channels:
            self.tempC.setText(
                "--" if np.isnan(temps["C"])
                else f"{temps['C']:.3f} K"
            )

            self.stableC.setText(
                "Stable" if stabilities["C"].stable
                else "Not Stable"
            )

        if "D" in active_channels:
            self.tempD.setText(
                "--" if np.isnan(temps["D"])
                else f"{temps['D']:.3f} K"
            )

            self.stableD.setText(
                "Stable" if stabilities["D"].stable
                else "Not Stable"
            )

        # Don't add graph data until logging has started
        if self.start_time is None:
            return

        current_time = time.monotonic() - self.start_time
        self.times.append(current_time)

        # Store temperature data
        if "A" in active_channels:
            self.tempAData.append(temps["A"])

        if "B" in active_channels:
            self.tempBData.append(temps["B"])

        if "C" in active_channels:
            self.tempCData.append(temps["C"])

        if "D" in active_channels:
            self.tempDData.append(temps["D"])

        # Truncate old data
        window = self.truncate.value()

        while self.times and (current_time - self.times[0]) > window:
            self.times.pop(0)

            if "A" in active_channels:
                self.tempAData.pop(0)

            if "B" in active_channels:
                self.tempBData.pop(0)

            if "C" in active_channels:
                self.tempCData.pop(0)

            if "D" in active_channels:
                self.tempDData.pop(0)

        # Update plots
        if "A" in active_channels:
            self.curveA.setData(self.times, self.tempAData)

        if "B" in active_channels:
            self.curveB.setData(self.times, self.tempBData)

        if "C" in active_channels:
            self.curveC.setData(self.times, self.tempCData)

        if "D" in active_channels:
            self.curveD.setData(self.times, self.tempDData)

    def set_temperature_range(self):

        start = self.startTemp.value()
        end = self.endTemp.value()
        step = self.stepTemp.value()

        if end <= start:
            QMessageBox.warning(
                self,
                "Invalid Range",
                "End temperature must be greater than start temperature"
            )
            return

        self.temperature_arange = list(
            np.arange(
                start,
                end + step,
                step
            )
        )

        self.rangeLabel.setText(
            f"Range: {self.temperature_arange}"
        )

        print("Temperature range:", self.temperature_arange)

    def show_stabilized_popup(self, temperature):

        if self.auto_proceed is True:
            self.next_temp()
        else:
            QMessageBox.information(
                self,
                "Temperature Stabilized",
                f"All channels have stabilized at {temperature:.3f} K."
            )

    def next_temp(self):
        self.temperature_loop.next_temperature()

    def get_active_channels(self):
        channels = []

        if self.channelA.isChecked():
            channels.append("A")

        if self.channelB.isChecked():
            channels.append("B")

        if self.channelC.isChecked():
            channels.append("C")

        if self.channelD.isChecked():
            channels.append("D")

        return tuple(channels)

    def ask_auto_proceed(self):
        msgbox = QMessageBox.question(
            self,
            "Automatically Proceed?",
            "Do you wish to automatically proceed to the next temperature once all channels have stabilized?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if msgbox == QMessageBox.Yes:
            self.auto_proceed = True
            print("Automatic progression enabled")
        else:
            self.auto_proceed = False
            print("Automatic progression disabled")

    #FUNCTIONS THAT CONTROL MOTOR START HERE
    def setup_instrument_motor(self):
        if not self.filename_motor.text().strip():
            QMessageBox.critical(
                None,
                "Error",
                "File name is empty or contains only spaces")
        elif self.confirmation == False:
            QMessageBox.critical(
                None,
                "Warning",
                "Home position defines the zero reference for microsteps in the motor. "
                f"Beginning of runs assumes this as {self.home.value()} in. "
                "Please confirm visually before connecting.")
        else:
            self.logger.start()
            self.logger.move_abs(self.home.value())
            self.stopStatus.setText("Run Status: <b> Running </b>")

    def add_comment_motor(self):
        self.logger.add_comment(self.comment_motor.text())

    def set_variables(self):
        if (self.max.value() < self.home.value()) or (self.home.value() < self.min.value()):
            QMessageBox.critical(
                None,
                "Error",
                f"Home position is out of bounds.")
        else:
            self.confirmation = True
            self.logger = NullFinder(
                _min=self.min.value(),
                _max=self.max.value(),
                _home=self.home.value(),
                filename=self.filename_motor.text()
            )
            self.variableStatus.setText("Status: <b>Confirmed</b>")
            self.connectStatus.setText("Status: <b> Ready </b>")

    def auto_null(self):
        self.nullStatus.setText("Status: <b>Searching</b>")
        self.logger.find_null(self.stepsize0.value(), self.precision.value())
        self.null = self.logger.null
        self.nullStatus.setText(
            f"Status: Null found and set as {self.null} in")

    def get_home(self):
        self.homeStatus.setText(f"Status: Home is {self.logger.get_home} in")

    def get_pos(self):
        val = self.logger.pos_in_inches() + self.home
        self.logger.write_pos()
        self.posStatus.setText(f"Status: Position is {val} in")
        self.voltage()

    def move_rel(self):
        val = self.logger.pos_in_inches() + self.home.value() + self.rel.value()

        if (self.max.value() < val) or (val < self.min.value()):
            QMessageBox.critical(
                None,
                "Error",
                f"Moving {self.rel.value()} in is out of bounds.")
        else:
            self.logger.move_rel(self.rel.value())
            self.logger.write_pos()
            self.voltage()

    def move_abs(self):
        if (self.max.value() < self.abs.value()) or (self.abs.value() < self.min.value()):
            QMessageBox.critical(
                None,
                "Error",
                f"Moving {self.abs.value()} in is out of bounds.")
        else:
            self.logger.move_abs(self.abs.value())
            self.logger.write_pos()
            self.voltage()

    def set_null(self):
        self.logger.set_null()
        self.setnullStatus.setText(f"Status: This position is set as null")

    def rehome(self):
        self.logger.move_abs(self.home.value())
        self.rehomeStatus.setText(f"Status: Complete")

    def stop_logging_motor(self):
        self.logger.stop()
        self.stopStatus.setText("Run Status: <b> Stopped </b>")

    def voltage(self):
       val = self.logger.get_voltage()
       self.vdisplay.blockSignals(True)
       self.vdisplay.setValue(val)
       self.vdisplay.blockSignals(False)

    def unlock(self, state):
        if state == Qt.CheckState.Checked:
            self.min.setReadOnly(True)
            self.max.setReadOnly(True)
            self.home.setReadOnly(True)
        elif state == Qt.CheckState.Unchecked:
            self.min.setReadOnly(False)
            self.max.setReadOnly(False)
            self.home.setReadOnly(False)
