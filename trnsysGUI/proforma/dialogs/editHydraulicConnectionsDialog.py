import collections.abc as _cabc
import copy as _copy

import PyQt5.QtCore as _qtc
import PyQt5.QtWidgets as _qtw

import trnsysGUI.common as _com
import trnsysGUI.common.cancelled as _cancel
import trnsysGUI.dialogs as _dlgs
from .. import models as _models

_dlgs.assertThatLocalGeneratedUIModuleAndResourcesExist(__name__, moduleName="_UI_hydraulicConnections_generated")

from . import _UI_hydraulicConnections_generated as _uigen  # type: ignore[import]  # pylint: disable=wrong-import-position


class _OnActivatedCallBack:
    def __init__(self, dialog: "EditHydraulicConnectionsDialog", comboBox: _qtw.QComboBox) -> None:
        self._dialog = dialog
        self._comboBox = comboBox

    @staticmethod
    def createAndConnect(dialog: "EditHydraulicConnectionsDialog", comboBox: _qtw.QComboBox) -> "_OnActivatedCallBack":
        callback = _OnActivatedCallBack(dialog, comboBox)
        comboBox.activated.connect(callback.onActivated)
        return callback

    def onActivated(self, newIndex: int) -> None:
        self._dialog.onComboBoxActivated(self._comboBox, newIndex)


