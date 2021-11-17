__all__ = ["HydraulicLoopDialog"]

import dataclasses as _dc
import itertools as _it
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

try:
    from . import _UI_hydraulicLoopDialog_generated as _uigen
    import trnsysGUI.resources.QRC_resources_generated as _
except ImportError as importError:
    raise AssertionError(
        "Could not find the generated Python code for a .ui or .qrc file. Please run the "
        "`dev-tools\\generateGuiClassesFromQtCreatorStudioUiFiles.py' script from your "
        "`pytrnsys_gui` directory."
    ) from importError

from . import _model


class HydraulicLoopDialog(_qtw.QDialog, _uigen.Ui_hydraulicLoopDialog):
    def __init__(self, hydraulicLoop: _model.HydraulicLoop):
        super().__init__()
        self.setupUi(self)

        self.hydraulicLoop = hydraulicLoop

        self.loopName.setText(hydraulicLoop.name)

        self._configureBulkOperations()

        self._configureFluidComboBox()

        self._reloadConnections()

    def _configureBulkOperations(self):
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

            for connection in self.hydraulicLoop.connections:
                if individualPipeLengthInM is not None:
                    connection.lengthInM = individualPipeLengthInM

                if diameterInCm is not None:
                    connection.diameterInCm = diameterInCm

                if uValueInWPerM2K is not None:
                    connection.uValueInWPerM2K = uValueInWPerM2K

            self._reloadConnections()

        self.bulkApplyButton.pressed.connect(onBulkApplyButtonPressed)

        def clearLineEdits() -> None:
            self.bulkLengthLineEdit.clear()
            self.bulkDiameterLineEdit.clear()
            self.bulkUValueLineEdit.clear()

        self.bulkCancelButton.pressed.connect(clearLineEdits)

        self._configureForPositiveFloat(self.bulkLengthLineEdit)
        self._configureForPositiveFloat(self.bulkDiameterLineEdit)
        self._configureForPositiveFloat(self.bulkUValueLineEdit)

    def _isBulkTotalPipeLengthTypeSelected(self):
        text = self.bulkLengthTypeComboBox.currentText()

        if text == "Individual pipe length":
            return False

        if text == "Total loop length":
            return True

        raise AssertionError(f"Unknown bulk length type text: {text}")

    @staticmethod
    def _configureForPositiveFloat(lineEdit: _qtw.QLineEdit):
        def checkIfTextIsPositiveFloatOrReset() -> None:
            text = lineEdit.text()
            try:
                _parsePositiveFloat(text)
            except ValueError:
                lineEdit.setText("")

        lineEdit.editingFinished.connect(checkIfTextIsPositiveFloatOrReset)

    def _reloadConnections(self):
        connectionsModel = _ConnectionsUiModel(self.hydraulicLoop.connections)

        connectionsModel.dataChanged.connect(lambda *_: self._updatePipesStatisticsLabel())

        self.connectionsTableView.setModel(connectionsModel)

        self.connectionsTableView.resizeRowsToContents()
        self.connectionsTableView.resizeColumnsToContents()

        self._updatePipesStatisticsLabel()

    def _updatePipesStatisticsLabel(self):
        totalLoopLengthInM = sum(c.lengthInM for c in self.hydraulicLoop.connections)
        statisticsLabelText = (
            f"Number of pipes: {len(self.hydraulicLoop.connections)}, total loop length: {totalLoopLengthInM:g} m"
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
        nPipes = len(self.hydraulicLoop.connections)
        individualPipeLengthM = loopLengthInM / nPipes
        return individualPipeLengthM

    def _configureFluidComboBox(self):
        def getFluidName(_fluid: _model.Fluid) -> str:
            return _fluid.name

        sortedFluids: _tp.Sequence[_model.Fluid] = sorted(_model.PredefinedFluids.getAllFluids(), key=getFluidName)
        for fluid in sortedFluids:
            self.fluidComboBox.addItem(fluid.name, userData=fluid)

        def onCurrentIndexChanged(_) -> None:
            self.hydraulicLoop.fluid = self.fluidComboBox.currentData()

        self.fluidComboBox.currentIndexChanged.connect(onCurrentIndexChanged)

    @staticmethod
    def showDialog(hydraulicLoop: _model.HydraulicLoop) -> _tp.Literal["oked", "cancelled"]:
        dialog = HydraulicLoopDialog(hydraulicLoop)

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
    getter: _tp.Callable[[_model.Connection], _PropertyValue]
    setter: _tp.Optional[_tp.Callable[[_model.Connection, _PropertyValue], None]] = None
    shallHighlightOutliers: bool = True


def _parsePositiveFloat(text: str) -> float:
    value = float(text)

    if value < 0:
        raise ValueError("Value must be positive.")

    return value


def _setConnectionDiameter(connection: _model.Connection, diameterInCmText: _tp.Any) -> None:
    connection.diameterInCm = _parsePositiveFloat(diameterInCmText)


def _setConnectionUValue(connection: _model.Connection, uValueInWPerM2KText: _tp.Any) -> None:
    connection.uValueInWPerM2K = _parsePositiveFloat(uValueInWPerM2KText)


def _setConnectionLength(connection: _model.Connection, lengthInMText: _tp.Any) -> None:
    connection.lengthInM = _parsePositiveFloat(lengthInMText)


class _ConnectionsUiModel(_qtc.QAbstractItemModel):
    c: _model.Connection
    _PROPERTIES = [
        _Property("Name", lambda c: c.name, shallHighlightOutliers=False),
        _Property("Diameter [cm]", lambda c: c.diameterInCm, _setConnectionDiameter),
        _Property("U value [W/(m^2 K)]", lambda c: c.uValueInWPerM2K, _setConnectionUValue),
        _Property("Length [m]", lambda c: c.lengthInM, _setConnectionLength),
    ]

    def __init__(self, connections: _tp.Sequence[_model.Connection]):
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

    def _getHighlightData(self, connection, prop, role):
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

    def _getMostUsedValue(self, prop: _Property):
        sortedValues = sorted(prop.getter(c) for c in self.connections)
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

    def _getConnectionAndProperty(self, modelIndex: _qtc.QModelIndex) -> _tp.Tuple[_model.Connection, _Property]:
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

    def index(self, row: int, column: int, parent: _qtc.QModelIndex = None) -> _qtc.QModelIndex:
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
    def _isTopLevel(parent):
        return not parent.isValid()
