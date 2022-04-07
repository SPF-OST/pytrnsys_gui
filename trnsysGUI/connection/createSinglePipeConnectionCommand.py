from __future__ import annotations

import typing as _tp

import PyQt5.QtWidgets as _qtw

import pytrnsys.utils.result as _res

import trnsysGUI.errors as _err
import trnsysGUI.connection.singlePipeConnection as _spc
import trnsysGUI.hydraulicLoops.merge as _hlmerge
import trnsysGUI.hydraulicLoops.split as _hlsplit
import trnsysGUI.singlePipePortItem as _spi

if _tp.TYPE_CHECKING:
    import trnsysGUI.diagram.Editor as _ed


class CreateSinglePipeConnectionCommand(_qtw.QUndoCommand):
    def __init__(
            self,
            fromPort: _spi.SinglePipePortItem,
            toPort: _spi.SinglePipePortItem,
            editor: _ed.Editor,  # type: ignore[name-defined]
    ):
        super().__init__("Create single pipe connection")
        self._fromPort = fromPort
        self._toPort = toPort
        self._editor = editor

        self._connection: _tp.Optional[_spc.SinglePipeConnection] = None
        self._mergeSummary: _tp.Optional[_hlmerge.MergeSummary] = None

    def redo(self):
        self._connection = _spc.SinglePipeConnection(self._fromPort, self._toPort, self._editor)

        mergedLoopSummary = self._mergeSummary.after if self._mergeSummary else None  # pylint: disable=no-member

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
                _err.showErrorMessageBox(error.message, "Cannot create connection")

            self._connection.deleteConn()
            self._connection = None
            self.setObsolete(True)
            return

        mergeSummary = cancellable

        self._mergeSummary = mergeSummary

    def undo(self):
        splitLoopsSummary = self._mergeSummary.before if self._mergeSummary else None  # pylint: disable=no-member

        cancellable = _hlsplit.split(
            self._connection, self._editor.hydraulicLoops, self._editor.fluids.fluids, splitLoopsSummary
        )
        assert cancellable != "cancelled"

        self._connection.deleteConn()
        self._connection = None
