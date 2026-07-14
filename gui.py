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
        self.showA = QCheckBox("Hide Graph A")
        self.showB = QCheckBox("Hide Graph B")
        self.showC = QCheckBox("Hide Graph C")
        self.showD = QCheckBox("Hide Graph D")

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

        self.truncate = QSpinBox()
        self.truncate.setRange(1,10000)
        self.truncate.setValue(10000)

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

        controlsLayout.addWidget(QLabel("Truncate old graph data after how many seconds?"))
        controlsLayout.addWidget(self.truncate)

        buttons = QHBoxLayout()
        buttons.addWidget(self.startButton)
        buttons.addWidget(self.stopButton)
        controlsLayout.addLayout(buttons)          

        buttons2 = QVBoxLayout()
        buttons2.addWidget(self.commentButton)
        controlsLayout.addLayout(buttons2)
    

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

        self.plotA.setVisible(True)
        self.plotB.setVisible(True)
        self.plotC.setVisible(True)
        self.plotD.setVisible(True)

        mainLayout.addLayout(controlsLayout, 1)
        mainLayout.addLayout(graphLayout, 3)
        self.setLayout(mainLayout)

        self.startButton.clicked.connect(self.start_logging)
        self.stopButton.clicked.connect(self.stop_logging)
        self.connectButton.clicked.connect(self.setup_instrument)
        self.commentButton.clicked.connect(self.add_comment)
        self.temperaturesUpdated.connect(self.update_temperatures)

        self.showA.toggled.connect(self.plotA.setHidden)
        self.showB.toggled.connect(self.plotB.setHidden)
        self.showC.toggled.connect(self.plotC.setHidden)
        self.showD.toggled.connect(self.plotD.setHidden)

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

        window = self.truncate.value()

        while self.times and (elapsed - self.times[0]) > window:
            self.times.pop(0)
            self.tempAData.pop(0)
            self.tempBData.pop(0)
            self.tempCData.pop(0)
            self.tempDData.pop(0)

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