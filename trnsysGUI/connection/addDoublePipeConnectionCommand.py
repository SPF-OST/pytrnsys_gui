from __future__ import annotations

import typing as _tp

import PyQt5.QtWidgets as _qtw

import trnsysGUI.connection.doublePipeConnection as _dpc
import trnsysGUI.connection.undo as _cundo
import trnsysGUI.names.undo as _nu

if _tp.TYPE_CHECKING:  # pragma: no cover
    import trnsysGUI.diagram.Editor as _ed


class AddDoublePipeConnectionCommand(_qtw.QUndoCommand):
    def __init__(
        self,
        connection: _dpc.DoublePipeConnection,
        undoNamingHelper: _nu.UndoNamingHelper,
        editor: _ed.Editor,  # type: ignore[name-defined]
    ) -> None:
        super().__init__("Create double pipe connection")
        self._connection = connection
        self._undoNamingHelper = undoNamingHelper
        self._editor = editor

    def redo(self):
        _cundo.setDisplayNameForReAdd(self._connection, self._undoNamingHelper)
        _cundo.reAddConnection(self._connection)
        self._editor.diagramScene.addItem(self._connection)

    def undo(self):
        self._editor.diagramScene.removeItem(self._connection)
        self._connection.deleteConnection()
        self._undoNamingHelper.removeNameForDelete(
            self._connection.displayName
        )