class EditHydraulicConnectionsDialog(_qtw.QDialog, _uigen.Ui_HydraulicConnections):
    _DEFAULT_CONNECTION_LABEL = "<Default connection>"

    def __init__(
        self,
        suggestedHydraulicConnections: _cabc.Sequence[_models.Connection],
        variablesByRole: _models.VariablesByRole,
    ) -> None:
        super().__init__()
        self.setupUi(self)

        self._variablesByRole = variablesByRole
        self.hydraulicConnections = self._getDeepCopiesSortedByName(suggestedHydraulicConnections)

        self._onActivatedCallbacks = list[_OnActivatedCallBack]()

        self.summaryTextEdit.setReadOnly(True)

        self._configureButtonBox()
        self._configureHydraulicConnections()
        self._configureComboBoxes()

        self._reloadConnections()

    def _configureButtonBox(self) -> None:
        self.okCancelButtonBox.accepted.connect(self.accept)
        self.okCancelButtonBox.rejected.connect(self.reject)

    @staticmethod
    def _getDeepCopiesSortedByName(suggestedHydraulicConnections):
        hydraulicConnections = [_copy.deepcopy(c) for c in suggestedHydraulicConnections]

        def getConnectionName(connection: _models.Connection) -> str:
            return connection.name or ""

        sortedHydraulicConnections = sorted(hydraulicConnections, key=getConnectionName)
        return sortedHydraulicConnections

    def _configureHydraulicConnections(self):
        self.connectionsListWidget.setSelectionMode(_qtw.QAbstractItemView.SingleSelection)

        for hydraulicConnection in self.hydraulicConnections:
            name = hydraulicConnection.name if hydraulicConnection.name else self._DEFAULT_CONNECTION_LABEL
            item = _qtw.QListWidgetItem(name)
            item.setData(_qtc.Qt.UserRole, hydraulicConnection)
            self.connectionsListWidget.addItem(item)

        self.connectionsListWidget.setCurrentRow(0)

        self.connectionsListWidget.itemSelectionChanged.connect(self._onSelectedConnectionChanged)

    def _onSelectedConnectionChanged(self) -> None:
        self._reconfigureGroupBoxLabels()
        self._reloadSelectedComboBoxItems()

    def _reconfigureGroupBoxLabels(self) -> None:
        selectedConnection = self._getSelectedConnection()

        connectionGroupBoxLabel = (
            f'"{selectedConnection.name}"' if selectedConnection.name else self._DEFAULT_CONNECTION_LABEL
        )
        connectionGroupBoxTitle = f"Hydraulic connection {connectionGroupBoxLabel}"
        self.hydraulicConnectionGroupBox.setTitle(connectionGroupBoxTitle)

        self.inletPortGroupBox.setTitle(f'Inlet port "{selectedConnection.inputPort.name}"')

        self.outletPortGroupBox.setTitle(f'Outlet port "{selectedConnection.outputPort.name}"')

    def _reconfigureComboBoxOptions(self) -> None:
        self._reconfigureFluid()
        self._reconfigureInputs()
        self._reconfigureOutputs()

    def _reconfigureFluid(self):
        self._addParametersAndInputOptions(self.fluidDensityComboBox)
        self._addParametersAndInputOptions(self.fluidHeatCapacityComboBox)

    def _addParametersAndInputOptions(self, comboBox: _qtw.QComboBox) -> None:
        self._addOptions(comboBox, self._getParameters(comboBox))
        comboBox.addItem("-----", _models.UNSET)
        self._addOptions(comboBox, self._getInputs(comboBox), withUnset=False, clear=False)

    def _reconfigureInputs(self) -> None:
        self._addOptions(self.massFlowRateComboBox, self._getInputs(self.massFlowRateComboBox))
        self._addOptions(self.inputTempComboBox, self._getInputs(self.inputTempComboBox))

    def _reconfigureOutputs(self) -> None:
        self._addOptions(self.outputTempComboBox, self._getOutputs(self.outputTempComboBox))
        self._addOptions(self.outputRevTempComboBox, self._getInputs(self.outputRevTempComboBox))

    @staticmethod
    def _addOptions(
        comboBox: _qtw.QComboBox,
        variables: _cabc.Sequence[_models.Variable],
        withUnset: bool = True,
        clear: bool = True,
    ) -> None:
        if clear:
            comboBox.clear()

        if withUnset:
            comboBox.addItem("", _models.UNSET)

        for variable in variables:
            text = variable.getInfo(withRole=True)
            comboBox.addItem(text, variable)

    @property
    def _selectedVariables(self) -> _cabc.Sequence[_models.Variable]:
        selectedVariables = [v for c in self.hydraulicConnections for v in c.allVariables]
        return selectedVariables

    def _getParameters(self, comboBox: _qtw.QComboBox) -> _cabc.Sequence[_models.Variable]:
        return self._removeSelectedVariablesOfOtherComboBoxes(comboBox, self._variablesByRole.parameters)

    def _getInputs(self, comboBox: _qtw.QComboBox) -> _cabc.Sequence[_models.Variable]:
        return self._removeSelectedVariablesOfOtherComboBoxes(comboBox, self._variablesByRole.inputs)

    def _getOutputs(self, comboBox: _qtw.QComboBox) -> _cabc.Sequence[_models.Variable]:
        return self._removeSelectedVariablesOfOtherComboBoxes(comboBox, self._variablesByRole.outputs)

    def _removeSelectedVariablesOfOtherComboBoxes(
        self, comboBox: _qtw.QComboBox, variables: _cabc.Sequence[_models.Variable]
    ) -> _cabc.Sequence[_models.Variable]:
        selectedVariableForComboBox = self._getVariableCorrespondingToComboBox(comboBox)
        selectedOrOtherUnselectedVariables = [
            v for v in variables if v == selectedVariableForComboBox or v not in self._selectedVariables
        ]
        return selectedOrOtherUnselectedVariables

    def _getVariableCorrespondingToComboBox(self, comboBox: _qtw.QComboBox) -> _models.Variable | _models.Unset:
        selectedConnection = self._getSelectedConnection()

        if comboBox == self.fluidDensityComboBox:
            return selectedConnection.fluid.density or _models.UNSET
        if comboBox == self.fluidHeatCapacityComboBox:
            return selectedConnection.fluid.heatCapacity or _models.UNSET
        if comboBox == self.massFlowRateComboBox:
            return selectedConnection.inputPort.massFlowRate
        if comboBox == self.inputTempComboBox:
            return selectedConnection.inputPort.temperature
        if comboBox == self.outputTempComboBox:
            return selectedConnection.outputPort.temperature
        if comboBox == self.outputRevTempComboBox:
            return selectedConnection.outputPort.reverseTemperature or _models.UNSET

        raise AssertionError("Unknown combo box.")

    def _getSelectedConnection(self) -> _models.Connection:
        selectedItems = self.connectionsListWidget.selectedItems()
        selectedItem = _com.getSingle(selectedItems)
        selectedConnection = selectedItem.data(_qtc.Qt.UserRole)
        assert isinstance(selectedConnection, _models.Connection)
        return selectedConnection

    def _configureComboBoxes(self) -> None:
        for comboBox in self._comboBoxes:
            onActivatedCallback = _OnActivatedCallBack.createAndConnect(self, comboBox)
            self._onActivatedCallbacks.append(onActivatedCallback)

    def onComboBoxActivated(self, comboBox: _qtw.QComboBox, newIndex: int) -> None:
        data = comboBox.itemData(newIndex)
        self._setVariableCorrespondingToComboBox(comboBox, data)
        self._reloadConnections()

    def _reloadConnections(self) -> None:
        self._resetOkButton()
        self._reloadSelectedComboBoxItems()
        self._reloadSummaryText()

    def _reloadSummaryText(self) -> None:
        overallSummary = "\n".join(s for c in self.hydraulicConnections if (s := c.getSummary()))
        self.summaryTextEdit.setPlainText(overallSummary)

    def _resetOkButton(self) -> None:
        okButton = self.okCancelButtonBox.button(_qtw.QDialogButtonBox.Ok)
        areAnyRequiredVariablesUnset = self._areAnyRequiredVariablesUnset()
        isEnabled = not areAnyRequiredVariablesUnset
        okButton.setEnabled(isEnabled)
        toolTip = (
            "Please specify the required properties (in bold) for all connections."
            if areAnyRequiredVariablesUnset
            else ""
        )
        okButton.setToolTip(toolTip)

    def _areAnyRequiredVariablesUnset(self) -> bool:
        areAnyRequiredVariablesUnset = any(c.areAnyRequiredVariablesUnset for c in self.hydraulicConnections)
        return areAnyRequiredVariablesUnset

    def _reloadSelectedComboBoxItems(self) -> None:
        self._reconfigureComboBoxOptions()

        for comboBox in self._comboBoxes:
            data = self._getVariableCorrespondingToComboBox(comboBox)
            _setSelected(comboBox, data)

    @property
    def _comboBoxes(self) -> _cabc.Sequence[_qtw.QComboBox]:
        return [
            self.fluidDensityComboBox,
            self.fluidHeatCapacityComboBox,
            self.massFlowRateComboBox,
            self.inputTempComboBox,
            self.outputTempComboBox,
            self.outputRevTempComboBox,
        ]

    def _setVariableCorrespondingToComboBox(
        self, comboBox: _qtw.QComboBox, value: _models.Variable | _models.Unset
    ) -> None:
        selectedConnection = self._getSelectedConnection()

        valueForOptionalVariables = value if isinstance(value, _models.Variable) else None

        if comboBox == self.fluidDensityComboBox:
            selectedConnection.fluid.density = valueForOptionalVariables
        elif comboBox == self.fluidHeatCapacityComboBox:
            selectedConnection.fluid.heatCapacity = valueForOptionalVariables
        elif comboBox == self.massFlowRateComboBox:
            selectedConnection.inputPort.massFlowRate = value
        elif comboBox == self.inputTempComboBox:
            selectedConnection.inputPort.temperature = value
        elif comboBox == self.outputTempComboBox:
            selectedConnection.outputPort.temperature = value
        elif comboBox == self.outputRevTempComboBox:
            selectedConnection.outputPort.reverseTemperature = valueForOptionalVariables
        else:
            raise AssertionError("Unknown combo box.")

    @staticmethod
    def showDialogAndGetResults(
        suggestedHydraulicConnections: _cabc.Sequence[_models.Connection],
        variablesByRole: _models.VariablesByRole,
    ) -> _cancel.MaybeCancelled[_cabc.Sequence[_models.Connection]]:
        dialog = EditHydraulicConnectionsDialog(suggestedHydraulicConnections, variablesByRole)
        returnValue = dialog.exec()

        if returnValue == _qtw.QDialog.Rejected:
            return _cancel.CANCELLED

        return dialog.hydraulicConnections


def _setSelected(comboBox: _qtw.QComboBox, data: _models.Variable | _models.Unset) -> None:
    # Cannot use `QComboBox.findData` as `findData` works by reference, but we want by value
    for index in range(comboBox.count()):
        rowData = comboBox.itemData(index)
        if rowData == data:
            comboBox.setCurrentIndex(index)
            return

    raise AssertionError(f"{data} not a member of combo box.")