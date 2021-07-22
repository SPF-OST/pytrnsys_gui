# pylint: skip-file
# type: ignore

import re
import sys
from datetime import timedelta, datetime, MINYEAR

import numpy
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPainter, QBrush, QColor
from PyQt5.QtWidgets import QSlider, QDialog, QLineEdit, QPushButton, QHBoxLayout, QLabel, QGridLayout, QWidget

from trnsysGUI.Connection import Connection
import pandas as pd
import itertools
import numpy as np


class MassFlowVisualizer(QDialog):
    def __init__(self, parent, mfrFile, tempFile):

        super(MassFlowVisualizer, self).__init__(parent)

        self.logger = parent.logger

        self.dataFilePath = mfrFile
        self.tempDatafilePath = tempFile
        self.loadedFile = False
        self.tempLoadedFile = False
        self.loadFile()
        self.loadTempFile()
        self.maxTimeStep = len(self.massFlowData.index) - 1
        self.showMass = False

        self.setMinimumSize(1000, 200)

        self.parent = parent
        self.timeStep = 0
        self.timeSteps = len(self.massFlowData.index) - 1  # 0 to 364

        # threshold values for positive list
        self.medianValue = 0
        self.lowerQuarter = 0
        self.upperQuarter = 0
        self.minValue = 0
        self.maxValue = 0

        self.medianValueMfr = 0
        self.lowerQuarterMfr = 0
        self.upperQuarterMfr = 0
        self.minValueMfr = 0
        self.maxValueMfr = 0

        self.getThresholdValues()
        self.getTempThresholdValues()

        self.jumpValue = QLabel("Jump by ( 30 = 1 Hour ):\n              ( 720 = 1 Day )")
        self.jumpValueLE = QLineEdit("1")

        self.slider = QSlider(parent)
        self.setSlider()
        self.slider.sliderReleased.connect(self.testValChange)
        self.slider.sliderPressed.connect(self.pressedSlider)
        self.slider.valueChanged.connect(self.moveValues)
        self.slider.setTickInterval(24)

        self.qtm = QTimer(parent)
        self.lines = None
        self.started = False

        self.paused = True

        nameLabel = QLabel("Name:")
        self.currentStepLabel = QLabel("Time: " + str(self.convertTime(self.getTime(0))))
        self.le = QLineEdit("NONE")

        self.showMassButton = QPushButton("Show mass")  # comment out
        self.togglePauseButton = QPushButton("Pause/Continue")
        self.cancelButton = QPushButton("Cancel")

        minColorLabel = QLabel("Min")
        minColorLabel.setStyleSheet("color: blue")
        maxColorLabel = QLabel("Max")
        maxColorLabel.setStyleSheet("color: red")
        minToFiftyPercentile = QLabel("Min to 50%")
        minToFiftyPercentile.setStyleSheet("color: cyan")
        fiftyPercentileToMax = QLabel("50% to max")
        fiftyPercentileToMax.setStyleSheet("color: pink")
        arrowLabel = QLabel("-->")
        arrowLabel2 = QLabel("-->")
        arrowLabel3 = QLabel("-->")

        colorLayout = QHBoxLayout()
        colorLayout.addWidget(minColorLabel)
        colorLayout.addWidget(arrowLabel)
        colorLayout.addWidget(minToFiftyPercentile)
        colorLayout.addWidget(arrowLabel2)
        colorLayout.addWidget(fiftyPercentileToMax)
        colorLayout.addWidget(arrowLabel3)
        colorLayout.addWidget(maxColorLabel)
        colorLayout.addStretch()

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.jumpValue)
        buttonLayout.addWidget(self.jumpValueLE)
        buttonLayout.addWidget(self.showMassButton)  # comment out
        buttonLayout.addWidget(self.togglePauseButton)
        buttonLayout.addWidget(self.cancelButton)
        layout = QGridLayout()
        layout.addWidget(nameLabel, 0, 0)
        layout.addWidget(self.le, 0, 1)
        layout.addLayout(colorLayout, 1, 0, 1, 0)
        layout.addLayout(buttonLayout, 2, 0, 2, 0)
        layout.addWidget(self.currentStepLabel, 3, 0, 1, 2)
        layout.addWidget(self.slider, 4, 0, 1, 2)  # Only for debug (Why do I need a 3 here instead of a 2 for int:row?)

        self.setLayout(layout)

        self.showMassButton.clicked.connect(self.showMassBtn)  # comment out
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
        self.parent.centralWidget.updateConnGrads()

    # comment out
    def showMassBtn(self):
        """
        For showing the mass under the connections
        -------

        """
        self.showMass = not self.showMass

        for t in self.parent.centralWidget.trnsysObj:
            if isinstance(t, Connection):
                if self.showMass:
                    t.firstS.labelMass.setVisible(True)
                else:
                    t.firstS.labelMass.setVisible(False)

        self.logger.debug("%s %s %s" % (str(self.minValue), str(self.medianValue), str(self.maxValue)))

    def loadFile(self):
        if not self.loadedFile:
            self.massFlowData = pd.read_csv(self.dataFilePath, sep="\t").rename(columns=lambda x: x.strip())
        self.loadedFile = True

    def loadTempFile(self):
        if not self.tempLoadedFile:
            self.tempMassFlowData = pd.read_csv(self.tempDatafilePath, sep="\t").rename(columns=lambda x: x.strip())
        self.tempLoadedFile = True

    def start(self):

        self.paused = False
        self.qtm = QTimer(self.parent)
        self.qtm.timeout.connect(self.advance)
        self.qtm.timeout.connect(self.increaseValue)
        self.qtm.start(1000)

    def advance(self):
        if self.timeStep == self.maxTimeStep:
            self.logger.debug("reached end of data, returning")
            self.qtm.stop()
            return

        if self.loadedFile:
            i = 0
            for t in self.parent.centralWidget.trnsysObj:
                if isinstance(t, Connection):
                    if (
                        "Mfr" + t.displayName in self.massFlowData.columns
                        and "T" + t.displayName in self.tempMassFlowData
                    ):
                        mass = str(round(self.massFlowData["Mfr" + t.displayName].iloc[self.timeStep]))
                        mass1Dp = str(round(self.massFlowData["Mfr" + t.displayName].iloc[self.timeStep], 1))
                        temperature = str(round(self.tempMassFlowData["T" + t.displayName].iloc[self.timeStep]))
                        self.logger.debug("Found connection in ts " + str(self.timeStep) + " " + str(i))
                        self.logger.debug("mass flow value of %s : " % t.displayName)
                        t.setMassAndTemperature(mass1Dp, temperature)
                        thickValue = self.getThickness(mass)
                        self.logger.debug("Thickvalue: " + str(thickValue))
                        if self.massFlowData["Mfr" + t.displayName].iloc[self.timeStep] == 0:
                            t.setColor(thickValue, mfr="ZeroMfr")
                        elif round(abs(self.tempMassFlowData["T" + t.displayName].iloc[self.timeStep])) == self.maxValue:
                            t.setColor(thickValue, mfr="max")
                        elif round(abs(self.tempMassFlowData["T" + t.displayName].iloc[self.timeStep])) == self.minValue:
                            t.setColor(thickValue, mfr="min")
                        elif (
                            self.minValue
                            < round(abs(self.tempMassFlowData["T" + t.displayName].iloc[self.timeStep]))
                            <= self.lowerQuarter
                        ):
                            t.setColor(thickValue, mfr="minTo25")
                        elif (
                            self.lowerQuarter
                            < round(abs(self.tempMassFlowData["T" + t.displayName].iloc[self.timeStep]))
                            <= self.medianValue
                        ):
                            t.setColor(thickValue, mfr="25To50")
                        elif (
                            self.medianValue
                            < round(abs(self.tempMassFlowData["T" + t.displayName].iloc[self.timeStep]))
                            <= self.upperQuarter
                        ):
                            t.setColor(thickValue, mfr="50To75")
                        elif (
                            self.upperQuarter
                            < round(abs(self.tempMassFlowData["T" + t.displayName].iloc[self.timeStep]))
                            < self.maxValue
                        ):
                            t.setColor(thickValue, mfr="75ToMax")
                        else:
                            t.setColor(thickValue, mfr="test")
                        i += 1
                else:
                    if "xFrac" + t.displayName in self.massFlowData.columns:
                        valvePosition = str(self.massFlowData["xFrac" + t.displayName].iloc[self.timeStep])
                        t.setPositionForMassFlowSolver(valvePosition)
                        t.posLabel.setPlainText(valvePosition)
                        self.logger.debug("valve position: " + str(valvePosition))

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
        if self.checkTimeStep and self.checkTempTimeStep():
            self.slider.setVisible(True)
            self.slider.setEnabled(False)
            self.increaseValue()
        else:
            self.slider.setVisible(True)
            self.slider.setEnabled(True)

    def testValChange(self):
        """
        Updates mass flow visualizer after releasing the mouse
        """
        val = self.slider.value()
        self.logger.debug("Slider value has changed to " + str(val))
        time = self.getTime(val)
        self.currentStepLabel.setText("Time :" + str(self.convertTime(time)))
        self.timeStep = val
        self.advance()

    def moveValues(self):
        """
        Updates mass flow visualizer when moving the mouse
        """
        val = self.slider.value()
        self.logger.debug("Slider value is still: " + str(val))
        time = self.getTime(val)
        self.currentStepLabel.setText("Time :" + str(self.convertTime(time)))
        self.timeStep = val
        self.advance()

    def increaseValue(self):
        """
        For automatic slider movement

        """

        self.timeStep += float(self.jumpValueLE.text())
        if self.timeStep > self.maxTimeStep:
            self.timeStep = 0
        self.slider.setValue(self.timeStep)

    def decreaseValue(self):
        """
        For automatic slider movement

        """

        self.timeStep -= float(self.jumpValueLE.text())
        if self.timeStep < 0:
            self.timeStep = self.maxTimeStep
        self.slider.setValue(self.timeStep)

    def checkTimeStep(self):
        """
        Check individual columns of the data frame, If a column has rows with different values, return False.
        Else, continue to next column. Return True if no such column can be found.

        False indicates the rows are not identical and slider should be enabled
        True indicates the rows are identical and slider should be disabled

        """
        massFlowDataDup = self.massFlowData
        massFlowDataDup = massFlowDataDup.drop(massFlowDataDup.index[0])
        for items in round(abs(massFlowDataDup)).nunique().iteritems():
            if items[0] != "TIME":
                if items[1] > 1:
                    return False
        return True

    def checkTempTimeStep(self):
        tempMassFlowDataDup = self.tempMassFlowData
        tempMassFlowDataDup = tempMassFlowDataDup.drop(tempMassFlowDataDup.index[0])
        for items in tempMassFlowDataDup.nunique().iteritems():
            if items[0] != "TIME":
                if items[1] > 1:
                    return False
        return True

    def getThresholdValues(self):
        """
        Access the data frame, convert into a nested list.
        Merge the nested list into one single list.
        Remove 'nan' from the list.
        Convert the values inside the list into absolute values then round them off.
        Split the list into two for negative and positive values.
        Get the minimum value, the 25th percentile, the median value, the 75th percentile and
        the max value from the lists.
        Returns
        -------
        """

        data = self.massFlowData.values.tolist()  # data frame converted to nested list
        for sublist in data:  # delete the time column from the list
            del sublist[0]
        data = list(itertools.chain.from_iterable(data))  # nested list combined into one list
        cleanedData = [x for x in data if str(x) != "nan"]  # remove nan from list
        cleanedData = [round(abs(num)) for num in cleanedData]  # get absolute value and round off
        nonZeroData = [x for x in cleanedData if x > 1]  # a work around to remove the 1 values from the data frame
        noDuplicateData = list(dict.fromkeys(nonZeroData))

        self.medianValueMfr = np.percentile(noDuplicateData, 50)  # median value / 50th percentile
        self.lowerQuarterMfr = np.percentile(noDuplicateData, 25)  # 25th percentile
        self.upperQuarterMfr = np.percentile(noDuplicateData, 75)  # 75th percentile
        self.minValueMfr = np.min(noDuplicateData)  # minimum value excluding 0
        self.maxValueMfr = np.max(noDuplicateData)  # max value

    def getThickness(self, mass):
        mass = abs(float(mass))
        if mass == self.minValueMfr:
            return 2
        elif self.minValueMfr < mass <= self.medianValueMfr:
            return 4
        elif self.medianValueMfr < mass < self.maxValueMfr:
            return 6
        elif mass == self.maxValueMfr:
            return 8
        else:
            return 2

    def getTempThresholdValues(self):
        """
        Access the data frame, convert into a nested list.
        Merge the nested list into one single list.
        Remove 'nan' from the list.
        Convert the values inside the list into absolute values then round them off.
        Split the list into two for negative and positive values.
        Get the minimum value, the 25th percentile, the median value, the 75th percentile and
        the max value from the lists.
        Returns
        -------
        """

        data = self.tempMassFlowData.values.tolist()  # data frame converted to nested list
        for sublist in data:  # delete the time column from the list
            del sublist[0]
        data = list(itertools.chain.from_iterable(data))  # nested list combined into one list
        cleanedData = [x for x in data if str(x) != "nan"]  # remove nan from list
        cleanedData = [round(abs(num)) for num in cleanedData]  # get absolute value and round off
        noDuplicateData = list(dict.fromkeys(cleanedData))

        self.medianValue = np.percentile(noDuplicateData, 50)  # median value / 50th percentile
        self.lowerQuarter = np.percentile(noDuplicateData, 25)  # 25th percentile
        self.upperQuarter = np.percentile(noDuplicateData, 75)  # 75th percentile
        self.minValue = np.min(noDuplicateData)  # minimum value excluding 0
        self.maxValue = np.max(noDuplicateData)  # max value

        # print(noDuplicateData)
        # sys.exit()

    def getTime(self, row):
        """
        Gets the time of the current time step
        """
        data = self.massFlowData
        timeColumn = data[data.columns[0]]
        self.logger.debug(str(timeColumn[row]))
        return timeColumn[row]

    def convertTime(self, time):
        """
        Convert the time into YYYY--MM--DD HH:MM:SS format
        """
        noOfHours = 8760
        decHour = float(time) / float(noOfHours)
        base = datetime(MINYEAR, 1, 1)
        result = base + timedelta(seconds=(base.replace(year=base.year + 1) - base).total_seconds() * decHour)
        return str(result)

    def pressedSlider(self):
        self.pauseVis()

    def closeEvent(self, a0):
        for t in self.parent.centralWidget.trnsysObj:
            if isinstance(t, Connection):
                t.firstS.labelMass.setVisible(False)

        self.pauseVis()
        self.parent.centralWidget.updateConnGrads()
        self.parent.massFlowEnabled = False

        super(MassFlowVisualizer, self).closeEvent(a0)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Up:
            self.logger.debug("Up is pressed")
            self.increaseValue()
        elif e.key() == Qt.Key_Down:
            self.logger.debug("Down is pressed")
            self.decreaseValue()
