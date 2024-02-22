from __future__ import annotations

import typing as _tp

import PyQt5.QtWidgets as _qtw

import trnsysGUI.connection.undo as _cundo
import trnsysGUI.names.undo as _nu

if _tp.TYPE_CHECKING:
    import trnsysGUI.connection.doublePipeConnection as _dpc


class DeleteDoublePipeConnectionCommand(_qtw.QUndoCommand):
    def __init__(
        self,
        doublePipeConnection: _dpc.DoublePipeConnection,
        undoNamingHelper: _nu.UndoNamingHelper,
        parentCommand: _tp.Optional[_qtw.QUndoCommand] = None,
    ) -> None:
        super().__init__("Delete double pipe connection", parentCommand)
        self._undoNamingHelper = undoNamingHelper
        self._connection = doublePipeConnection

    def undo(self):
        _cundo.setDisplayNameForReAdd(self._connection, self._undoNamingHelper)
        _cundo.reAddConnection(self._connection)

    def redo(self):
        self._connection.deleteConnection()
        self._undoNamingHelper.removeNameForDelete(self._connection.displayName)
