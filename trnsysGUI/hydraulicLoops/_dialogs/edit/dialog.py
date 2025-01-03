__all__ = ["HydraulicLoopDialog"]

import abc as _abc
import dataclasses as _dc
import itertools as _it
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

import trnsysGUI.dialogs as _dlgs
import trnsysGUI.hydraulicLoops.model as _model
import trnsysGUI.hydraulicLoops.connectionsDefinitionMode as _cdm

from . import model as _gmodel

_dlgs.assertThatLocalGeneratedUIModuleAndResourcesExist(__name__)

from . import _UI_dialog_generated as _uigen  # type: ignore[import]  # pylint: disable=wrong-import-position


class HydraulicLoopDialog(_qtw.QDialog, _uigen.Ui_hydraulicLoopDialog):
    def __init__(
        self,
        hydraulicLoop: _gmodel.HydraulicLoop,
        occupiedNames: _tp.Sequence[str],
        fluids: _model.Fluids,
    ):
        super().__init__()
        self.setupUi(self)

        self._hydraulicLoop = hydraulicLoop
        self._occupiedNames = occupiedNames
        self._fluids = fluids

        self._configureAndInitializeLoopGroupBox()

        self._configureBulkOperations()

        self._reloadConnections()

        self.connectionsTableView.resizeRowsToContents()
        self.connectionsTableView.resizeColumnsToContents()

    def _configureAndInitializeLoopGroupBox(self) -> None:
        self._configureLoopNameLineEdit()
        self.loopName.setText(self._hydraulicLoop.name)

        self._configureFluidComboBox()
        self._setCurrentData(self.fluidComboBox, self._hydraulicLoop.fluid)

        self._configureConnectionsDefinitionModeComboBox()
        self._setConnectionsDefinitionMode(
            self._hydraulicLoop.connectionsDefinitionMode
        )

    def _configureConnectionsDefinitionModeComboBox(self) -> None:
        self.connectionsDefinitionModeComboBox.addItem(
            "Define connections individually",
            _cdm.ConnectionsDefinitionMode.INDIVIDUAL,
        )
        self.connectionsDefinitionModeComboBox.addItem(
            "Define loop wide defaults",
            _cdm.ConnectionsDefinitionMode.LOOP_WIDE_DEFAULTS,
        )
        self.connectionsDefinitionModeComboBox.addItem(
            "All pipes in loops are dummies",
            _cdm.ConnectionsDefinitionMode.DUMMY_PIPES,
        )

        def onActivated(newIndex: int) -> None:
            oldMode = self.connectionsDefinitionModeComboBox.currentIndex()
            newMode = self.connectionsDefinitionModeComboBox.itemData(newIndex)

            haveChangedAwayFromIndividualMode = (
                oldMode == _cdm.ConnectionsDefinitionMode.INDIVIDUAL
                and newMode != _cdm.ConnectionsDefinitionMode.INDIVIDUAL
            )
            if (
                haveChangedAwayFromIndividualMode
                and not self._doesUserSayContinueWithChangingAwayFromDefiningPipesIndividually()
            ):
                self._setCurrentData(
                    self.connectionsDefinitionModeComboBox,
                    _cdm.ConnectionsDefinitionMode.INDIVIDUAL,
                )
                return

            self._setConnectionsDefinitionMode(newMode)

            self.adjustSize()

        self.connectionsDefinitionModeComboBox.activated.connect(onActivated)

    @staticmethod
    def _setCurrentData(comboBox: _qtw.QComboBox, data: _tp.Any) -> None:
        index = comboBox.findData(data)
        assert index >= 0
        comboBox.setCurrentIndex(index)

    def _configureLoopNameLineEdit(self) -> None:
        def onNameChanged(newName: str) -> None:
            self._hydraulicLoop.name = newName

            isNameEmpty = not newName
            isNameOccupied = self._isNameOccupied(newName)

            if isNameEmpty:
                tooltipText = "You must specify a name"
            elif isNameOccupied:
                tooltipText = "This name is already in use"
            else:
                tooltipText = ""
            self.invalidNameWarningWidget.setToolTip(tooltipText)

            haveError = isNameEmpty or isNameOccupied
            self.invalidNameWarningWidget.setVisible(haveError)

            okButton = self.okCancelButtonBox.button(self.okCancelButtonBox.Ok)
            okButton.setEnabled(not haveError)

        self.loopName.textChanged.connect(onNameChanged)

    def _isNameOccupied(self, newName: str) -> bool:
        return newName in self._occupiedNames

    def _configureFluidComboBox(self) -> None:
        for fluid in self._fluids.fluids:
            self.fluidComboBox.addItem(fluid.name, userData=fluid)

        def onCurrentIndexChanged(_) -> None:
            self._hydraulicLoop.fluid = self.fluidComboBox.currentData()

        self.fluidComboBox.currentIndexChanged.connect(onCurrentIndexChanged)

    def _configureBulkOperations(self) -> None:
        def setTotalLoopLengthInfoToolTipVisible(_) -> None:
            isVisible = self._isBulkTotalPipeLengthTypeSelected()
            self.bulkLengthInfoIconWidget.setVisible(isVisible)

        self.bulkLengthTypeComboBox.currentTextChanged.connect(
            setTotalLoopLengthInfoToolTipVisible
        )

        def onBulkApplyButtonPressed() -> None:

            diameterText = self.bulkDiameterLineEdit.text()
            diameterInCm = float(diameterText) if diameterText else None

            uValueText = self.bulkUValueLineEdit.text()
            uValueInWPerM2K = float(uValueText) if uValueText else None

            shallBeSimulatedText = (
                self.bulkShallBeSimulatedComboBox.currentText()
            )
            if not shallBeSimulatedText:
                shallBeSimulated = None
            elif shallBeSimulatedText == "Yes":
                shallBeSimulated = True
            elif shallBeSimulatedText == "No":
                shallBeSimulated = False
            else:
                raise AssertionError(
                    "Expecting 'Yes' or 'No' for 'Simulate pipe?' combobox."
                )

            for connection in self._hydraulicLoop.connections:
                pipeLengthInM = self._computeBulkIndividualPipeLength(
                    connection, shallBeSimulated
                )
                if pipeLengthInM is not None:
                    connection.lengthInM = pipeLengthInM

                if diameterInCm is not None:
                    connection.diameterInCm = diameterInCm

                if uValueInWPerM2K is not None:
                    connection.uValueInWPerM2K = uValueInWPerM2K

                if shallBeSimulated is not None:
                    connection.shallBeSimulated = shallBeSimulated

            self._reloadConnections()

        def clearBulkValues() -> None:
            self.bulkLengthLineEdit.clear()
            self.bulkDiameterLineEdit.clear()
            self.bulkUValueLineEdit.clear()
            self.bulkShallBeSimulatedComboBox.setCurrentText("")

        self.bulkApplyButton.pressed.connect(onBulkApplyButtonPressed)
        self.bulkApplyButton.pressed.connect(clearBulkValues)

        self.bulkCancelButton.pressed.connect(clearBulkValues)

        self._configureForPositiveFloat(self.bulkLengthLineEdit)
        self._configureForPositiveFloat(self.bulkDiameterLineEdit)
        self._configureForPositiveFloat(self.bulkUValueLineEdit)

    def _isBulkTotalPipeLengthTypeSelected(self) -> bool:
        text = self.bulkLengthTypeComboBox.currentText()

        if text == "Individual pipe length":
            return False

        if text == "Total loop length":
            return True

        raise AssertionError(f"Unknown bulk length type text: {text}")

    @staticmethod
    def _configureForPositiveFloat(lineEdit: _qtw.QLineEdit) -> None:
        def checkIfTextIsPositiveFloatOrReset() -> None:
            text = lineEdit.text()
            try:
                _parsePositiveFloat(text)
            except ValueError:
                lineEdit.setText("")

        lineEdit.editingFinished.connect(checkIfTextIsPositiveFloatOrReset)

    def _reloadConnections(self) -> None:
        connectionsModel = _ConnectionsUiModel(self._hydraulicLoop.connections)

        connectionsModel.dataChanged.connect(
            lambda *_: self._updatePipesStatisticsLabel()
        )

        self.connectionsTableView.setModel(connectionsModel)

        self._updatePipesStatisticsLabel()

    def _updatePipesStatisticsLabel(self) -> None:
        totalLoopLengthInM = sum(
            c.lengthInM for c in self._hydraulicLoop.simulatedConnections
        )
        nConnections = self._hydraulicLoop.nConnections
        nSimulatedConnections = self._hydraulicLoop.nSimulatedConnections

        statisticsLabelText = (
            f"Number of pipes: {nConnections} (of which {nSimulatedConnections} simulated), "
            f"total loop length: {totalLoopLengthInM:g}m"
        )

        self.pipesStatisticsLabel.setText(statisticsLabelText)

    def _computeBulkIndividualPipeLength(
        self, connection: _gmodel.Connection, bulkShallBeSimulated: bool | None
    ) -> _tp.Optional[float]:
        lengthText = self.bulkLengthLineEdit.text()
        if not lengthText:
            return None

        haveTotalPipeLength = self._isBulkTotalPipeLengthTypeSelected()

        if not haveTotalPipeLength:
            individualPipeLengthInM = float(lengthText)
            return individualPipeLengthInM

        loopLengthInM = float(lengthText)

        isShallBeSimulatedSameForAllConnections = (
            len({c.shallBeSimulated for c in self._hydraulicLoop.connections})
            == 1
        )

        willShallBeSimulatedBeSameForAllConnections = (
            isShallBeSimulatedSameForAllConnections
            or (bulkShallBeSimulated is not None)
        )

        if willShallBeSimulatedBeSameForAllConnections:
            individualPipeLength = (
                loopLengthInM / self._hydraulicLoop.nConnections
            )
            return individualPipeLength

        if not connection.shallBeSimulated:
            return None

        individualPipeLengthM = (
            loopLengthInM / self._hydraulicLoop.nSimulatedConnections
        )

        return individualPipeLengthM

    def _doesUserSayContinueWithChangingAwayFromDefiningPipesIndividually(
        self,
    ) -> bool:
        messageBox = _qtw.QMessageBox(self)
        messageBox.setWindowTitle("Pipe properties will be lost")
        messageBox.setText(
            "Pipe property values will be lost upon OK'ing the dialog when changing away from "
            "defining pipes individually. Proceed anyway?"
        )
        messageBox.setStandardButtons(messageBox.Yes | messageBox.No)
        pressedButton = messageBox.exec()
        shallContinue = pressedButton == messageBox.Yes
        return shallContinue

    def _setConnectionsDefinitionMode(
        self, connectionsDefinitionMode: _cdm.ConnectionsDefinitionMode
    ) -> None:
        self._hydraulicLoop.connectionsDefinitionMode = (
            connectionsDefinitionMode
        )
        self._setCurrentData(
            self.connectionsDefinitionModeComboBox, connectionsDefinitionMode
        )

        areEditWidgetsEnabled = (
            connectionsDefinitionMode
            == _cdm.ConnectionsDefinitionMode.INDIVIDUAL
        )
        self.bulkOperationsGroupBox.setVisible(areEditWidgetsEnabled)
        self.pipesGroupBox.setVisible(areEditWidgetsEnabled)
        self.adjustSize()

    @classmethod
    def showDialog(
        cls,
        hydraulicLoop: _gmodel.HydraulicLoop,
        occupiedNames: _tp.Sequence[str],
        fluids: _model.Fluids,
    ) -> _tp.Literal["oked", "cancelled"]:
        dialog = HydraulicLoopDialog(hydraulicLoop, occupiedNames, fluids)

        dialogCode = dialog.exec()

        if dialogCode == _qtw.QDialog.Accepted:
            return "oked"

        if dialogCode == _qtw.QDialog.Rejected:
            return "cancelled"

        raise AssertionError(f"Unknown dialog code {dialogCode}.")


