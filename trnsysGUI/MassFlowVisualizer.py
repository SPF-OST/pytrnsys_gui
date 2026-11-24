# pylint: skip-file
# type: ignore

import datetime as _dt
import itertools as _it
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
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

# Temperature colour scales, from min (0) to max (1)
_COLOR_SCALES = {
    # blue -> cyan -> green -> yellow -> red
    "Default": [
        (0.0, (0, 0, 200)),
        (0.25, (0, 160, 255)),
        (0.5, (32, 192, 64)),
        (0.75, (255, 208, 0)),
        (1.0, (208, 0, 0)),
    ],
    # viridis: dark purple -> blue -> green -> yellow, readable with colour blindness and in grey
    "Colour-blind safe": [
        (0.0, (68, 1, 84)),
        (0.25, (59, 82, 139)),
        (0.5, (33, 145, 140)),
        (0.75, (94, 201, 98)),
        (1.0, (253, 231, 37)),
    ],
    # heat map: dark blue -> blue -> purple -> red -> dark red (no white middle: stays visible on white)
    "Heat map": [
        (0.0, (5, 30, 90)),
        (0.25, (40, 100, 190)),
        (0.5, (140, 80, 160)),
        (0.75, (215, 45, 45)),
        (1.0, (100, 0, 15)),
    ],
}
_COLOR_SCALE_STOPS = _COLOR_SCALES["Default"]


def getTemperatureColor(
    temperature: float,
    minTemperature: float,
    maxTemperature: float,
    stops=None,
) -> _qtg.QColor:
    """Colour of a temperature on the scale; values outside [min, max] get the end colours."""
    stops = stops or _COLOR_SCALE_STOPS
    if maxTemperature <= minTemperature:
        fraction = 0.5
    else:
        fraction = (temperature - minTemperature) / (
            maxTemperature - minTemperature
        )
    fraction = min(1.0, max(0.0, fraction))
    for (lowerStop, lowerColor), (upperStop, upperColor) in zip(
        stops, stops[1:]
    ):
        if fraction <= upperStop:
            weight = (fraction - lowerStop) / (upperStop - lowerStop)
            red, green, blue = (
                round(lower + (upper - lower) * weight)
                for lower, upper in zip(lowerColor, upperColor)
            )
            return _qtg.QColor(red, green, blue)
    return _qtg.QColor(*stops[-1][1])


