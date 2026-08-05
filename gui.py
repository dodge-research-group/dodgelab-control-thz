import numpy as np
import pyqtgraph as pg
import time

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
    QDoubleSpinBox
)

from Instruments.Cryocon34 import Cryocon34
from Instruments.Fake_Cryocon34 import FakeCryocon34
from Instruments.Temperature_controllers import TemperatureController
from Instruments.temperature_logger import temperature_logger
from Instruments.Temperature_loop import TemperatureLoop
from Instruments.temperature_stability import temperature_stability


from PySide6.QtCore import (QTimer, Qt, Signal)


class TestWindow(QWidget):

    temperature_stabilized = Signal(float)

    def __init__(self):
        super().__init__()

        #Graph plotting
        self.plotA = pg.PlotWidget(title="Channel A")
        self.plotB = pg.PlotWidget(title="Channel B")
        self.plotC = pg.PlotWidget(title="Channel C")
        self.plotD = pg.PlotWidget(title="Channel D")
        self.showA = QCheckBox("Hide Graph A")
        self.showB = QCheckBox("Hide Graph B")
        self.showC = QCheckBox("Hide Graph C")
        self.showD = QCheckBox("Hide Graph D")

        self.times = []

        self.tempAData = []
        self.tempBData = []
        self.tempCData = []
        self.tempDData = []

        for plot in [self.plotA, self.plotB, self.plotC, self.plotD]:
            plot.setLabel("left", "Temperature", units="K")
            plot.setLabel("bottom", "Time", units="s")

        self.curveA = self.plotA.plot(name="Channel A",pen='r')
        self.curveB = self.plotB.plot(name="Channel B",pen='g')
        self.curveC = self.plotC.plot(name="Channel C",pen='b')
        self.curveD = self.plotD.plot(name="Channel D",pen='white')

        self.start_time = None

        self.times = []


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


        #timer to continuously update temperatures
        self.guiTimer = QTimer()
        self.guiTimer.timeout.connect(self.update_temperatures)
        self.guiTimer.start(1000)   # Update every 500 ms

        mainLayout = QHBoxLayout()

        controlsLayout = QVBoxLayout()
        tempcontLayout = QVBoxLayout()
        graphLayout = QGridLayout()

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
        
        # Proceed to next temperature
        tempcontLayout.addWidget(self.proceedButton)

        # Graph layout

        graphLayout.setRowStretch(1, 1)
        graphLayout.setRowStretch(3, 1)
        graphLayout.setColumnStretch(0, 1)
        graphLayout.setColumnStretch(1, 1)

        graphLayout.addWidget(self.showA, 0, 0)
        graphLayout.addWidget(self.plotA, 1, 0)

        graphLayout.addWidget(self.showB, 0, 1)
        graphLayout.addWidget(self.plotB, 1, 1)

        graphLayout.addWidget(self.showC, 2, 0)
        graphLayout.addWidget(self.plotC, 3, 0)

        graphLayout.addWidget(self.showD, 2, 1)
        graphLayout.addWidget(self.plotD, 3, 1)


        mainLayout.addLayout(controlsLayout, 0)
        mainLayout.addWidget(separator1)
        mainLayout.addLayout(tempcontLayout, 0)
        mainLayout.addWidget(separator2)
        mainLayout.addLayout(graphLayout, 1)
        self.setLayout(mainLayout)

        #connect buttons to functions
        self.startButton.clicked.connect(self.start_logging)
        self.stopButton.clicked.connect(self.stop_logging)
        self.connectButton.clicked.connect(self.setup_instrument)
        self.commentButton.clicked.connect(self.add_comment)
        self.setRangeButton.clicked.connect(self.set_temperature_range)
        self.temperature_stabilized.connect(self.show_stabilized_popup)
        self.proceedButton.clicked.connect(self.next_temp)

    def setup_instrument(self):
        if not self.filename.text().strip():
            QMessageBox.critical(
                self,
                "Error",
                "File name is empty or contains only spaces"
            )
            return

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
            channels=("A","B","C","D"),
        )
        self.temperature_loop = TemperatureLoop(
            controller=self.inst,
            temperature_arange=self.temperature_arange,
            channels=("A","B","C","D"),
            logger=self.logger,
            stability_callback=self.temperature_stabilized.emit,

    )


    def start_logging(self):
        
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

        self.tempA.setText("--" if np.isnan(temps['A']) else (f"{temps['A']:.3f} K"))
        self.tempB.setText("--" if np.isnan(temps['B']) else (f"{temps['B']:.3f} K"))
        self.tempC.setText("--" if np.isnan(temps['C']) else (f"{temps['C']:.3f} K"))
        self.tempD.setText("--" if np.isnan(temps['D']) else (f"{temps['D']:.3f} K"))

        self.stableA.setText("Stable" if stabilities["A"].stable else "Not Stable")
        self.stableB.setText("Stable" if stabilities["B"].stable else "Not Stable")
        self.stableC.setText("Stable" if stabilities["C"].stable else "Not Stable")
        self.stableD.setText("Stable" if stabilities["D"].stable else "Not Stable")
        # add graph point
        if self.start_time is None:
            return
        
        current_time = time.monotonic() - self.start_time
        self.times.append(current_time)

        # store temperatures
        self.tempAData.append(temps["A"])
        self.tempBData.append(temps["B"])
        self.tempCData.append(temps["C"])
        self.tempDData.append(temps["D"])

        window = self.truncate.value()

        while self.times and (current_time - self.times[0]) > window:
            self.times.pop(0)
            self.tempAData.pop(0)
            self.tempBData.pop(0)
            self.tempCData.pop(0)
            self.tempDData.pop(0)

        # update plots
        self.curveA.setData(self.times, self.tempAData)
        self.curveB.setData(self.times, self.tempBData)
        self.curveC.setData(self.times, self.tempCData)
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
        QMessageBox.information(
            self,
            "Temperature Stabilized",
            f"All channels have stabilized at {temperature:.3f} K."
        )

    def next_temp(self):
        self.temperature_loop.next_temperature()
