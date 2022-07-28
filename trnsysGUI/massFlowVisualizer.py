from __future__ import annotations

import dataclasses as _dc
import datetime as _dt
import pathlib as _pl
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw
import numpy as _np
import pandas as _pd  # type: ignore[import]
import pytrnsys.utils.result as _res

import trnsysGUI.TVentil as _tv
import trnsysGUI.connection.names as _cnames
import trnsysGUI.connection.singlePipeConnection as _spc
import trnsysGUI.massFlowSolver.names as _mnames
import trnsysGUI.massFlowSolver.networkModel as _mfn

if _tp.TYPE_CHECKING:
    import trnsysGUI.diagram.Editor as _ed


class MassFlowVisualizer(_qtw.QDialog):  # pylint: disable=too-many-instance-attributes
    @staticmethod
    def createAndShow(
        editor: _ed.Editor,  # type: ignore[name-defined]
        massFlowsFilePath: _pl.Path,
        temperaturesFilePath: _pl.Path,  # type: ignore[name-defined]
    ) -> _res.Result[None]:
        massFlowData = _pd.read_csv(massFlowsFilePath, sep="\t", index_col=0).rename(columns=lambda x: x.strip())
        temperatureData = _pd.read_csv(temperaturesFilePath, sep="\t", index_col=0).rename(columns=lambda x: x.strip())

        trnsysObjects = editor.trnsysObj
        connections = [o for o in trnsysObjects if isinstance(o, _spc.SinglePipeConnection)]
        valves = [o for o in trnsysObjects if isinstance(o, _tv.TVentil)]

        result = _getDataAndMassFlowAndTemperatureQuantiles(
            connections, valves, massFlowData, temperatureData, massFlowsFilePath, temperaturesFilePath
        )
        if _res.isError(result):
            return _res.error(result)
        data, massFlowQuantiles, temperatureQuantiles = _res.value(result)

        visualizer = MassFlowVisualizer(editor, data, massFlowQuantiles, temperatureQuantiles)
        visualizer.show()

        return None

    def __init__(  # pylint: disable=too-many-locals,too-many-statements
        self,
        editor: _ed.Editor,  # type: ignore[name-defined]
        data: _pd.DataFrame,
        massFlowQuantiles: Quantiles,
        temperatureQuantiles: Quantiles,
    ) -> None:
        super().__init__(editor)
        self._editor = editor
        self.logger = editor.logger

        self._data = data
        self._massFlowToWidthMapping = _getMapping(massFlowQuantiles, (2, 4, 5, 7, 6, 8), useAbsoluteValues=True)

        colors = (
            _qtg.QColor(0, 0, 204),  # deep blue
            _qtg.QColor(0, 128, 255),  # blue
            _qtg.QColor(102, 255, 255),  # light blue
            _qtg.QColor(255, 153, 153),  # light red
            _qtg.QColor(255, 51, 51),  # red
            _qtg.QColor(153, 0, 0),  # deep red
        )
        self._temperatureToColorMapping = _getMapping(temperatureQuantiles, colors)

        self.maxTimeStep = data.shape[0] - 1
        self.showMass = False

        self.setMinimumSize(1000, 200)

        self.timeStep = 0
        self.timeSteps = data.shape[1]

        self.jumpValue = _qtw.QLabel("Jump by ( 30 = 1 Hour ):\n              ( 720 = 1 Day )")
        self.jumpValueLE = _qtw.QLineEdit("1")

        self.slider = _qtw.QSlider(editor)
        self.setSlider()
        self.slider.sliderReleased.connect(self.testValChange)
        self.slider.sliderPressed.connect(self.pressedSlider)
        self.slider.valueChanged.connect(self.moveValues)
        self.slider.setTickInterval(24)

        self.qtm = _qtc.QTimer(editor)
        self.lines = None
        self.started = False

        self.paused = True

        nameLabel = _qtw.QLabel("Name:")
        self.currentStepLabel = _qtw.QLabel("Time: " + str(self.convertTime(self.getTime(0))))
        self._lineEdit = _qtw.QLineEdit("NONE")

        self.showMassButton = _qtw.QPushButton("Show mass")
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
        buttonLayout.addWidget(self.showMassButton)
        buttonLayout.addWidget(self.togglePauseButton)
        buttonLayout.addWidget(self.cancelButton)
        layout = _qtw.QGridLayout()
        layout.addWidget(nameLabel, 0, 0)
        layout.addWidget(self._lineEdit, 0, 1)
        layout.addLayout(colorLayout, 1, 0, 1, 0)
        layout.addLayout(buttonLayout, 2, 0, 2, 0)
        layout.addWidget(self.currentStepLabel, 3, 0, 1, 2)
        layout.addWidget(self.slider, 4, 0, 1, 2)  # Only for debug

        self.setLayout(layout)

        self.showMassButton.clicked.connect(self.showMassBtn)
        self.togglePauseButton.clicked.connect(self.togglePause)
        self.cancelButton.clicked.connect(self.cancel)

        self.advance()

        self.setWindowTitle("Flow visualizer")
        self.move(self._editor.diagramView.geometry().topLeft())

    def togglePause(self):
        if self.paused:
            self.continueVis()
        else:
            self.pauseVis()

    def cancel(self):
        self.pauseVis()
        self.close()
        self._editor.updateConnGrads()

    # comment out
    def showMassBtn(self):
        """
        For showing the mass under the connections
        -------

        """
        self.showMass = not self.showMass

        for trnsysObject in self._editor.trnsysObj:
            if isinstance(trnsysObject, _spc.SinglePipeConnection):
                if self.showMass:
                    trnsysObject.firstS.labelMass.setVisible(True)
                else:
                    trnsysObject.firstS.labelMass.setVisible(False)

    def start(self):
        self.paused = False
        self.qtm = _qtc.QTimer(self)
        self.qtm.timeout.connect(self.increaseValue)
        self.qtm.start(1000)

    def advance(self):
        timeStep = int(self.timeStep)

        trnsysObjects = self._editor.trnsysObj

        connections = [o for o in trnsysObjects if isinstance(o, _spc.SinglePipeConnection)]
        for connection in connections:
            mfrVariableName = _mnames.getCanonicalMassFlowVariableName(connection, connection.modelPipe)
            temperatureVariableName = _cnames.getTemperatureVariableName(connection, _mfn.PortItemType.STANDARD)

            if mfrVariableName in self._data and temperatureVariableName in self._data:
                mass = self._data[mfrVariableName].iloc[timeStep]
                temperature = self._data[temperatureVariableName].iloc[timeStep]

                connection.setMassAndTemperature(mass, temperature)

                width = self._massFlowToWidthMapping(mass)
                color = self._temperatureToColorMapping(temperature)

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
            self.qtm.stop()
            self.timeStep = 0
            return

        self.slider.setValue(self.timeStep)

    def decreaseValue(self):
        """
        For automatic slider movement

        """

        self.timeStep -= float(self.jumpValueLE.text())
        if self.timeStep < 0:
            self.timeStep = self.maxTimeStep
        self.slider.setValue(self.timeStep)

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

    def closeEvent(self, event):
        for trnsysObject in self._editor.trnsysObj:
            if isinstance(trnsysObject, _spc.SinglePipeConnection):
                trnsysObject.firstS.labelMass.setVisible(False)

        self.pauseVis()
        self._editor.updateConnGrads()
        self._editor.massFlowEnabled = False

        super().closeEvent(event)

    def keyPressEvent(self, event):
        if event.key() == _qtc.Qt.Key_Up:
            self.logger.debug("Up is pressed")
            self.increaseValue()
        elif event.key() == _qtc.Qt.Key_Down:
            self.logger.debug("Down is pressed")
            self.decreaseValue()