_PropertyValue = str | float | bool


@_dc.dataclass
class _Property(_abc.ABC):
    header: str
    getter: _tp.Callable[[_gmodel.Connection], _PropertyValue]
    setter: _tp.Optional[
        _tp.Callable[[_gmodel.Connection, _PropertyValue], None]
    ] = None
    shallHighlightOutliers: bool = True

    @property
    @_abc.abstractmethod
    def mayBeEditable(self) -> bool:
        raise NotImplementedError()

    @property
    @_abc.abstractmethod
    def mayBeUserCheckable(self) -> bool:
        raise NotImplementedError()

    @property
    @_abc.abstractmethod
    def mayBeDisplayable(self) -> bool:
        raise NotImplementedError()


class _TextProperty(_Property):
    @property
    def mayBeDisplayable(self) -> bool:
        return True

    @property
    def mayBeEditable(self) -> bool:
        return True

    @property
    def mayBeUserCheckable(self) -> bool:
        return False


class _BoolProperty(_Property):
    @property
    def mayBeDisplayable(self) -> bool:
        return False

    @property
    def mayBeEditable(self) -> bool:
        return False

    @property
    def mayBeUserCheckable(self) -> bool:
        return True


def _parsePositiveFloat(text: str) -> float:
    value = float(text)

    if value < 0:
        raise ValueError("Value must be positive.")

    return value


