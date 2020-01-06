import re

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QSlider, QDialog, QLineEdit, QPushButton, QHBoxLayout, QLabel, QGridLayout

from trnsysGUI.Connection import Connection


class MassFlowVisualizer(QDialog):

    def __init__(self, parent):

        super(MassFlowVisualizer, self).__init__(parent)
        self.setMinimumSize(1000, 300)

        self.parent = parent
        self.timeStep = 0
        self.timeSteps = 365    # 0 to 364
        self.dataFilePath = "massflowData/flows.txt"

        self.slider = QSlider(parent)
        self.setSlider()
        self.slider.sliderReleased.connect(self.testValChange)
        self.slider.sliderPressed.connect(self.pressedSlider)
        self.loadedFile = False
        self.qtm = QTimer(parent)
        self.lines = None
        self.started = False

        self.paused = True

        nameLabel = QLabel("Name:")
        self.currentStepLabel = QLabel("Step: " + str(self.slider.value()))
        self.le = QLineEdit("NONE")

        self.togglePauseButton = QPushButton("Pause/Continue")
        self.cancelButton = QPushButton("Cancel")

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.togglePauseButton)
        buttonLayout.addWidget(self.cancelButton)
        layout = QGridLayout()
        layout.addWidget(nameLabel, 0, 0)
        layout.addWidget(self.le, 0, 1)
        layout.addLayout(buttonLayout, 1, 0, 2, 0)
        layout.addWidget(self.currentStepLabel, 2, 0, 1, 2)
        layout.addWidget(self.slider, 3, 0, 1, 2)  # Only for debug (Why do I need a 3 here instead of a 2 for int:row?)
        self.setLayout(layout)

        self.togglePauseButton.clicked.connect(self.togglePause)
        self.cancelButton.clicked.connect(self.cancel)
        self.setWindowTitle("Flow visualizer")
        self.show()

    def togglePause(self):
        if self.paused:
            self.continueVis()
        else:
            self.pauseVis()

    def cancel(self):
        self.pauseVis()
        self.close()
        self.parent.updateConnGrads()

    def loadFile(self):
        if not self.loadedFile:
            file = open(self.dataFilePath, 'r')
            self.lines = file.readlines()
        self.loadedFile = True

    def start(self):
        self.loadFile()
        self.paused = False
        self.qtm = QTimer(self.parent)
        self.qtm.timeout.connect(self.advance)
        self.qtm.start(1000)

    def advance(self):
        if self.timeStep == 364:
            print("reached end of data, returning")
            self.qtm.stop()
            return

        if self.loadedFile:
            line = self.lines[self.timeStep]
            self.slider.setValue(self.timeStep)
            self.currentStepLabel.setText("Step: " + str(self.timeStep))
            self.timeStep += 1

            vals = re.sub(r" {1,}", " ", line)
            vals = vals.split(" ")[:-1]

            # print(vals)

            i = 0
            for t in self.parent.trnsysObj:
                if isinstance(t, Connection):
                    print("Found connection in ts " + str(self.timeStep) + " " + str(i))
                    if float(vals[i]) < 0:
                        t.setColor(mfr="NegMfr")
                    elif float(vals[i]) == 0:
                        t.setColor(mfr="ZeroMfr")
                    else:
                        t.setColor(mfr="PosMfr")
                    i += 1

        else:
            return

    def pauseVis(self):
        self.paused = True
        self.qtm.stop()

    def continueVis(self):
        if self.started:
            self.paused = False
            self.qtm.start(1000)
        else:
            self.start()

    def setSlider(self):
        self.slider.setOrientation(1)
        self.slider.setMinimum(0)
        self.slider.setMaximum(self.timeSteps)
        self.slider.setTickInterval(1)
        self.slider.setTickPosition(2)
        self.slider.setVisible(True)

    def testValChange(self):
        val = self.slider.value()
        print("Slider value has changed to " + str(val))
        self.currentStepLabel.setText("Step :" + str(val))
        self.timeStep = val

    def pressedSlider(self):
        self.pauseVis()

    def closeEvent(self, a0):
        self.pauseVis()
        self.parent.updateConnGrads()
        super(MassFlowVisualizer, self).closeEvent(a0)