def _getDataAndMassFlowAndTemperatureQuantiles(
    connections: _tp.Sequence[_spc.SinglePipeConnection],
    valves: _tp.Sequence[_tv.TVentil],
    massFlowData: _pd.DataFrame,
    temperatureData: _pd.DataFrame,
    massFlowsFilePath: _pl.Path,
    temperaturesFilePath: _pl.Path,
) -> _res.Result[_tp.Tuple[_pd.DataFrame, Quantiles, Quantiles]]:
    result = _getColumnNames(connections, valves, massFlowData, temperatureData, massFlowsFilePath, temperaturesFilePath)
    if _res.isError(result):
        return _res.error(result)
    columnNames = _res.value(result)

    relevantMassFlowDataColumns = [*columnNames.massFlows, *columnNames.valvePositions]
    relevantTemperatureDataColumns = columnNames.temperatures
    data = _pd.concat(
        [massFlowData[relevantMassFlowDataColumns], temperatureData[relevantTemperatureDataColumns]], axis="columns"
    )

    massFlowQuantiles = _getGlobalQuantiles(data[columnNames.massFlows].abs())
    temperatureQuantiles = _getGlobalQuantiles(data[columnNames.temperatures])

    return data, massFlowQuantiles, temperatureQuantiles


@_dc.dataclass
class _ColumnNames:
    massFlows: _tp.Sequence[str]
    valvePositions: _tp.Sequence[str]
    temperatures: _tp.Sequence[str]


