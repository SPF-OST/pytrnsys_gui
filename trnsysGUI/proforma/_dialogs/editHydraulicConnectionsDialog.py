import collections.abc as _cabc

import PyQt5.QtWidgets as _qtw

import trnsysGUI.common as _com
import trnsysGUI.common.cancelled as _cancel
import trnsysGUI.dialogs as _dlgs
from .. import modelConnection as _mc

_dlgs.assertThatLocalGeneratedUIModuleAndResourcesExist(__name__, moduleName="_UI_hydraulicConnections_generated")

from . import _UI_hydraulicConnections_generated as _uigen  # type: ignore[import]  # pylint: disable=wrong-import-position


class _ConnectionListItem(_qtw.QListWidgetItem):
    def __init__(self, connection: _mc.Connection) -> None:
        super().__init__()

        self.connection = connection
        self.setText(connection.name)

    @staticmethod
    def create() -> "_ConnectionListItem":
        connection = _mc.Connection.createEmpty()
        return _ConnectionListItem(connection)


class EditHydraulicConnectionsDialog(_qtw.QDialog, _uigen.Ui_HydraulicConnections):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)
