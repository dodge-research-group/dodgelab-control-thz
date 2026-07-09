from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QSpinBox,
    QCheckBox,
    QMessageBox
)
from cryocon import  (
    connect_cryocon,
    read_temp,
    CryoconLogger,
    FakeCryocon 
)   

from PySide6.QtCore import (QTimer,Signal)
import pyqtgraph as pg
import time

class TestWindow(QWidget):

    temperaturesUpdated = Signal(list)

    def __init__(self):

        super().__init__()

        #Graph plotting
        self.plotA = pg.PlotWidget(title="Channel A")
        self.plotB = pg.PlotWidget(title="Channel B")
        self.plotC = pg.PlotWidget(title="Channel C")
        self.plotD = pg.PlotWidget(title="Channel D")

        for plot in [self.plotA, self.plotB, self.plotC, self.plotD]:
            plot.setLabel("left", "Temperature", units="K")
            plot.setLabel("bottom", "Time", units="s")

        self.curveA = self.plotA.plot(name="Channel A",pen='r')
        self.curveB = self.plotB.plot(name="Channel B",pen='g')
        self.curveC = self.plotC.plot(name="Channel C",pen='b')
        self.curveD = self.plotD.plot(name="Channel D",pen='white')

        self.setWindowTitle("Cryocon Logger")

        self.startTime = None

        self.times = []
        self.tempAData = []
        self.tempBData = []
        self.tempCData = []
        self.tempDData = []

        self.connectStatus = QLabel("Disconnected")
        self.runStatus = QLabel("Stopped")
        self.tempA = QLabel("--")
        self.tempB = QLabel("--")
        self.tempC = QLabel("--")
        self.tempD = QLabel("--")

        self.comment = QLineEdit()

        self.filename = QLineEdit()
    
        self.interval = QSpinBox()
        self.interval.setRange(1, 3600)
        self.interval.setValue(10)


        self.startButton = QPushButton("Start Logging")
        self.stopButton = QPushButton("Stop Logging")
        self.connectButton = QPushButton("Connect to Cryocon")
        self.commentButton = QPushButton("Save Comment")
        self.simcheck = QCheckBox("Simulate Random Data?")

        mainLayout = QHBoxLayout()

        controlsLayout = QVBoxLayout()
        graphLayout = QGridLayout()

        controlsLayout.addWidget(self.simcheck)
        controlsLayout.addWidget(self.connectButton)

        controlsLayout.addWidget(self.connectStatus)
        controlsLayout.addWidget(self.runStatus)

        controlsLayout.addWidget(QLabel("Temperature A"))
        controlsLayout.addWidget(self.tempA)

        controlsLayout.addWidget(QLabel("Temperature B"))
        controlsLayout.addWidget(self.tempB)

        controlsLayout.addWidget(QLabel("Temperature C"))
        controlsLayout.addWidget(self.tempC)

        controlsLayout.addWidget(QLabel("Temperature D"))
        controlsLayout.addWidget(self.tempD)

        controlsLayout.addWidget(QLabel("Comment"))
        controlsLayout.addWidget(self.comment)

        controlsLayout.addWidget(QLabel("Filename"))
        controlsLayout.addWidget(self.filename)

        controlsLayout.addWidget(QLabel("Interval"))
        controlsLayout.addWidget(self.interval)

        buttons = QHBoxLayout()
        buttons.addWidget(self.startButton)
        buttons.addWidget(self.stopButton)
        controlsLayout.addLayout(buttons)          

        buttons2 = QVBoxLayout()
        buttons2.addWidget(self.commentButton)
        controlsLayout.addLayout(buttons2)
    
        graphLayout.addWidget(self.plotA, 0, 0)
        graphLayout.addWidget(self.plotB, 0, 1)
        graphLayout.addWidget(self.plotC, 1, 0)
        graphLayout.addWidget(self.plotD, 1, 1)

        mainLayout.addLayout(controlsLayout, 1)
        mainLayout.addLayout(graphLayout, 3)
        self.setLayout(mainLayout)

        self.startButton.clicked.connect(self.start_logging)
        self.stopButton.clicked.connect(self.stop_logging)
        self.connectButton.clicked.connect(self.setup_instrument)
        self.commentButton.clicked.connect(self.add_comment)
        self.temperaturesUpdated.connect(self.update_temperatures)

    def setup_instrument(self):

        if not self.filename.text().strip():
            QMessageBox.critical(None, "Error", "File name is empty or contains only spaces")
        else:
            if self.simcheck.isChecked():
                self.inst = FakeCryocon()
                self.connectStatus.setText("Using Fake Cryocon")
            else:
                self.inst = connect_cryocon("GPIB0::7::INSTR")
                self.connectStatus.setText("Ready")
            self.logger = CryoconLogger(
                self.inst,
                channels=("A", "B", "C", "D"),
                interval=self.interval.value(),
                filename=self.filename.text(),
                update_callback=self.temperaturesUpdated.emit
                )


    def start_logging(self):

        if self.logger is None:
            self.connectStatus.setText("No logger initialized")
            return
        if len(self.times) > 0:
            reply = QMessageBox.question(
                self,
                "Clear Graphs?",
                "Graphs already contain data. Clear graphs before starting?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.clear_graphs()
        
        self.logger.interval = self.interval.value()
        self.logger.start()
        self.runStatus.setText("Logging...")

    def stop_logging(self):
        self.logger.stop()
        self.runStatus.setText("Stopped")

    def add_comment(self):
        self.logger.add_comment(self.comment.text())

    
    def update_temperatures(self, temps):

        if self.startTime is None:
            self.startTime = time.time()

        elapsed = time.time() - self.startTime

        self.times.append(elapsed)

        self.tempAData.append(temps[0])
        self.tempBData.append(temps[1])
        self.tempCData.append(temps[2])
        self.tempDData.append(temps[3])

        labels = [self.tempA, self.tempB, self.tempC, self.tempD]

        for label, temp in zip(labels, temps):
            if temp is None:
                label.setText("--")
            else:
                label.setText(f"{temp:.3f} K")

        self.curveA.setData(self.times, self.tempAData)
        self.curveB.setData(self.times, self.tempBData)
        self.curveC.setData(self.times, self.tempCData)
        self.curveD.setData(self.times, self.tempDData)
    
    def clear_graphs(self):

        self.times.clear()

        self.tempAData.clear()
        self.tempBData.clear()
        self.tempCData.clear()
        self.tempDData.clear()

        self.startTime = None

        self.curveA.clear()
        self.curveB.clear()
        self.curveC.clear()
        self.curveD.clear()