def _getColumnNames(
    connections: _tp.Sequence[_spc.SinglePipeConnection],
    valves: _tp.Sequence[_tv.TVentil],
    massFlowData: _pd.DataFrame,
    temperatureData: _pd.DataFrame,
    massFlowsFilePath: _pl.Path,
    temperaturesFilePath: _pl.Path,
) -> _res.Result[_ColumnNames]:
    errorMessages = []

    connectionMfrNames = {_mnames.getCanonicalMassFlowVariableName(c, c.modelPipe) for c in connections}
    foundConnectionMfrNames = connectionMfrNames & set(massFlowData.columns)
    if not foundConnectionMfrNames:
        errorMessage = f"""\
    Could not find any mass flow rates for single pipes in {massFlowsFilePath}.
    Please check whether the column names in {massFlowsFilePath} corresponding to
    to pipe mass flow rates match the format M<pipe name>. If they don't
    match, change the name and try loading the file again."""
        errorMessages.append(errorMessage)

    connectionTemperatureNames = {_cnames.getTemperatureVariableName(c, _mfn.PortItemType.STANDARD) for c in connections}
    foundConnectionTemperatureNames = connectionTemperatureNames & set(temperatureData.columns)
    if not foundConnectionTemperatureNames:
        errorMessage = f"""\
    Could not find any temperatures for single pipes in {temperaturesFilePath}.
    Please check whether the column names in {temperaturesFilePath} corresponding
    to connection temperatures match the format T<pipe name>. If they
    don't match, change the name and try loading the file again."""
        errorMessages.append(errorMessage)

    valvePositionNames = {_mnames.getInputVariableName(v, v.modelDiverter) for v in valves}
    foundValvePositionNames = valvePositionNames & set(massFlowData.columns)
    if not foundValvePositionNames:
        errorMessage = f"""\
    Could not find any valve positions in {massFlowsFilePath}.
    Please check whether the column names in {massFlowsFilePath} corresponding to
    valve positions match the format xFrac<valve name>. If they don't match,
    change the name and try loading the file again."""
        errorMessages.append(errorMessage)

    if errorMessages:
        jointErrorMessage = "\n\n".join(errorMessages)
        return _res.Error(jointErrorMessage)

    return _ColumnNames(
        list(foundConnectionMfrNames), list(foundValvePositionNames), list(foundConnectionTemperatureNames)
    )


Quantiles = _tp.Tuple[float, float, float, float, float]


_T_co = _tp.TypeVar("_T_co", covariant=True)


def _getGlobalQuantiles(frame: _pd.DataFrame) -> Quantiles:
    values = frame.to_numpy().reshape(-1)
    numericValues = values[~_pd.isna(values)]
    quantiles = _np.quantile(numericValues, q=(1e-3, 0.25, 0.5, 0.75, 1 - 1e-3))
    return quantiles[0], quantiles[1], quantiles[2], quantiles[3], quantiles[4]


def _getMapping(
    quantiles: Quantiles, values: _tp.Tuple[_T_co, _T_co, _T_co, _T_co, _T_co, _T_co], useAbsoluteValues: bool = False
) -> _tp.Callable[[float], _T_co]:
    lowerBounds = [-_np.inf, *quantiles]
    upperBounds = [*quantiles, _np.inf]
    assert len(lowerBounds) == len(upperBounds) == len(values)

    boundsAndValue = list(
        zip(lowerBounds, upperBounds, values)
    )

    def mapping(inputValue: float) -> _T_co:
        inputValue = abs(inputValue) if useAbsoluteValues else inputValue

        for lower, upper, value in boundsAndValue:
            if lower < inputValue <= upper:
                return value

        raise AssertionError("Can't get here")

    return mapping
