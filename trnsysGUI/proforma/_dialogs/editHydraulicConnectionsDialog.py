import collections.abc as _cabc
import copy as _copy

import PyQt5.QtWidgets as _qtw

import trnsysGUI.common.cancelled as _cancel
import trnsysGUI.dialogs as _dlgs
from .. import models as _models

_dlgs.assertThatLocalGeneratedUIModuleAndResourcesExist(__name__, moduleName="_UI_hydraulicConnections_generated")

from . import _UI_hydraulicConnections_generated as _uigen  # type: ignore[import]  # pylint: disable=wrong-import-position


class EditHydraulicConnectionsDialog(_qtw.QDialog, _uigen.Ui_HydraulicConnections):

    def __init__(
        self,
        suggestedHydraulicConnections: _cabc.Sequence[_models.Connection],
        variablesByRole: _models.VariablesByRole,
    ) -> None:
        super().__init__()
        self.setupUi(self)

        self._variablesByRole = variablesByRole
        self.hydraulicConnections = self._getDeepCopiesSortedByName(suggestedHydraulicConnections)

        self._comboboxOptionsSeparator = object()

        self._configureFluid()
        self._configureInputs()
        self._configureOutputs()

    def _configureFluid(self):
        self._addParametersAndInputOptions(self.fluidDensityComboBox)
        self._addParametersAndInputOptions(self.fluidHeatCapacityComboBox)

    def _addParametersAndInputOptions(self, comboBox):
        self._addOptions(comboBox, self._variablesByRole.parameters)
        comboBox.addItem("-----", self._comboboxOptionsSeparator)
        self._addOptions(comboBox, self._variablesByRole.inputs, withUnset=False)

    def _configureInputs(self) -> None:
        self._addOptions(self.massFlowRateComboBox, self._variablesByRole.inputs)
        self._addOptions(self.inputTempComboBox, self._variablesByRole.inputs)

    def _configureOutputs(self) -> None:
        self._addOptions(self.outputTempComboBox, self._variablesByRole.outputs)
        self._addOptions(self.outputRevTempComboBox, self._variablesByRole.inputs)

    @staticmethod
    def _addOptions(
        comboBox: _qtw.QComboBox, variables: _cabc.Sequence[_models.Variable], withUnset: bool = True
    ) -> None:
        if withUnset:
            comboBox.addItem("", _models.UNSET)

        for variable in variables:
            text = variable.getInfo(withRole=True)
            comboBox.addItem(text, variable)

    @staticmethod
    def _getDeepCopiesSortedByName(suggestedHydraulicConnections):
        hydraulicConnections = [_copy.deepcopy(c) for c in suggestedHydraulicConnections]

        def getConnectionName(connection: _models.Connection) -> str:
            return connection.name

        sortedHydraulicConnections = sorted(hydraulicConnections, key=getConnectionName)
        return sortedHydraulicConnections

    @staticmethod
    def showDialogAndGetResults(
        suggestedHydraulicConnections: _cabc.Sequence[_models.Connection],
        variablesByRole: _models.VariablesByRole,
    ) -> _cancel.MaybeCancelled[_cabc.Sequence[_models.Connection]]:
        dialog = EditHydraulicConnectionsDialog(suggestedHydraulicConnections, variablesByRole)
        dialog.exec()
        return _cancel.CANCELLED
