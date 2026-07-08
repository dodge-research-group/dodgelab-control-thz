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
    QMessageBox
)
from cryocon import  (
    connect_cryocon,
    read_temp,
    CryoconLogger,
    FakeCryocon 
)   

from PySide6.QtCore import (QTimer,Signal)


class TestWindow(QWidget):

    temperaturesUpdated = Signal(list)

    def __init__(self):

        super().__init__()

        self.setWindowTitle("Cryocon Logger")

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

        layout = QVBoxLayout()

        layout.addWidget(self.simcheck)
        layout.addWidget(self.connectButton)

        layout.addWidget(self.connectStatus)
        layout.addWidget(self.runStatus)

        layout.addWidget(QLabel("Temperature A"))
        layout.addWidget(self.tempA)

        layout.addWidget(QLabel("Temperature B"))
        layout.addWidget(self.tempB)

        layout.addWidget(QLabel("Temperature C"))
        layout.addWidget(self.tempC)

        layout.addWidget(QLabel("Temperature D"))
        layout.addWidget(self.tempD)

        layout.addWidget(QLabel("Comment"))
        layout.addWidget(self.comment)

        layout.addWidget(QLabel("Filename"))
        layout.addWidget(self.filename)

        layout.addWidget(QLabel("Interval"))
        layout.addWidget(self.interval)

        buttons = QHBoxLayout()
        buttons.addWidget(self.startButton)
        buttons.addWidget(self.stopButton)
        layout.addLayout(buttons)          

        buttons2 = QVBoxLayout()
        buttons2.addWidget(self.commentButton)
        layout.addLayout(buttons2)
        self.setLayout(layout)
    
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
        else:
            self.logger.interval = self.interval.value()
            self.logger.start()
            self.runStatus.setText("Logging...")

    def stop_logging(self):
        self.logger.stop()
        self.runStatus.setText("Stopped")

    def add_comment(self):
        self.logger.add_comment(self.comment.text())

    
    def update_temperatures(self, temps):
        labels = [self.tempA, self.tempB, self.tempC, self.tempD]

        for label, temp in zip(labels, temps):
            if temp is None:
                label.setText("--")
            else:
                label.setText(f"{temp:.3f} K")