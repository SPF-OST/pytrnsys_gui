import re
import sys

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QSlider, QDialog, QLineEdit, QPushButton, QHBoxLayout, QLabel, QGridLayout

from trnsysGUI.Connection import Connection
import pandas as pd


class MassFlowVisualizer(QDialog):

    def __init__(self, parent,mfrFile):

        super(MassFlowVisualizer, self).__init__(parent)
        self.dataFilePath = mfrFile
        self.loadedFile = False
        # self.identicalAtallTimeSteps = True
        self.loadFile()

        self.setMinimumSize(1000, 200)

        self.parent = parent
        self.timeStep = 0
        self.timeSteps = len(self.massFlowData.index)    # 0 to 364


        self.slider = QSlider(parent)
        self.setSlider()
        self.slider.sliderReleased.connect(self.testValChange)
        self.slider.sliderPressed.connect(self.pressedSlider)
        self.slider.sliderMoved.connect(self.moveValues)
        self.slider.setTickInterval(24)


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

        self.advance()

        self.setWindowTitle("Flow visualizer")
        ph = parent.geometry().height()
        pw = parent.geometry().width()
        px = parent.geometry().x()
        py = parent.geometry().y()
        dw = self.width()
        dh = self.height()
        self.move(parent.centralWidget.diagramView.geometry().topLeft())
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
            self.massFlowData = pd.read_csv(self.dataFilePath, sep='\t').rename(
                columns=lambda x: x.strip())
        self.loadedFile = True


    def start(self):

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

            i = 0
            for t in self.parent.centralWidget.trnsysObj:
                if isinstance(t, Connection):
                    if 'Mfr'+t.displayName in self.massFlowData.columns:
                        print("Found connection in ts " + str(self.timeStep) + " " + str(i))
                        if self.massFlowData['Mfr'+t.displayName].iloc[self.timeStep] < 0:
                            t.setColor(mfr="NegMfr")
                        elif self.massFlowData['Mfr'+t.displayName].iloc[self.timeStep] == 0:
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
        if self.checkTimeStep():
            self.slider.setVisible(True)
            self.slider.setEnabled(False)
        else:
            self.slider.setVisible(True)
            self.slider.setEnabled(True)

    def testValChange(self):
        val = self.slider.value()
        print("Slider value has changed to " + str(val))
        self.currentStepLabel.setText("Step :" + str(val))
        self.timeStep = val

    def moveValues(self):
        val = self.slider.value()
        self.currentStepLabel.setText("Step :" + str(val))
        self.timeStep = val
        self.advance()

    def checkTimeStep(self):
        """
        Check individual columns, if every row in every column is identical. Return False
        Else, return True

        """
        for items in self.massFlowData.nunique().iteritems():
            if items[0] != 'TIME':
                if items[1] > 1:
                    return False
        return True

    def pressedSlider(self):
        self.pauseVis()

    def closeEvent(self, a0):
        self.pauseVis()
        self.parent.centralWidget.updateConnGrads()
        super(MassFlowVisualizer, self).closeEvent(a0)
