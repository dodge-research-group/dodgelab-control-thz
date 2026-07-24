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
# DELETE THIS ONCE gui.py and main.py is updated
# from cryocon import  (
#     connect_cryocon,
#     read_temp,
#     CryoconLogger,
#     FakeCryocon 
# )   

from Instruments.Cryocon34 import Cryocon34
from Instruments.Fake_Cryocon34 import FakeCryocon34
from Instruments.Temperature_controllers import TemperatureController
from Instruments.temperature_logger import temperature_logger
from Instruments.Temperature_loop import TemperatureLoop
from Instruments.temperature_stability import temperature_stability


from PySide6.QtCore import QTimer


class TestWindow(QWidget):

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

        layout.addWidget(QLabel("Filename (.csv)"))
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
            temperature_arange=[4,5,6,7],
            channels=("A","B","C","D"),
            logger=self.logger
    )


    def start_logging(self):

        if not self.logger:
            self.connectStatus.setText("No logger initialized")
            return
        else:
            self.logger.interval = self.interval.value()
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