class _DayMonthPicker(_qtw.QFrame):
    """Pop-up to pick a day: a month list and the day numbers 1..31.
    No weekdays and no year, because the simulated year is not known (only the year
    index, "year 2", when the file goes beyond the first year)."""

    _MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    def __init__(self, dateTimeEdit: _qtw.QDateTimeEdit, onPicked):
        super().__init__(None, _qtc.Qt.Popup)
        self.setFrameShape(_qtw.QFrame.StyledPanel)
        self._edit = dateTimeEdit
        self._onPicked = onPicked
        self._first = dateTimeEdit.minimumDateTime().date()
        self._last = dateTimeEdit.maximumDateTime().date()
        firstYear = self._first.year()

        self._months = []  # (year, month) in the range of the file
        year, month = self._first.year(), self._first.month()
        while (year, month) <= (self._last.year(), self._last.month()):
            self._months.append((year, month))
            year, month = (year + 1, 1) if month == 12 else (year, month + 1)

        self._monthComboBox = _qtw.QComboBox()
        severalYears = self._last.year() > firstYear
        for year, month in self._months:
            label = self._MONTH_NAMES[month - 1]
            if severalYears:
                label += f" (year {year - firstYear + 1})"
            self._monthComboBox.addItem(label)
        current = dateTimeEdit.date()
        self._monthComboBox.setCurrentIndex(self._months.index((current.year(), current.month())))
        self._monthComboBox.currentIndexChanged.connect(self._fillDays)

        self._daysLayout = _qtw.QGridLayout()
        self._daysLayout.setSpacing(2)
        layout = _qtw.QVBoxLayout(self)
        layout.addWidget(self._monthComboBox)
        layout.addLayout(self._daysLayout)
        self._fillDays()

    def _fillDays(self) -> None:
        while self._daysLayout.count():
            oldButton = self._daysLayout.takeAt(0).widget()
            oldButton.hide()
            oldButton.deleteLater()
        year, month = self._months[self._monthComboBox.currentIndex()]
        current = self._edit.date()
        for day in range(1, _qtc.QDate(year, month, 1).daysInMonth() + 1):
            date = _qtc.QDate(year, month, day)
            button = _qtw.QToolButton()
            button.setText(str(day))
            button.setFixedSize(30, 24)
            button.setEnabled(self._first <= date <= self._last)
            if date == current:
                button.setStyleSheet("font-weight: bold")
            button.clicked.connect(lambda _=False, d=date: self._pick(d))
            self._daysLayout.addWidget(button, (day - 1) // 7, (day - 1) % 7)  # 7 per row, no weekdays

    def _pick(self, date: _qtc.QDate) -> None:
        dateTime = _qtc.QDateTime(date, self._edit.time(), _qtc.Qt.UTC)
        self._edit.setDateTime(dateTime)  # clamped to the range of the file
        self.close()
        self._onPicked()


class _ColorBar(_qtw.QWidget):
    """Colour bar of the temperature scale with ticks in deg C."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._minTemperature = 0.0
        self._maxTemperature = 100.0
        self._stops = _COLOR_SCALE_STOPS
        self.setMinimumHeight(42)
        self.setMinimumWidth(300)

    def setRange(self, minTemperature: float, maxTemperature: float) -> None:
        self._minTemperature = minTemperature
        self._maxTemperature = maxTemperature
        self.update()

    def setStops(self, stops) -> None:
        self._stops = stops
        self.update()

    def paintEvent(self, event):  # pylint: disable=unused-argument
        painter = _qtg.QPainter(self)
        painter.setRenderHint(_qtg.QPainter.Antialiasing)
        left, right, barHeight = 10, self.width() - 40, 16
        gradient = _qtg.QLinearGradient(left, 0, right, 0)
        for stop, color in self._stops:
            gradient.setColorAt(stop, _qtg.QColor(*color))
        barRect = _qtc.QRectF(left, 2, right - left, barHeight)
        painter.fillRect(barRect, _qtg.QBrush(gradient))
        painter.setPen(_qtg.QColor(80, 80, 80))
        painter.drawRect(barRect)

        span = self._maxTemperature - self._minTemperature
        if span <= 0:
            return
        tickStep = _getNiceTickStep(span)
        firstTick = _np.ceil(self._minTemperature / tickStep) * tickStep
        tick = firstTick
        while tick <= self._maxTemperature + 1e-9:
            x = left + (tick - self._minTemperature) / span * (right - left)
            painter.drawLine(_qtc.QPointF(x, 2 + barHeight), _qtc.QPointF(x, 6 + barHeight))
            label = f"{tick:g}"
            painter.drawText(
                _qtc.QRectF(x - 20, 8 + barHeight, 40, 14),
                _qtc.Qt.AlignHCenter,
                label,
            )
            tick += tickStep
        painter.drawText(
            _qtc.QRectF(right + 6, 2, 34, barHeight), _qtc.Qt.AlignVCenter, "°C"
        )


def _getNiceTickStep(span: float) -> float:
    rawStep = span / 10
    magnitude = 10 ** _np.floor(_np.log10(rawStep))
    for factor in (1, 2, 5, 10):
        if rawStep <= factor * magnitude:
            return factor * magnitude
    return 10 * magnitude


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

        self.medianValueMfr = 0
        self.lowerQuarterMfr = 0
        self.upperQuarterMfr = 0
        self.minValueMfr = 0
        self.maxValueMfr = 0

        self.getThresholdValues()

        # Temperature scale: limits read from the file every time it is loaded
        self._fileMinTemperature, self._fileMaxTemperature = (
            self._getFileTemperatureRange()
        )
        self._minTemperature = self._fileMinTemperature
        self._maxTemperature = self._fileMaxTemperature

        # Time interval to show (rows of the files), whole file by default
        self._startRow = 0
        self._endRow = self.maxTimeStep

        # Playback speed (time steps shown per second)
        self._framesPerSecond = 1.0

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

        # --- temperature scale: min / max fields, reset button, colour bar
        self._minTemperatureSpinBox = self._createTemperatureSpinBox(
            self._minTemperature
        )
        self._maxTemperatureSpinBox = self._createTemperatureSpinBox(
            self._maxTemperature
        )
        self._minTemperatureSpinBox.valueChanged.connect(
            self._onTemperatureRangeChanged
        )
        self._maxTemperatureSpinBox.valueChanged.connect(
            self._onTemperatureRangeChanged
        )
        useFileRangeButton = _qtw.QPushButton("Use range of file")
        useFileRangeButton.clicked.connect(self._onUseFileRange)
        self._colorBar = _ColorBar()
        self._colorBar.setRange(self._minTemperature, self._maxTemperature)

        self._colorScaleStops = _COLOR_SCALES["Default"]
        self._colorScaleComboBox = _qtw.QComboBox()
        self._colorScaleComboBox.addItems(list(_COLOR_SCALES))
        self._colorScaleComboBox.setToolTip(
            "Default: blue - green - red\n"
            "Colour-blind safe: purple - green - yellow (viridis)\n"
            "Heat map: dark blue - purple - dark red"
        )
        self._colorScaleComboBox.currentTextChanged.connect(
            self._onColorScaleChanged
        )

        colorLayout = _qtw.QHBoxLayout()
        colorLayout.addWidget(self._colorScaleComboBox)
        colorLayout.addWidget(_qtw.QLabel("Min [°C]"))
        colorLayout.addWidget(self._minTemperatureSpinBox)
        colorLayout.addWidget(_qtw.QLabel("Max [°C]"))
        colorLayout.addWidget(self._maxTemperatureSpinBox)
        colorLayout.addWidget(useFileRangeButton)
        colorLayout.addWidget(
            _qtw.QLabel("grey = no flow, pipe width = mass flow")
        )
        colorLayout.addStretch()

        # --- time interval of the file to show
        firstTime, lastTime = self.getTime(0), self.getTime(self.maxTimeStep)
        fileRangeLabel = _qtw.QLabel(
            f"File: {self._formatTime(firstTime)} to {self._formatTime(lastTime)}"
        )
        # date fields (day, month, hour, minute); they also work across the new year,
        # e.g. for a simulation from October to March
        self._fromDateTimeEdit = self._createDateTimeEdit(firstTime)
        self._toDateTimeEdit = self._createDateTimeEdit(lastTime)
        self._fromDateTimeEdit.editingFinished.connect(self._onTimeIntervalChanged)
        self._toDateTimeEdit.editingFinished.connect(self._onTimeIntervalChanged)

        intervalLayout = _qtw.QHBoxLayout()
        intervalLayout.addWidget(fileRangeLabel)
        intervalLayout.addSpacing(20)
        intervalLayout.addWidget(_qtw.QLabel("Show from"))
        intervalLayout.addWidget(self._fromDateTimeEdit)
        intervalLayout.addWidget(self._createPickerButton(self._fromDateTimeEdit))
        intervalLayout.addWidget(_qtw.QLabel("to"))
        intervalLayout.addWidget(self._toDateTimeEdit)
        intervalLayout.addWidget(self._createPickerButton(self._toDateTimeEdit))
        intervalLayout.addStretch()

        # --- playback speed
        self._speedSpinBox = _qtw.QDoubleSpinBox()
        self._speedSpinBox.setDecimals(1)
        self._speedSpinBox.setRange(0.1, 50.0)
        self._speedSpinBox.setSingleStep(0.5)
        self._speedSpinBox.setValue(self._framesPerSecond)
        self._speedSpinBox.setToolTip("Images (time steps) shown per second")
        self._speedSpinBox.valueChanged.connect(self._onSpeedChanged)

        buttonLayout = _qtw.QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self._timeStepIncreaseLabel)
        buttonLayout.addWidget(self._timeStepIncreaseLineEdit)
        buttonLayout.addWidget(_qtw.QLabel("Speed [images/s]"))
        buttonLayout.addWidget(self._speedSpinBox)
        buttonLayout.addWidget(self.showMassButton)  # comment out
        buttonLayout.addWidget(self.togglePauseButton)
        buttonLayout.addWidget(self.cancelButton)
        layout = _qtw.QGridLayout()
        layout.addWidget(nameLabel, 0, 0)
        layout.addWidget(self.le, 0, 1)
        layout.addLayout(colorLayout, 1, 0, 1, 2)
        layout.addWidget(self._colorBar, 2, 0, 1, 2)
        layout.addLayout(intervalLayout, 3, 0, 1, 2)
        layout.addLayout(buttonLayout, 4, 0, 1, 2)
        layout.addWidget(self.currentStepLabel, 5, 0, 1, 2)
        layout.addWidget(self.slider, 6, 0, 1, 2)

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
                t.setMassFlowLabelVisible(self.showMass)

        self.logger.debug(
            "temperature scale: %s ... %s"
            % (str(self._minTemperature), str(self._maxTemperature))
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
        self.qtm.start(self._getTimerIntervalInMs())

    def advance(self):
        if self.timeStep >= self._endRow:
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
                if massFlow == 0 or _pd.isna(temperature):
                    t.setColor(thickValue, mfr="ZeroMfr")
                else:
                    color = getTemperatureColor(
                        temperature,
                        self._minTemperature,
                        self._maxTemperature,
                        self._colorScaleStops,
                    )
                    t.setColor(thickValue, color=color)

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
            self.qtm.start(self._getTimerIntervalInMs())
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
        if self.timeStep > self._endRow:
            self.timeStep = self._startRow
        self.slider.setValue(self.timeStep)

    def decreaseValue(self):
        """
        For automatic slider movement

        """

        self.timeStep -= self._timeStepIncrease
        if self.timeStep < self._startRow:
            self.timeStep = self._endRow
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

    def _getFileTemperatureRange(self) -> _tp.Tuple[float, float]:
        """Lowest and highest temperature in the temperature file (time column excluded)."""
        temperatures = self.tempMassFlowData.iloc[:, 1:].apply(
            _pd.to_numeric, errors="coerce"
        )
        values = temperatures.to_numpy(dtype=float).ravel()
        values = values[~_np.isnan(values)]
        if values.size == 0:
            return 0.0, 100.0
        minTemperature = float(_np.floor(values.min()))
        maxTemperature = float(_np.ceil(values.max()))
        if maxTemperature <= minTemperature:
            maxTemperature = minTemperature + 1
        return minTemperature, maxTemperature

    @staticmethod
    def _createTemperatureSpinBox(value: float) -> _qtw.QDoubleSpinBox:
        spinBox = _qtw.QDoubleSpinBox()
        spinBox.setDecimals(1)
        spinBox.setRange(-100.0, 1000.0)
        spinBox.setSingleStep(5.0)
        spinBox.setValue(value)
        return spinBox

    def _onTemperatureRangeChanged(self) -> None:
        self._minTemperature = self._minTemperatureSpinBox.value()
        self._maxTemperature = self._maxTemperatureSpinBox.value()
        self._colorBar.setRange(self._minTemperature, self._maxTemperature)
        self.advance()

    def _onColorScaleChanged(self, name: str) -> None:
        self._colorScaleStops = _COLOR_SCALES[name]
        self._colorBar.setStops(self._colorScaleStops)
        self.advance()

    def _onUseFileRange(self) -> None:
        for spinBox, value in (
            (self._minTemperatureSpinBox, self._fileMinTemperature),
            (self._maxTemperatureSpinBox, self._fileMaxTemperature),
        ):
            spinBox.blockSignals(True)
            spinBox.setValue(value)
            spinBox.blockSignals(False)
        self._onTemperatureRangeChanged()

    def _getTimerIntervalInMs(self) -> int:
        return max(20, round(1000 / self._framesPerSecond))

    def _onSpeedChanged(self, framesPerSecond: float) -> None:
        self._framesPerSecond = framesPerSecond
        if self.started and not self.paused:
            self.qtm.setInterval(self._getTimerIntervalInMs())

    # Simulation hours are counted from 1 January of the first simulated year (8760 h per year).
    # They are shown as dates of a reference year without 29 February (2001, 2002, ...), so that
    # hours beyond 8760 (second year, e.g. October to March) fall in January of the next year.
    # UTC: no daylight-saving shifts (simulation time has none)
    _REFERENCE_START = _qtc.QDateTime(
        _qtc.QDate(2001, 1, 1), _qtc.QTime(0, 0), _qtc.Qt.UTC
    )

    @classmethod
    def _hoursToDateTime(cls, hours: float) -> _qtc.QDateTime:
        return cls._REFERENCE_START.addSecs(int(round(float(hours) * 3600)))

    @classmethod
    def _dateTimeToHours(cls, dateTime: _qtc.QDateTime) -> float:
        return cls._REFERENCE_START.secsTo(dateTime) / 3600.0

    def _createDateTimeEdit(self, hours: float) -> _qtw.QDateTimeEdit:
        dateTimeEdit = _qtw.QDateTimeEdit()
        dateTimeEdit.setTimeSpec(_qtc.Qt.UTC)
        dateTimeEdit.setDisplayFormat("dd.MM. HH:mm")
        dateTimeEdit.setCalendarPopup(False)  # the Qt calendar shows weekdays and a year
        dateTimeEdit.setMinimumWidth(100)
        dateTimeEdit.setDateTimeRange(
            self._hoursToDateTime(self.getTime(0)),
            self._hoursToDateTime(self.getTime(self.maxTimeStep)),
        )
        dateTimeEdit.setDateTime(self._hoursToDateTime(hours))
        dateTimeEdit.setToolTip(
            "Day, month and time of the simulation. Select the day, month or hour "
            "with the cursor and use the arrows, or pick the day with the button next to it."
        )
        return dateTimeEdit

    def _createPickerButton(self, dateTimeEdit: _qtw.QDateTimeEdit) -> _qtw.QToolButton:
        button = _qtw.QToolButton()
        button.setText("▾")
        button.setToolTip("Pick day and month")

        def openPicker():
            picker = _DayMonthPicker(dateTimeEdit, self._onTimeIntervalChanged)
            picker.move(dateTimeEdit.mapToGlobal(_qtc.QPoint(0, dateTimeEdit.height())))
            picker.show()
            self._picker = picker  # keep a reference while it is open

        button.clicked.connect(openPicker)
        return button

    def _getRowOfTime(self, time: float) -> int:
        timeColumn = self.massFlowData[self.massFlowData.columns[0]].to_numpy(
            dtype=float
        )
        row = int(_np.searchsorted(timeColumn, time, side="left"))
        return min(max(row, 0), self.maxTimeStep)

    def _onTimeIntervalChanged(self) -> None:
        fromTime = self._dateTimeToHours(self._fromDateTimeEdit.dateTime())
        toTime = self._dateTimeToHours(self._toDateTimeEdit.dateTime())
        if toTime < fromTime:
            fromTime, toTime = toTime, fromTime
        self._startRow = self._getRowOfTime(fromTime)
        self._endRow = max(self._getRowOfTime(toTime), self._startRow)

        self.slider.blockSignals(True)
        self.slider.setRange(self._startRow, self._endRow)
        self.slider.blockSignals(False)
        if not self._startRow <= self.timeStep <= self._endRow:
            self.timeStep = self._startRow
        self.slider.setValue(self.timeStep)
        self.currentStepLabel.setText(
            "Time: " + str(self.convertTime(self.getTime(self.timeStep)))
        )
        self.advance()

    @staticmethod
    def _formatTime(hours) -> str:
        """Hours of the simulation as day.month hour:minute (+ year if beyond the first one)."""
        hours = float(hours)
        year, hourOfYear = divmod(hours, 8760.0)
        moment = _dt.datetime(2001, 1, 1) + _dt.timedelta(hours=hourOfYear)
        text = moment.strftime("%d.%m. %H:%M")
        if year >= 1:
            text += f" (year {int(year) + 1})"
        return text

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
        Convert the time (hours of the simulation) into "dd.mm. HH:MM", like the interval fields
        """
        return self._formatTime(time)

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
