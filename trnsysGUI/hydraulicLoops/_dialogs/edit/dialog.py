__all__ = ["HydraulicLoopDialog"]

import dataclasses as _dc
import itertools as _it
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
from PyQt5 import QtWidgets as _qtw

try:
    from . import _UI_dialog_generated as _uigen
    import trnsysGUI.resources.QRC_resources_generated as _
except ImportError as importError:
    raise AssertionError(  # pylint: disable=duplicate-code  # 1
        "Could not find the generated Python code for a .ui or .qrc file. Please run the "
        "`dev-tools\\generateGuiClassesFromQtCreatorStudioUiFiles.py' script from your "
        "`pytrnsys_gui` directory."
    ) from importError

import trnsysGUI.hydraulicLoops.model as _model

from . import model as _gmodel


class HydraulicLoopDialog(_qtw.QDialog, _uigen.Ui_hydraulicLoopDialog):
    def __init__(self, hydraulicLoop: _gmodel.HydraulicLoop, occupiedNames: _tp.Sequence[str], fluids: _model.Fluids):
        super().__init__()
        self.setupUi(self)

        self._hydraulicLoop = hydraulicLoop
        self._occupiedNames = occupiedNames
        self._fluids = fluids

        self._configureAndInitializeLoopGroupBox()

        self._configureBulkOperations()

        self._reloadConnections()

    def _configureAndInitializeLoopGroupBox(self) -> None:
        self._configureLoopNameLineEdit()
        self.loopName.setText(self._hydraulicLoop.name)

        self._configureFluidComboBox()
        fluidIndex = self.fluidComboBox.findData(self._hydraulicLoop.fluid)
        assert fluidIndex >= 0
        self.fluidComboBox.setCurrentIndex(fluidIndex)

        self._setUseLoopWideDefaults(self._hydraulicLoop.useLoopWideDefaults)
        self._configureUseLoopWideDefaultsCheckbox()

    def _configureUseLoopWideDefaultsCheckbox(self) -> None:
        def onToggled(isSet: bool) -> None:
            if isSet and not self._doesUserSayContinueWithEnablingLoopWideDefaults():
                self.useLoopWideDefaultsCheckBox.setChecked(False)
                return

            self._setUseLoopWideDefaults(isSet)

            self.adjustSize()

        self.useLoopWideDefaultsCheckBox.toggled.connect(onToggled)

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

        self.bulkLengthTypeComboBox.currentTextChanged.connect(setTotalLoopLengthInfoToolTipVisible)

        def onBulkApplyButtonPressed() -> None:
            individualPipeLengthInM = self._bulkIndividualPipeLengthInM

            diameterText = self.bulkDiameterLineEdit.text()
            diameterInCm = float(diameterText) if diameterText else None

            uValueText = self.bulkUValueLineEdit.text()
            uValueInWPerM2K = float(uValueText) if uValueText else None

            for connection in self._hydraulicLoop.connections:
                if individualPipeLengthInM is not None:
                    connection.lengthInM = individualPipeLengthInM

                if diameterInCm is not None:
                    connection.diameterInCm = diameterInCm

                if uValueInWPerM2K is not None:
                    connection.uValueInWPerM2K = uValueInWPerM2K

            self._reloadConnections()

        def clearLineEdits() -> None:
            self.bulkLengthLineEdit.clear()
            self.bulkDiameterLineEdit.clear()
            self.bulkUValueLineEdit.clear()

        self.bulkApplyButton.pressed.connect(onBulkApplyButtonPressed)
        self.bulkApplyButton.pressed.connect(clearLineEdits)

        self.bulkCancelButton.pressed.connect(clearLineEdits)

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

        connectionsModel.dataChanged.connect(lambda *_: self._updatePipesStatisticsLabel())

        self.connectionsTableView.setModel(connectionsModel)

        self.connectionsTableView.resizeRowsToContents()
        self.connectionsTableView.resizeColumnsToContents()

        self._updatePipesStatisticsLabel()

    def _updatePipesStatisticsLabel(self) -> None:
        totalLoopLengthInM = sum(c.lengthInM for c in self._hydraulicLoop.connections)
        statisticsLabelText = (
            f"Number of pipes: {len(self._hydraulicLoop.connections)}, total loop length: {totalLoopLengthInM:g} m"
        )
        self.pipesStatisticsLabel.setText(statisticsLabelText)

    @property
    def _bulkIndividualPipeLengthInM(self) -> _tp.Optional[float]:
        lengthText = self.bulkLengthLineEdit.text()
        if not lengthText:
            return None

        haveTotalPipeLength = self._isBulkTotalPipeLengthTypeSelected()

        if not haveTotalPipeLength:
            individualPipeLengthInM = float(lengthText)
            return individualPipeLengthInM

        loopLengthInM = float(lengthText)
        nPipes = len(self._hydraulicLoop.connections)
        individualPipeLengthM = loopLengthInM / nPipes
        return individualPipeLengthM

    def _doesUserSayContinueWithEnablingLoopWideDefaults(self):
        messageBox = _qtw.QMessageBox(self)
        messageBox.setWindowTitle("Do you want to proceed?")
        messageBox.setText(
            "The values of the length, diameter and U-Value for every pipe in the loop will be "
            "lost upon OK'ing the main dialog when enabling loop wide defaults. Do you want to proceed?"
        )
        messageBox.setStandardButtons(messageBox.Yes | messageBox.No)
        pressedButton = messageBox.exec()
        shallContinue = (pressedButton == messageBox.Yes)
        return shallContinue

    def _setUseLoopWideDefaults(self, isSet: bool) -> None:
        self._hydraulicLoop.useLoopWideDefaults = isSet
        self.useLoopWideDefaultsCheckBox.setChecked(isSet)
        isEnabled = not isSet
        self.bulkOperationsGroupBox.setVisible(isEnabled)
        self.pipesGroupBox.setVisible(isEnabled)
        self.adjustSize()

    @classmethod
    def showDialog(
        cls, hydraulicLoop: _gmodel.HydraulicLoop, occupiedNames: _tp.Sequence[str], fluids: _model.Fluids
    ) -> _tp.Literal["oked", "cancelled"]:
        dialog = HydraulicLoopDialog(hydraulicLoop, occupiedNames, fluids)

        dialogCode = dialog.exec()

        if dialogCode == _qtw.QDialog.Accepted:
            return "oked"

        if dialogCode == _qtw.QDialog.Rejected:
            return "cancelled"

        raise AssertionError(f"Unknown dialog code {dialogCode}.")


