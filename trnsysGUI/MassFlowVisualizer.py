import re
import sys

import numpy
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QSlider, QDialog, QLineEdit, QPushButton, QHBoxLayout, QLabel, QGridLayout

from trnsysGUI.Connection import Connection
import pandas as pd
import itertools
import numpy as np

class MassFlowVisualizer(QDialog):

    def __init__(self, parent,mfrFile):

        super(MassFlowVisualizer, self).__init__(parent)
        self.dataFilePath = mfrFile
        self.loadedFile = False
        self.loadFile()
        self.maxTimeStep = 5 # todo change this to the number of rows in the file
        self.showMass = False

        self.setMinimumSize(1000, 200)

        self.parent = parent
        self.timeStep = 0
        self.timeSteps = len(self.massFlowData.index)  - 1    # 0 to 364

        # threshold values for positive list
        self.medianValue = 0
        self.lowerQuarter = 0
        self.upperQuarter = 0
        self.minValue = 0
        self.maxValue = 0

        self.getThresholdValues()

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
        self.currentStepLabel = QLabel("Time: " + str(self.slider.value()))
        self.le = QLineEdit("NONE")

        self.showMassButton = QPushButton("Show mass")  # comment out
        self.togglePauseButton = QPushButton("Pause/Continue")
        self.cancelButton = QPushButton("Cancel")

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.showMassButton)  # comment out
        buttonLayout.addWidget(self.togglePauseButton)
        buttonLayout.addWidget(self.cancelButton)
        layout = QGridLayout()
        layout.addWidget(nameLabel, 0, 0)
        layout.addWidget(self.le, 0, 1)
        layout.addLayout(buttonLayout, 1, 0, 2, 0)
        layout.addWidget(self.currentStepLabel, 2, 0, 1, 2)
        layout.addWidget(self.slider, 3, 0, 1, 2)  # Only for debug (Why do I need a 3 here instead of a 2 for int:row?)

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
        self.parent.updateConnGrads()

    # comment out
    def showMassBtn(self):
        """
        For showing the mass under the connections
        -------

        """
        self.showMass = not self.showMass

        for t in self.parent.centralWidget.trnsysObj:
            if isinstance(t, Connection):
                if not self.showMass:
                    t.firstS.labelMass.setVisible(True)
                else:
                    t.firstS.labelMass.setVisible(False)



    def loadFile(self):
        if not self.loadedFile:
            self.massFlowData = pd.read_csv(self.dataFilePath, sep='\t').rename(
                columns=lambda x: x.strip())
        self.loadedFile = True


    def start(self):

        self.paused = False
        self.qtm = QTimer(self.parent)
        self.qtm.timeout.connect(self.advance)
        # self.qtm.timeout.connect(self.increaseValue)
        self.qtm.start(1000)

    def advance(self):
        if self.timeStep == 364:
            print("reached end of data, returning")
            self.qtm.stop()
            return

        if self.loadedFile:

            i = 0
            # for t in self.parent.centralWidget.trnsysObj:
            #     if isinstance(t, Connection):
            #         if 'Mfr'+t.displayName in self.massFlowData.columns:
            #             print("Found connection in ts " + str(self.timeStep) + " " + str(i))
            #             if self.massFlowData['Mfr'+t.displayName].iloc[self.timeStep] < 0:
            #                 t.setColor(mfr="NegMfr")
            #             elif self.massFlowData['Mfr'+t.displayName].iloc[self.timeStep] == 0:
            #                 t.setColor(mfr="ZeroMfr")
            #             else:
            #                 t.setColor(mfr="PosMfr")
            #             i += 1

            # for t in self.parent.centralWidget.trnsysObj:
            #     if isinstance(t, Connection):
            #         if 'Mfr'+t.displayName in self.massFlowData.columns:
            #             print("Found connection in ts " + str(self.timeStep) + " " + str(i))
            #             if self.massFlowData['Mfr' + t.displayName].iloc[self.timeStep] == 0:
            #                 t.setColor(mfr="ZeroMfr")
            #             elif self.minValue <= abs(self.massFlowData['Mfr'+t.displayName].iloc[self.timeStep]) < self.lowerQuarter:
            #                 t.setColor(mfr="minToLower")
            #                 t.setMass(str(round(self.massFlowData['Mfr' + t.displayName].iloc[self.timeStep])))
            #             elif self.lowerQuarter <= abs(self.massFlowData['Mfr'+t.displayName].iloc[self.timeStep]) < self.medianValue:
            #                 t.setColor(mfr="lowerToMedian")
            #                 t.setMass(str(round(self.massFlowData['Mfr' + t.displayName].iloc[self.timeStep])))
            #             elif self.medianValue <= abs(self.massFlowData['Mfr'+t.displayName].iloc[self.timeStep]) < self.upperQuarter:
            #                 t.setColor(mfr="medianToUpper")
            #                 t.setMass(str(round(self.massFlowData['Mfr' + t.displayName].iloc[self.timeStep])))
            #             else:
            #                 t.setColor(mfr="upperToMax")
            #                 t.setMass(str(round(self.massFlowData['Mfr' + t.displayName].iloc[self.timeStep])))
            #             i += 1

            for t in self.parent.centralWidget.trnsysObj:
                if isinstance(t, Connection):
                    if 'Mfr'+t.displayName in self.massFlowData.columns:
                        print("Found connection in ts " + str(self.timeStep) + " " + str(i))
                        print("mass flow value of %s : " % t.displayName)
                        print((abs(self.massFlowData['Mfr'+t.displayName].iloc[self.timeStep])))
                        if self.massFlowData['Mfr' + t.displayName].iloc[self.timeStep] == 0:
                            t.setColor(mfr="ZeroMfr")
                        elif round(abs(self.massFlowData['Mfr'+t.displayName].iloc[self.timeStep])) == self.maxValue:
                            t.setColor(mfr="max")
                            t.setMass(str(round(self.massFlowData['Mfr' + t.displayName].iloc[self.timeStep])))
                        elif round(abs(self.massFlowData['Mfr'+t.displayName].iloc[self.timeStep])) == self.minValue:
                            t.setColor(mfr="min")
                            t.setMass(str(round(self.massFlowData['Mfr' + t.displayName].iloc[self.timeStep])))
                        elif self.minValue < round(abs(self.massFlowData['Mfr'+t.displayName].iloc[self.timeStep])) <= self.medianValue:
                            t.setColor(mfr="minToMedian")
                            t.setMass(str(round(self.massFlowData['Mfr' + t.displayName].iloc[self.timeStep])))
                        elif self.medianValue < round(abs(self.massFlowData['Mfr'+t.displayName].iloc[self.timeStep])) < self.maxValue:
                            t.setColor(mfr="medianToMax")
                            t.setMass(str(round(self.massFlowData['Mfr' + t.displayName].iloc[self.timeStep])))
                        else:
                            # TODO  need include colour for values between min and max
                            t.setColor(mfr="test")
                            t.setMass(str(round(self.massFlowData['Mfr' + t.displayName].iloc[self.timeStep])))
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
        self.advance()

    def moveValues(self):

        val = self.slider.value()
        print("Slider value is still: " + str(val))
        self.currentStepLabel.setText("Step :" + str(val))
        self.timeStep = val

    def increaseValue(self):
        """
        For automatic slider movement

        """

        self.timeStep += 1
        self.slider.setValue(self.timeStep)
        if self.timeStep > self.maxTimeStep:
            self.timeStep = 0


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
            if items[0] != 'TIME':
                if items[1] > 1:
                    return False
        self.increaseValue()
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
        # TODO : maybe dun include the non-connection columns into the list,  delete those columns before hand
        #  need to know which columns are not connections

        data = self.massFlowData.values.tolist()    # data frame converted to nested list
        for sublist in data:  # delete the time column from the list
            del sublist[0]
        data = list(itertools.chain.from_iterable(data))  # nested list combined into one list
        cleanedData = [x for x in data if str(x) != 'nan']  # remove nan from list
        cleanedData = [round(abs(num)) for num in cleanedData]  # get absolute value and round off
        nonZeroData = [x for x in cleanedData if x > 1]  # a work around to remove the 1 values from the data frame
        noDuplicateData = list(dict.fromkeys(nonZeroData))

        self.medianValue = np.percentile(noDuplicateData, 50)  # median value / 50th percentile
        self.lowerQuarter = np.percentile(noDuplicateData, 25)  # 25th percentile
        self.upperQuarter = np.percentile(noDuplicateData, 75)   # 75th percentile
        self.minValue = np.min(noDuplicateData)  # minimum value excluding 0
        self.maxValue = np.max(noDuplicateData)  # max value






    def pressedSlider(self):
        self.pauseVis()

    def closeEvent(self, a0):
        self.pauseVis()
        self.parent.centralWidget.updateConnGrads()
        super(MassFlowVisualizer, self).closeEvent(a0)
