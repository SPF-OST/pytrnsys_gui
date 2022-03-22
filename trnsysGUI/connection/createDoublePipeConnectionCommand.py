from __future__ import annotations

import typing as _tp

import PyQt5.QtWidgets as _qtw

import trnsysGUI.connection.doublePipeConnection as _dpc
import trnsysGUI.doublePipePortItem as _dpi

if _tp.TYPE_CHECKING:
    import trnsysGUI.diagram.Editor as _ed


class CreateDoublePipeConnectionCommand(_qtw.QUndoCommand):
    def __init__(
            self,
            fromPort: _dpi.DoublePipePortItem,
            toPort: _dpi.DoublePipePortItem,
            editor: _ed.Editor,  # type: ignore[name-defined]
    ) -> None:
        super().__init__("Create double pipe connection")
        self._fromPort = fromPort
        self._toPort = toPort
        self._editor = editor
        self._connection = None

    def redo(self):
        self._connection = _dpc.DoublePipeConnection(self._fromPort, self._toPort, self._editor)

    def undo(self):
        self._connection.deleteConn()
        self._connection = None