_PropertyValue = _tp.Union[str, float]


@_dc.dataclass
class _Property:
    header: str
    getter: _tp.Callable[[_gmodel.Connection], _PropertyValue]
    setter: _tp.Optional[_tp.Callable[[_gmodel.Connection, _PropertyValue], None]] = None
    shallHighlightOutliers: bool = True


def _parsePositiveFloat(text: str) -> float:
    value = float(text)

    if value < 0:
        raise ValueError("Value must be positive.")

    return value


def _setConnectionDiameter(connection: _gmodel.Connection, diameterInCmText: _tp.Any) -> None:
    connection.diameterInCm = _parsePositiveFloat(diameterInCmText)


def _setConnectionUValue(connection: _gmodel.Connection, uValueInWPerM2KText: _tp.Any) -> None:
    connection.uValueInWPerM2K = _parsePositiveFloat(uValueInWPerM2KText)


def _setConnectionLength(connection: _gmodel.Connection, lengthInMText: _tp.Any) -> None:
    connection.lengthInM = _parsePositiveFloat(lengthInMText)


class _ConnectionsUiModel(_qtc.QAbstractItemModel):
    c: _gmodel.Connection
    _PROPERTIES = [
        _Property("Name", lambda c: c.name, shallHighlightOutliers=False),
        _Property("Diameter [cm]", lambda c: c.diameterInCm, _setConnectionDiameter),
        _Property("U value [W/(m^2 K)]", lambda c: c.uValueInWPerM2K, _setConnectionUValue),
        _Property("Length [m]", lambda c: c.lengthInM, _setConnectionLength),
    ]

    def __init__(self, connections: _tp.Sequence[_gmodel.Connection]):
        super().__init__()

        self.connections = connections

    def rowCount(self, parent: _qtc.QModelIndex = _qtc.QModelIndex()) -> int:
        if not self._isTopLevel(parent):
            return 0

        return len(self.connections)

    def columnCount(self, parent: _qtc.QModelIndex = _qtc.QModelIndex()) -> int:
        if not self._isTopLevel(parent):
            return 0

        return len(self._headers)

    def headerData(self, section: int, orientation: _qtc.Qt.Orientation, role: int = _qtc.Qt.DisplayRole) -> _tp.Any:
        if role != _qtc.Qt.DisplayRole or orientation != _qtc.Qt.Horizontal:
            return None

        return self._headers[section]

    @property
    def _headers(self) -> _tp.Sequence[str]:
        return [p.header for p in self._PROPERTIES]

    def data(self, modelIndex: _qtc.QModelIndex, role: int = _qtc.Qt.DisplayRole) -> _tp.Any:
        connection, prop = self._getConnectionAndProperty(modelIndex)

        if role == _qtc.Qt.DisplayRole:
            data = prop.getter(connection)  # type: ignore[misc,call-arg]
            return data

        if prop.shallHighlightOutliers and role in [_qtc.Qt.FontRole, _qtc.Qt.ForegroundRole]:
            return self._getHighlightData(connection, prop, role)

        return None

    def _getHighlightData(self, connection: _gmodel.Connection, prop: _Property, role: int) -> _tp.Any:
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

        raise ValueError(f"Role must be {_qtc.Qt.FontRole} or {_qtc.Qt.ForegroundRole}.", role)

    def _getMostUsedValue(self, prop: _Property) -> _PropertyValue:
        sortedValues = sorted(prop.getter(c) for c in self.connections)  # type: ignore[misc, call-arg]
        groupedValues = _it.groupby(sortedValues)
        valuesWithCount = [{"value": v, "count": len(list(vs))} for v, vs in groupedValues]
        mostUsedValueWithCount = max(valuesWithCount, key=lambda vwc: vwc["count"])
        return mostUsedValueWithCount["value"]

    def setData(self, index: _qtc.QModelIndex, value: _tp.Any, role: int = _qtc.Qt.EditRole) -> bool:
        if role != _qtc.Qt.EditRole:
            return False

        connection, prop = self._getConnectionAndProperty(index)

        try:
            prop.setter(connection, value)  # type: ignore[misc]
        except ValueError:
            return False

        self.dataChanged.emit(index, index, [role])

        return True

    def _getConnectionAndProperty(self, modelIndex: _qtc.QModelIndex) -> _tp.Tuple[_gmodel.Connection, _Property]:
        rowIndex = modelIndex.row()
        connection = self.connections[rowIndex]

        propertyIndex = modelIndex.column()
        prop = self._PROPERTIES[propertyIndex]

        return connection, prop

    def flags(self, index: _qtc.QModelIndex) -> _qtc.Qt.ItemFlags:
        parentFlags = super().flags(index)

        if not self._isEditable(index.column()):
            return parentFlags

        return parentFlags | _qtc.Qt.ItemIsEditable  # type: ignore[operator,return-value]

    def _isEditable(self, columnIndex: int) -> bool:
        prop = self._PROPERTIES[columnIndex]
        return bool(prop.setter)

    def index(self, row: int, column: int, parent: _tp.Optional[_qtc.QModelIndex] = None) -> _qtc.QModelIndex:
        assert parent

        if not self._isTopLevel(parent):
            return _qtc.QModelIndex()

        if not 0 <= row < self.rowCount():
            return _qtc.QModelIndex()

        if not 0 <= column < self.columnCount():
            return _qtc.QModelIndex()

        return self.createIndex(row, column)

    def parent(self, _: _qtc.QModelIndex) -> _qtc.QModelIndex:  # type: ignore[override] # pylint: disable=no-self-use
        return _qtc.QModelIndex()

    @staticmethod
    def _isTopLevel(parent: _qtc.QModelIndex) -> bool:
        return not parent.isValid()
