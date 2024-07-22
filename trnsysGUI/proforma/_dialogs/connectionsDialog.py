import collections.abc as _cabc

import PyQt5.QtWidgets as _qtw
import PyQt5.QtCore as _qtc

import trnsysGUI.common as _com
import trnsysGUI.common.cancelled as _cancel
import trnsysGUI.dialogs as _dlgs


from .. import models as _models

_dlgs.assertThatLocalGeneratedUIModuleAndResourcesExist(__name__)

from . import _UI_connections_generated as _uigen  # type: ignore[import]  # pylint: disable=wrong-import-position


class _ConnectionListItem(_qtw.QListWidgetItem):
    def __init__(self, connection: _models.Connection) -> None:
        super().__init__()

        self.connection = connection
        self.setText(connection.name)

    @staticmethod
    def create() -> "_ConnectionListItem":
        connection = _models.Connection.createEmpty()
        return _ConnectionListItem(connection)


class ConnectionsDialog(_qtw.QDialog, _uigen.Ui_HydraulicConnections):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)

        self.connectionsListWidget.setSelectionMode(_qtw.QListWidget.SelectionMode.SingleSelection)
        self.connectionsListWidget.itemSelectionChanged.connect(self._onSelectionChanged)

        self.addConnectionButton.clicked.connect(self._onAddConnection)
        self.removeConnectionButton.clicked.connect(self._onRemoveConnection)

    def _onSelectionChanged(self) -> None:
        selectedItems = self.connectionsListWidget.selectedItems()

        isItemSelected = bool(selectedItems)

        self.editConnectionButton.setEnabled(isItemSelected)
        self.removeConnectionButton.setEnabled(isItemSelected)

    def _onAddConnection(self) -> None:
        listItem = _ConnectionListItem.create()
        self.connectionsListWidget.addItem(listItem)

    def _onRemoveConnection(self) -> None:
        selectedItem = self._getSelectedConnectionListItem()
        self.connectionsListWidget.removeItemWidget(selectedItem)

    def _getSelectedConnectionListItem(self) -> _ConnectionListItem:
        selectedItems = self.connectionsListWidget.selectedItems()
        selectedItem = _com.getSingle(selectedItems)
        return selectedItem

    @staticmethod
    def showDialogAndGetResults() -> _cancel.MaybeCancelled[_cabc.Set[_models.Connection]]:
        connectionsDialog = ConnectionsDialog()
        returnValue = connectionsDialog.exec()

        if returnValue == _qtw.QDialogButtonBox.StandardButton.Cancel:
            return _cancel.CANCELLED

        connectionListWidget = connectionsDialog.connectionsListWidget
        connections = {connectionListWidget.item(r) for r in range(connectionListWidget.count())}

        return connections
