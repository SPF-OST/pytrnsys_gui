# pylint: skip-file
# type: ignore

import datetime as _dt
import itertools as _it
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtWidgets as _qtw
import numpy as _np
import pandas as _pd
import trnsysGUI.TVentil as _tv
import trnsysGUI.connection.connectionBase as _cb
import trnsysGUI.connection.doublePipeConnection as _dpc
import trnsysGUI.connection.names as _cnames
import trnsysGUI.connection.singlePipeConnection as _spc
import trnsysGUI.massFlowSolver.names as _mnames
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.warningsAndErrors as _werrors

_MAX_HEADER_LENGTH = 25


class MassFlowVisualizer(_qtw.QDialog):
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

        timeStepIncreaseLabelText = "Increase time-step by ( 30 = 1 Hour ):\n              ( 720 = 1 Day )"
        self._timeStepIncreaseLabel = _qtw.QLabel(timeStepIncreaseLabelText)
        self._timeStepIncrease = 1
        self._timeStepIncreaseLineEdit = _qtw.QLineEdit()
        self._timeStepIncreaseLineEdit.setText(str(self._timeStepIncrease))
        self._timeStepIncreaseLineEdit.editingFinished.connect(
            self._onTimeStepIncreaseLineEditEditingFinished
        )

        self.slider = _qtw.QSlider(parent)
        self.setSlider()
        self.slider.sliderReleased.connect(self.testValChange)
        self.slider.sliderPressed.connect(self.pressedSlider)
        self.slider.valueChanged.connect(self.moveValues)
        self.slider.setTickInterval(24)

        self.qtm = _qtc.QTimer(parent)
        self.lines = None
        self.started = False

        self.paused = True

        nameLabel = _qtw.QLabel("Name:")
        self.currentStepLabel = _qtw.QLabel(
            "Time: " + str(self.convertTime(self.getTime(0)))
        )
        self.le = _qtw.QLineEdit("NONE")

        self.showMassButton = _qtw.QPushButton("Show mass")  # comment out
        self.togglePauseButton = _qtw.QPushButton("Pause/Continue")
        self.cancelButton = _qtw.QPushButton("Cancel")

        minColorLabel = _qtw.QLabel("Min")
        minColorLabel.setStyleSheet("color: blue")
        maxColorLabel = _qtw.QLabel("Max")
        maxColorLabel.setStyleSheet("color: red")
        minToFiftyPercentile = _qtw.QLabel("Min to 50%")
        minToFiftyPercentile.setStyleSheet("color: cyan")
        fiftyPercentileToMax = _qtw.QLabel("50% to max")
        fiftyPercentileToMax.setStyleSheet("color: pink")
        arrowLabel = _qtw.QLabel("-->")
        arrowLabel2 = _qtw.QLabel("-->")
        arrowLabel3 = _qtw.QLabel("-->")

        colorLayout = _qtw.QHBoxLayout()
        colorLayout.addWidget(minColorLabel)
        colorLayout.addWidget(arrowLabel)
        colorLayout.addWidget(minToFiftyPercentile)
        colorLayout.addWidget(arrowLabel2)
        colorLayout.addWidget(fiftyPercentileToMax)
        colorLayout.addWidget(arrowLabel3)
        colorLayout.addWidget(maxColorLabel)
        colorLayout.addStretch()

        buttonLayout = _qtw.QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self._timeStepIncreaseLabel)
        buttonLayout.addWidget(self._timeStepIncreaseLineEdit)
        buttonLayout.addWidget(self.showMassButton)  # comment out
        buttonLayout.addWidget(self.togglePauseButton)
        buttonLayout.addWidget(self.cancelButton)
        layout = _qtw.QGridLayout()
        layout.addWidget(nameLabel, 0, 0)
        layout.addWidget(self.le, 0, 1)
        layout.addLayout(colorLayout, 1, 0, 1, 0)
        layout.addLayout(buttonLayout, 2, 0, 2, 0)
        layout.addWidget(self.currentStepLabel, 3, 0, 1, 2)
        layout.addWidget(
            self.slider, 4, 0, 1, 2
        )  # Only for debug (Why do I need a 3 here instead of a 2 for int:row?)

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
        self.move(parent.editor.diagramView.geometry().topLeft())
        self.show()

    def _onTimeStepIncreaseLineEditEditingFinished(self) -> None:
        try:
            lineEditText = self._timeStepIncreaseLineEdit.text()
            timeStepIncrease = int(lineEditText)
        except ValueError:
            timeStepIncrease = None

        if timeStepIncrease is None or not (
            1 <= timeStepIncrease <= self.maxTimeStep
        ):
            errorMessage = f"The time-step increase must be an integer between 1 and {self.maxTimeStep}, inclusive."
            _werrors.showMessageBox(errorMessage, title="Invalid value")
            self._timeStepIncreaseLineEdit.setText(str(self._timeStepIncrease))
            return

        self._timeStepIncrease = timeStepIncrease

    def togglePause(self):
        if self.paused:
            self.continueVis()
        else:
            self.pauseVis()

    def cancel(self):
        self.pauseVis()
        self.close()
        self.parent.editor.updateConnGrads()

    # comment out
    def showMassBtn(self):
        """
        For showing the mass under the connections
        -------

        """
        self.showMass = not self.showMass

        for t in self.parent.editor.trnsysObj:
            if isinstance(t, _cb.ConnectionBase):
                t.massFlowLabel.setVisible(self.showMass)

        self.logger.debug(
            "%s %s %s"
            % (str(self.minValue), str(self.medianValue), str(self.maxValue))
        )

    def loadFile(self):
        if not self.loadedFile:
            self.massFlowData = _pd.read_csv(
                self.dataFilePath, sep="\t"
            ).rename(columns=lambda x: x.strip())
            _truncateColumnNames(self.massFlowData)
        self.loadedFile = True

    def loadTempFile(self):
        if not self.tempLoadedFile:
            self.tempMassFlowData = _pd.read_csv(
                self.tempDatafilePath, sep="\t"
            ).rename(columns=lambda x: x.strip())
            _truncateColumnNames(self.tempMassFlowData)
        self.tempLoadedFile = True

    def start(self):

        self.paused = False
        self.qtm = _qtc.QTimer(self.parent)
        self.qtm.timeout.connect(self.advance)
        self.qtm.timeout.connect(self.increaseValue)
        self.qtm.start(1000)

    def advance(self):
        if self.timeStep == self.maxTimeStep:
            self.logger.debug("reached end of data, returning")
            self.qtm.stop()

        if not self.loadedFile:
            return

        for t in self.parent.editor.trnsysObj:
            if isinstance(t, _spc.SinglePipeConnection):
                mfrVariableName = _mnames.getCanonicalMassFlowVariableName(
                    componentDisplayName=t.getDisplayName(),
                    pipeName=t.modelPipe.name,
                )
                temperatureVariableName = _cnames.getTemperatureVariableName(
                    t, _mfn.PortItemType.STANDARD
                )

                if not self._haveTruncatedColumns(
                    mfrVariableName, temperatureVariableName
                ):
                    continue

                massFlow = self._getMassFlow(mfrVariableName, self.timeStep)
                temperature = self._getTemperature(
                    temperatureVariableName, self.timeStep
                )

                t.setMassFlowAndTemperature(massFlow, temperature)
                thickValue = self.getThickness(massFlow)
                self.logger.debug("Thickvalue: " + str(thickValue))
                if massFlow == 0:
                    t.setColor(thickValue, mfr="ZeroMfr")
                elif round(abs(temperature)) == self.maxValue:
                    t.setColor(thickValue, mfr="max")
                elif round(abs(temperature)) == self.minValue:
                    t.setColor(thickValue, mfr="min")
                elif (
                    self.minValue
                    < round(abs(temperature))
                    <= self.lowerQuarter
                ):
                    t.setColor(thickValue, mfr="minTo25")
                elif (
                    self.lowerQuarter
                    < round(abs(temperature))
                    <= self.medianValue
                ):
                    t.setColor(thickValue, mfr="25To50")
                elif (
                    self.medianValue
                    < round(abs(temperature))
                    <= self.upperQuarter
                ):
                    t.setColor(thickValue, mfr="50To75")
                elif (
                    self.upperQuarter < round(abs(temperature)) < self.maxValue
                ):
                    t.setColor(thickValue, mfr="75ToMax")
                else:
                    t.setColor(thickValue, mfr="test")

            if isinstance(t, _dpc.DoublePipeConnection):
                coldMassFlowVariableName = (
                    _mnames.getCanonicalMassFlowVariableName(
                        componentDisplayName=t.displayName,
                        pipeName=t.coldModelPipe.name,
                    )
                )
                coldTemperatureVariableName = (
                    _cnames.getTemperatureVariableName(
                        t, _mfn.PortItemType.COLD
                    )
                )

                hotMassFlowVariableName = (
                    _mnames.getCanonicalMassFlowVariableName(
                        componentDisplayName=t.displayName,
                        pipeName=t.hotModelPipe.name,
                    )
                )
                hotTemperatureVariableName = (
                    _cnames.getTemperatureVariableName(
                        t, _mfn.PortItemType.HOT
                    )
                )

                if not self._haveTruncatedColumns(
                    coldMassFlowVariableName, coldTemperatureVariableName
                ) or not self._haveTruncatedColumns(
                    hotMassFlowVariableName, hotTemperatureVariableName
                ):
                    continue

                coldMassFlow = self._getMassFlow(
                    coldMassFlowVariableName, self.timeStep
                )
                coldTemperature = self._getTemperature(
                    coldTemperatureVariableName, self.timeStep
                )

                hotMassFlow = self._getMassFlow(
                    hotMassFlowVariableName, self.timeStep
                )
                hotTemperature = self._getTemperature(
                    hotTemperatureVariableName, self.timeStep
                )

                t.setMassFlowAndTemperature(
                    coldMassFlow,
                    coldTemperature,
                    hotMassFlow,
                    hotTemperature,
                )

            elif isinstance(t, _tv.TVentil):
                valvePositionVariableName = _mnames.getInputVariableName(
                    t, t.modelDiverter
                )
                if not self._haveTruncatedColumn(
                    self.massFlowData, valvePositionVariableName
                ):
                    continue

                valvePosition = str(
                    self.massFlowData[valvePositionVariableName].iloc[
                        self.timeStep
                    ]
                )
                t.setPositionForMassFlowSolver(valvePosition)
                t.posLabel.setPlainText(valvePosition)

    def _getMassFlow(self, mfrVariableName: str, timeStep: int) -> float:
        truncatedMfrVariableName = _truncateName(mfrVariableName)
        mass = self.massFlowData[truncatedMfrVariableName].iloc[timeStep]
        return mass

    def _getTemperature(
        self, temperatureVariableName: str, timeStep: int
    ) -> float:
        truncatedTemperatureVariableName = _truncateName(
            temperatureVariableName
        )
        return self.tempMassFlowData[truncatedTemperatureVariableName].iloc[
            timeStep
        ]

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

        self.timeStep += self._timeStepIncrease
        if self.timeStep > self.maxTimeStep:
            self.timeStep = 0
        self.slider.setValue(self.timeStep)

    def decreaseValue(self):
        """
        For automatic slider movement

        """

        self.timeStep -= self._timeStepIncrease
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
        tempMassFlowDataDup = tempMassFlowDataDup.drop(
            tempMassFlowDataDup.index[0]
        )
        for items in tempMassFlowDataDup.nunique().items():
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

        data = (
            self.massFlowData.values.tolist()
        )  # data frame converted to nested list
        for sublist in data:  # delete the time column from the list
            del sublist[0]
        data = list(
            _it.chain.from_iterable(data)
        )  # nested list combined into one list
        cleanedData = [
            x for x in data if str(x) != "nan"
        ]  # remove nan from list
        cleanedData = [
            round(abs(num)) for num in cleanedData
        ]  # get absolute value and round off
        noDuplicateData = list(dict.fromkeys(cleanedData))

        self.medianValueMfr = _np.percentile(
            noDuplicateData, 50
        )  # median value / 50th percentile
        self.lowerQuarterMfr = _np.percentile(
            noDuplicateData, 25
        )  # 25th percentile
        self.upperQuarterMfr = _np.percentile(
            noDuplicateData, 75
        )  # 75th percentile
        self.minValueMfr = _np.min(
            noDuplicateData
        )  # minimum value excluding 0
        self.maxValueMfr = _np.max(noDuplicateData)  # max value

    def getThickness(self, mass: float) -> int:
        mass = abs(mass)
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

        data = (
            self.tempMassFlowData.values.tolist()
        )  # data frame converted to nested list
        for sublist in data:  # delete the time column from the list
            del sublist[0]
        data = list(
            _it.chain.from_iterable(data)
        )  # nested list combined into one list
        cleanedData = [
            x for x in data if str(x) != "nan"
        ]  # remove nan from list
        cleanedData = [
            round(abs(num)) for num in cleanedData
        ]  # get absolute value and round off
        noDuplicateData = list(dict.fromkeys(cleanedData))

        self.medianValue = _np.percentile(
            noDuplicateData, 50
        )  # median value / 50th percentile
        self.lowerQuarter = _np.percentile(
            noDuplicateData, 25
        )  # 25th percentile
        self.upperQuarter = _np.percentile(
            noDuplicateData, 75
        )  # 75th percentile
        self.minValue = _np.min(noDuplicateData)  # minimum value excluding 0
        self.maxValue = _np.max(noDuplicateData)  # max value

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
        base = _dt.datetime(_dt.MINYEAR, 1, 1)
        result = base + _dt.timedelta(
            seconds=(base.replace(year=base.year + 1) - base).total_seconds()
            * decHour
        )
        return str(result)

    def pressedSlider(self):
        self.pauseVis()

    def closeEvent(self, a0):
        self.pauseVis()
        super().closeEvent(a0)

    def keyPressEvent(self, e):
        if e.key() == _qtc.Qt.Key_Up:
            self.logger.debug("Up is pressed")
            self.increaseValue()
        elif e.key() == _qtc.Qt.Key_Down:
            self.logger.debug("Down is pressed")
            self.decreaseValue()

    def _haveTruncatedColumns(
        self, mfrVariableName: str, temperatureVariableName: str
    ) -> bool:
        haveMassFlowColumn = self._haveTruncatedColumn(
            self.massFlowData, mfrVariableName
        )
        haveTemperatureColumn = self._haveTruncatedColumn(
            self.tempMassFlowData, temperatureVariableName
        )

        haveColumns = haveMassFlowColumn and haveTemperatureColumn

        return haveColumns

    @staticmethod
    def _haveTruncatedColumn(
        dataFrame: _pd.DataFrame, variableName: str
    ) -> bool:
        truncatedName = _truncateName(variableName)
        haveColumn = truncatedName in dataFrame.columns
        return haveColumn


def _truncateColumnNames(df: _pd.DataFrame) -> None:
    _ensureNamesDontCollideAfterTruncating(df.columns)
    df.columns = [_truncateName(n) for n in df.columns]


def _ensureNamesDontCollideAfterTruncating(
    columnNames: _tp.Sequence[str],
) -> None:
    sortedColumnNames = sorted(columnNames)
    groupedNames = [
        list(g) for _, g in _it.groupby(sortedColumnNames, key=_truncateName)
    ]
    collidingNames = _flatten(g for g in groupedNames if len(g) > 1)
    if collidingNames:
        formattedCollidingNames = "\n\t".join(collidingNames)
        errorMessage = (
            f"The following column names collide after truncating them to "
            f"{_MAX_HEADER_LENGTH} characters:\n\t{formattedCollidingNames}"
        )
        raise ValueError(errorMessage)


def _truncateName(name: str):
    return name[:_MAX_HEADER_LENGTH]


def _flatten(iterable: _tp.Iterable[_tp.Iterable[str]]) -> _tp.Sequence[str]:
    return list(_it.chain.from_iterable(iterable))
