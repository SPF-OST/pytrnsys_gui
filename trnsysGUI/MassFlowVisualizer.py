import datetime as _dt
import itertools as _it
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw
import numpy as _np
import pandas as _pd
import pandas as pd
import pytrnsys.utils.result as _res

import trnsysGUI.TVentil as _tv
import trnsysGUI.connection.names as _cnames
import trnsysGUI.connection.singlePipeConnection as _spc
import trnsysGUI.massFlowSolver.names as _mnames
import trnsysGUI.massFlowSolver.networkModel as _mfn

Quantiles = _tp.Tuple[float, float, float, float]


_TCo = _tp.TypeVar("_TCo", covariant=True)


def _getGlobalQuantiles(df: _pd.DataFrame) -> Quantiles:
    values = df.to_numpy().reshape(-1)
    numericValues = values[~_pd.isna(values)]
    quantiles = _np.quantile(numericValues, q=(0, 0.25, 0.5, 0.75, 1))
    return tuple(quantiles)


def _getMapping(quantiles: Quantiles, values: _tp.Tuple[_TCo, _TCo, _TCo, _TCo, _TCo, _TCo]) -> pd.Series:
    lowerBounds = [-_np.inf, *quantiles]
    upperBounds = [*quantiles, +_np.inf]
    intervalIndex = _pd.IntervalIndex.from_arrays(lowerBounds, upperBounds)
    return pd.Series(data=values, index=intervalIndex)