def _setConnectionDiameter(
    connection: _gmodel.Connection, diameterInCmText: _tp.Any
) -> None:
    connection.diameterInCm = _parsePositiveFloat(diameterInCmText)


def _setConnectionUValue(
    connection: _gmodel.Connection, uValueInWPerM2KText: _tp.Any
) -> None:
    connection.uValueInWPerM2K = _parsePositiveFloat(uValueInWPerM2KText)


def _setConnectionLength(
    connection: _gmodel.Connection, lengthInMText: _tp.Any
) -> None:
    connection.lengthInM = _parsePositiveFloat(lengthInMText)


def _setshallBeSimulated(
    connection: _gmodel.Connection, shallBeSimulated: _tp.Any
) -> None:
    connection.shallBeSimulated = shallBeSimulated


class _ConnectionsUiModel(_qtc.QAbstractItemModel):
    _SHALL_SIMULATE_PROPERTY = _BoolProperty(
        "Simulate?", lambda c: c.shallBeSimulated, _setshallBeSimulated
    )

    _PROPERTIES = [
        _SHALL_SIMULATE_PROPERTY,
        _TextProperty("Name", lambda c: c.name, shallHighlightOutliers=False),
        _TextProperty(
            "Diameter [cm]", lambda c: c.diameterInCm, _setConnectionDiameter
        ),
        _TextProperty(
            "U value [W/(m^2 K)]",
            lambda c: c.uValueInWPerM2K,
            _setConnectionUValue,
        ),
        _TextProperty(
            "Length [m]", lambda c: c.lengthInM, _setConnectionLength
        ),
    ]

    def __init__(self, connections: _tp.Sequence[_gmodel.Connection]):
        super().__init__()

        self.connections = connections

    def rowCount(self, parent: _qtc.QModelIndex = _qtc.QModelIndex()) -> int:
        if not self._isTopLevel(parent):
            return 0

        return len(self.connections)

    def columnCount(
        self, parent: _qtc.QModelIndex = _qtc.QModelIndex()
    ) -> int:
        if not self._isTopLevel(parent):
            return 0

        return len(self._headers)

    def headerData(
        self,
        section: int,
        orientation: _qtc.Qt.Orientation,
        role: int = _qtc.Qt.DisplayRole,
    ) -> _tp.Any:
        if role != _qtc.Qt.DisplayRole or orientation != _qtc.Qt.Horizontal:
            return None

        return self._headers[section]

    @property
    def _headers(self) -> _tp.Sequence[str]:
        return [p.header for p in self._PROPERTIES]

    def data(
        self, modelIndex: _qtc.QModelIndex, role: int = _qtc.Qt.DisplayRole
    ) -> _tp.Any:
        connection, prop = self._getConnectionAndProperty(modelIndex)

        if role == _qtc.Qt.DisplayRole:
            if prop.mayBeUserCheckable:
                return None

            data = prop.getter(connection)  # type: ignore[misc,call-arg]

            return data

        if role == _qtc.Qt.CheckStateRole:
            if not prop.mayBeUserCheckable:
                return None

            data = prop.getter(connection)  # type: ignore[misc,call-arg]

            data = _qtc.Qt.Checked if data else _qtc.Qt.Unchecked

            return data

        if role in [_qtc.Qt.FontRole, _qtc.Qt.ForegroundRole]:
            return self._getHighlightDataOrNone(connection, prop, role)

        return None

    def _getHighlightDataOrNone(
        self, connection: _gmodel.Connection, prop: _Property, role: int
    ) -> _tp.Any:
        if not prop.shallHighlightOutliers:
            return None

        if not connection.shallBeSimulated:
            return None

        mostUsedValue = self._getMostUsedValue(prop)
        value = prop.getter(connection)  # type: ignore[misc,call-arg]
        shallHighlight = value != mostUsedValue

        if role == _qtc.Qt.FontRole:
            if not shallHighlight:
                return _qtg.QFont()

            highlightFont = _qtg.QFont()
            highlightFont.setBold(True)
            return highlightFont

        if role == _qtc.Qt.ForegroundRole:
            if not shallHighlight:
                return _qtg.QColorConstants.Black

            return _qtg.QColorConstants.Red

        raise ValueError(
            f"Role must be {_qtc.Qt.FontRole} or {_qtc.Qt.ForegroundRole}.",
            role,
        )

    def _getMostUsedValue(self, prop: _Property) -> _PropertyValue:
        sortedValues = sorted(
            prop.getter(c) for c in self.connections if c.shallBeSimulated  # type: ignore[misc, call-arg]
        )
        groupedValues = _it.groupby(sortedValues)
        valuesWithCount = [
            {"value": v, "count": len(list(vs))} for v, vs in groupedValues
        ]
        mostUsedValueWithCount = max(
            valuesWithCount, key=lambda vwc: vwc["count"]
        )
        return mostUsedValueWithCount["value"]

    def setData(
        self,
        index: _qtc.QModelIndex,
        value: _tp.Any,
        role: int = _qtc.Qt.EditRole,
    ) -> bool:
        if role not in [_qtc.Qt.EditRole, _qtc.Qt.CheckStateRole]:
            return False

        if role == _qtc.Qt.CheckStateRole:
            value = value == _qtc.Qt.Checked

        connection, prop = self._getConnectionAndProperty(index)

        try:
            prop.setter(connection, value)  # type: ignore[misc]
        except ValueError:
            return False

        self._emitRowDataChanged(index)

        return True

    def _emitRowDataChanged(self, index: _qtc.QModelIndex) -> None:
        rowStartIndex = index.siblingAtColumn(0)
        nRows = index.model().columnCount()
        rowEndIndex = index.siblingAtColumn(nRows - 1)
        self.dataChanged.emit(rowStartIndex, rowEndIndex)

    def _getConnectionAndProperty(
        self, modelIndex: _qtc.QModelIndex
    ) -> _tp.Tuple[_gmodel.Connection, _Property]:
        rowIndex = modelIndex.row()
        connection = self.connections[rowIndex]

        propertyIndex = modelIndex.column()
        prop = self._PROPERTIES[propertyIndex]

        return connection, prop

    def flags(self, index: _qtc.QModelIndex) -> _qtc.Qt.ItemFlags:
        connection, prop = self._getConnectionAndProperty(index)

        if (
            not connection.shallBeSimulated
            and prop != self._SHALL_SIMULATE_PROPERTY
        ):
            return _qtc.Qt.ItemFlags(_qtc.Qt.NoItemFlags)

        flags = _qtc.Qt.ItemIsEnabled | _qtc.Qt.ItemIsSelectable
        hasSetter = bool(prop.setter)
        if not hasSetter:
            return flags

        if prop.mayBeEditable:
            flags |= _qtc.Qt.ItemIsEditable

        if prop.mayBeUserCheckable:
            flags |= _qtc.Qt.ItemIsUserCheckable

        return flags

    def index(
        self,
        row: int,
        column: int,
        parent: _tp.Optional[_qtc.QModelIndex] = None,
    ) -> _qtc.QModelIndex:
        assert parent

        if not self._isTopLevel(parent):
            return _qtc.QModelIndex()

        if not 0 <= row < self.rowCount():
            return _qtc.QModelIndex()

        if not 0 <= column < self.columnCount():
            return _qtc.QModelIndex()

        return self.createIndex(row, column)

    def parent(self, _: _qtc.QModelIndex) -> _qtc.QModelIndex:  # type: ignore[override]
        return _qtc.QModelIndex()

    @staticmethod
    def _isTopLevel(parent: _qtc.QModelIndex) -> bool:
        return not parent.isValid()
