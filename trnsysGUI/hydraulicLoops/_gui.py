__all__ = ["HydraulicLoopDialog"]

import dataclasses as _dc
import itertools as _it
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

try:
    from . import _UI_hydraulicLoopDialog_generated as _uigen
except ImportError as importError:
    raise AssertionError(
        "Could not find the generated Python code for a .ui file. Please run the "
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

        self._configureFluidComboBox()

        connectionsModel = _ConnectionsUiModel(hydraulicLoop.connections)
        self.connectionsTableView.setModel(connectionsModel)

        self.connectionsTableView.resizeRowsToContents()
        self.connectionsTableView.resizeColumnsToContents()

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


def _setConnectionDiameter(connection: _model.Connection, diameterInCm: _tp.Any) -> None:
    connection.diameterInCm = float(diameterInCm)


def _setConnectionUValue(connection: _model.Connection, uValueInWPerM2K: _tp.Any) -> None:
    connection.uValueInWPerM2K = float(uValueInWPerM2K)


class _ConnectionsUiModel(_qtc.QAbstractItemModel):
    _PROPERTIES = [
        _Property("Name", lambda c: c.name, shallHighlightOutliers=False),
        _Property("Diameter [cm]", lambda c: c.diameterInCm, _setConnectionDiameter),
        _Property("U value [W/(m^2 K)]", lambda c: c.uValueInWPerM2K, _setConnectionUValue),
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

    def _getMostUsedValue(self, prop):
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