class MassFlowVisualizer(_qtw.QDialog):
    @classmethod
    def createAndShow(cls, parent, mfrFile, tempFile) -> _res.Result[None]:
        massFlowData = _pd.read_csv(mfrFile, sep="\t").rename(columns=lambda x: x.strip())
        temperatureData = _pd.read_csv(tempFile, sep="\t").rename(columns=lambda x: x.strip())

        trnsysObjects = parent.centralWidget.trnsysObj
        connections = [o for o in trnsysObjects if isinstance(o, _spc.SinglePipeConnection)]
        valves = [o for o in trnsysObjects if isinstance(o, _tv.TVentil)]

        result = cls._getDataAndMassFlowAndTemperatureQuantiles(connections, valves, massFlowData, temperatureData, mfrFile, tempFile)
        if _res.isError(result):
            return _res.error(result)
        data, massFlowQuantiles, temperatureQuantiles = _res.value(result)

        visualizer = MassFlowVisualizer(parent, data, massFlowQuantiles, temperatureQuantiles)
        visualizer.show()

        return None

    @staticmethod
    def _getDataAndMassFlowAndTemperatureQuantiles(
        connections: _tp.Sequence[_spc.SinglePipeConnection],
        valves: _tp.Sequence[_tv.TVentil],
        massFlowData: _pd.DataFrame,
        temperatureData: _pd.DataFrame,
        mfrFile: str,
        tempFile: str,
    ) -> _res.Result[_tp.Tuple[_pd.DataFrame, Quantiles, Quantiles]]:
        errorMessages = []

        connectionMfrNames = {_mnames.getCanonicalMassFlowVariableName(c, c.modelPipe) for c in connections}
        foundConnectionMfrNames = connectionMfrNames & massFlowData.columns
        if not foundConnectionMfrNames:
            errorMessage = f"""\
Could not find any mass flow rates for single pipes in {mfrFile}.
Please check whether the column names in {mfrFile} corresponding to
to pipe mass flow rates match the format M<pipe name>. If they don't
match, change the name and try loading
the file again."""
            errorMessages.append(errorMessage)

        connectionTemperatureNames = {
            _cnames.getTemperatureVariableName(c, _mfn.PortItemType.STANDARD) for c in connections
        }
        foundConnectionTemperatureNames = connectionTemperatureNames & temperatureData.columns
        if not foundConnectionTemperatureNames:
            errorMessage = f"""\
Could not find any temperatures for single pipes in {tempFile}.
Please check whether the column names in {tempFile} corresponding
to connection temperatures match the format T<pipe name>. If they
don't match, change the name and try loading the file again."""
            errorMessages.append(errorMessage)

        valvePositionNames = {_mnames.getInputVariableName(v, v.modelDiverter) for v in valves}
        foundValvePositionNames = valvePositionNames & massFlowData.columns
        if not foundValvePositionNames:
            errorMessage = f"""\
Could not find any valve positions in {mfrFile}.
Please check whether the column names in {mfrFile} corresponding to
valve positions match the format xFrac<valve name>. If they don't match,
change the name and try loading the file again."""
            errorMessages.append(errorMessage)

        if errorMessages:
            jointErrorMessage = "\n\n".join(errorMessages)
            return _res.Error(jointErrorMessage)

        if not (massFlowData.index == temperatureData.index).all():
            return _res.Error(
                f"Temperature data in {tempFile} and mass flow data in {mfrFile} seem to have different steps. Aborting."
            )

        relevantMasFlowDataColumns = foundConnectionMfrNames | foundValvePositionNames
        relevantTemperatureDataColumns = foundConnectionTemperatureNames
        data = _pd.concat(
            [massFlowData[relevantMasFlowDataColumns], temperatureData[relevantTemperatureDataColumns]], axis="columns"
        )

        massFlowQuantiles = _getGlobalQuantiles(data[connectionMfrNames])
        temperatureQuantiles = _getGlobalQuantiles(data[connectionTemperatureNames].abs())

        return data, massFlowQuantiles, temperatureQuantiles

    def __init__(
        self, parent, data: _pd.DataFrame, massFlowQuantiles: Quantiles, temperatureQuantiles: Quantiles
    ) -> None:
        super().__init__(parent)
        self.parent = parent
        self.logger = parent.logger

        self._data = data
        self._massFlowToWidthMapping = _getMapping(massFlowQuantiles, (2, 4, 4, 6, 6, 8))

        colors = (
            _qtg.QColor(0, 0, 204),  # deep blue
            _qtg.QColor(0, 128, 255),  # blue
            _qtg.QColor(102, 255, 255),  # light blue
            _qtg.QColor(255, 153, 153),  # light red
            _qtg.QColor(255, 51, 51),  # red
            _qtg.QColor(153, 0, 0),  # deep red
        )
        self._temperatureToColorMapping = _getMapping(temperatureQuantiles, colors)

        self.maxTimeStep = data.shape[1]
        self.showMass = False

        self.setMinimumSize(1000, 200)

        self.timeStep = 0
        self.timeSteps = data.shape[1]

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

        self.jumpValue = _qtw.QLabel("Jump by ( 30 = 1 Hour ):\n              ( 720 = 1 Day )")
        self.jumpValueLE = _qtw.QLineEdit("1")

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
        self.currentStepLabel = _qtw.QLabel("Time: " + str(self.convertTime(self.getTime(0))))
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
        buttonLayout.addWidget(self.jumpValue)
        buttonLayout.addWidget(self.jumpValueLE)
        buttonLayout.addWidget(self.showMassButton)  # comment out
        buttonLayout.addWidget(self.togglePauseButton)
        buttonLayout.addWidget(self.cancelButton)
        layout = _qtw.QGridLayout()
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
        self.move(parent.centralWidget.diagramView.geometry().topLeft())

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
            if isinstance(t, _spc.SinglePipeConnection):
                if self.showMass:
                    t.firstS.labelMass.setVisible(True)
                else:
                    t.firstS.labelMass.setVisible(False)

        self.logger.debug("%s %s %s" % (str(self.minValue), str(self.medianValue), str(self.maxValue)))

    def start(self):

        self.paused = False
        self.qtm = _qtc.QTimer(self.parent)
        self.qtm.timeout.connect(self.advance)
        self.qtm.timeout.connect(self.increaseValue)
        self.qtm.start(1000)

    def advance(self):
        timeStep = int(self.timeStep)

        if timeStep == self.maxTimeStep:
            self.logger.debug("reached end of data, returning")
            self.qtm.stop()

        trnsysObjects = self.parent.centralWidget.trnsysObj

        connections = [o for o in trnsysObjects if isinstance(o, _spc.SinglePipeConnection)]
        for connection in connections:
            mfrVariableName = _mnames.getCanonicalMassFlowVariableName(connection, connection.modelPipe)
            temperatureVariableName = _cnames.getTemperatureVariableName(connection, _mfn.PortItemType.STANDARD)

            if mfrVariableName in self._data and temperatureVariableName in self._data:
                mass = self._data[mfrVariableName].iloc[timeStep]
                temperature = self._data[temperatureVariableName].iloc[timeStep]

                connection.setMassAndTemperature(mass, temperature)

                width = self._massFlowToWidthMapping[mass]
                color = self._temperatureToColorMapping[temperature]

                connection.setColorAndWidthAccordingToMassflow(color, width)

            valves = [o for o in trnsysObjects if isinstance(o, _tv.TVentil)]
            for valve in valves:
                valvePositionVariableName = _mnames.getInputVariableName(valve, valve.modelDiverter)
                if valvePositionVariableName in self._data:
                    valvePosition = str(self._data[valvePositionVariableName].iloc[timeStep])
                    valve.setPositionForMassFlowSolver(valvePosition)
                    valve.posLabel.setPlainText(valvePosition)
                    self.logger.debug("valve position: " + str(valvePosition))

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
        self.slider.setEnabled(False)
        self.increaseValue()

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

        data = self._data.values.tolist()  # data frame converted to nested list
        for sublist in data:  # delete the time column from the list
            del sublist[0]
        data = list(_it.chain.from_iterable(data))  # nested list combined into one list
        cleanedData = [x for x in data if str(x) != "nan"]  # remove nan from list
        cleanedData = [round(abs(num)) for num in cleanedData]  # get absolute value and round off
        nonZeroData = [x for x in cleanedData if x > 1]  # a work around to remove the 1 values from the data frame
        noDuplicateData = list(dict.fromkeys(nonZeroData))

        self.medianValueMfr = _np.percentile(noDuplicateData, 50)  # median value / 50th percentile
        self.lowerQuarterMfr = _np.percentile(noDuplicateData, 25)  # 25th percentile
        self.upperQuarterMfr = _np.percentile(noDuplicateData, 75)  # 75th percentile
        self.minValueMfr = _np.min(noDuplicateData)  # minimum value excluding 0
        self.maxValueMfr = _np.max(noDuplicateData)  # max value

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

        data = self._data.values.tolist()  # data frame converted to nested list
        for sublist in data:  # delete the time column from the list
            del sublist[0]
        data = list(_it.chain.from_iterable(data))  # nested list combined into one list
        cleanedData = [x for x in data if str(x) != "nan"]  # remove nan from list
        cleanedData = [round(abs(num)) for num in cleanedData]  # get absolute value and round off
        noDuplicateData = list(dict.fromkeys(cleanedData))

        self.medianValue = _np.percentile(noDuplicateData, 50)  # median value / 50th percentile
        self.lowerQuarter = _np.percentile(noDuplicateData, 25)  # 25th percentile
        self.upperQuarter = _np.percentile(noDuplicateData, 75)  # 75th percentile
        self.minValue = _np.min(noDuplicateData)  # minimum value excluding 0
        self.maxValue = _np.max(noDuplicateData)  # max value

        # print(noDuplicateData)
        # sys.exit()

    def getTime(self, row):
        """
        Gets the time of the current time step
        """
        return self._data.index[row]

    @staticmethod
    def convertTime(time):
        """
        Convert the time into YYYY--MM--DD HH:MM:SS format
        """
        noOfHours = 8760
        decHour = float(time) / float(noOfHours)
        base = _dt.datetime(_dt.MINYEAR, 1, 1)
        result = base + _dt.timedelta(seconds=(base.replace(year=base.year + 1) - base).total_seconds() * decHour)
        return str(result)

    def pressedSlider(self):
        self.pauseVis()

    def closeEvent(self, a0):
        for t in self.parent.centralWidget.trnsysObj:
            if isinstance(t, _spc.SinglePipeConnection):
                t.firstS.labelMass.setVisible(False)

        self.pauseVis()
        self.parent.centralWidget.updateConnGrads()
        self.parent.massFlowEnabled = False

        super(MassFlowVisualizer, self).closeEvent(a0)

    def keyPressEvent(self, e):
        if e.key() == _qtc.Qt.Key_Up:
            self.logger.debug("Up is pressed")
            self.increaseValue()
        elif e.key() == _qtc.Qt.Key_Down:
            self.logger.debug("Down is pressed")
            self.decreaseValue()
