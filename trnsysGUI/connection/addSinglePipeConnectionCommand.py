from __future__ import annotations

import typing as _tp

import PyQt5.QtWidgets as _qtw
import pytrnsys.utils.result as _res

import trnsysGUI.connection.singlePipeConnection as _spc
import trnsysGUI.connection.undo as _cundo
import trnsysGUI.hydraulicLoops.merge as _hlmerge
import trnsysGUI.hydraulicLoops.split as _hlsplit
import trnsysGUI.names.undo as _nu
import trnsysGUI.warningsAndErrors as _werrors

if _tp.TYPE_CHECKING:
    import trnsysGUI.diagram.Editor as _ed


class AddSinglePipeConnectionCommand(_qtw.QUndoCommand):
    def __init__(
        self,
        connection: _spc.SinglePipeConnection,
        undoNamingHelper: _nu.UndoNamingHelper,
        editor: _ed.Editor,  # type: ignore[name-defined]
    ):
        super().__init__("Create single pipe connection")
        self._connection = connection
        self._undoNamingHelper = undoNamingHelper
        self._editor = editor

        self._mergeSummary: _tp.Optional[_hlmerge.MergeSummary] = None

    def redo(self):
        mergedLoopSummary = (
            self._mergeSummary.after if self._mergeSummary else None
        )  # pylint: disable=no-member

        cancellable = _hlmerge.merge(
            self._connection,
            self._editor.hydraulicLoops,
            self._editor.fluids.fluids,
            self._editor.fluids.WATER,
            mergedLoopSummary,
        )
        if cancellable == "cancelled" or _res.isError(cancellable):
            if _res.isError(cancellable):
                error = _res.error(cancellable)
                _werrors.showMessageBox(
                    error.message, "Cannot create connection"
                )

            self.setObsolete(True)
            return

        mergeSummary = cancellable

        self._mergeSummary = mergeSummary

        _cundo.setDisplayNameForReAdd(self._connection, self._undoNamingHelper)
        _cundo.reAddConnection(self._connection)
        self._editor.diagramScene.addItem(self._connection)

    def undo(self):
        splitLoopsSummary = (
            self._mergeSummary.before if self._mergeSummary else None
        )  # pylint: disable=no-member

        cancellable = _hlsplit.split(
            self._connection,
            self._editor.hydraulicLoops,
            self._editor.fluids.fluids,
            splitLoopsSummary,
        )
        assert cancellable != "cancelled"

        self._editor.diagramScene.removeItem(self._connection)
        self._connection.deleteConnection()
        self._undoNamingHelper.removeNameForDelete(
            self._connection.displayName
        )
