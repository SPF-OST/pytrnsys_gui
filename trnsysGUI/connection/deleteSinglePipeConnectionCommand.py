from __future__ import annotations

import typing as _tp

from PyQt5 import QtWidgets as _qtw

import pytrnsys.utils.result as _res
import trnsysGUI.connection.singlePipeConnection as _spc  # pylint: disable=cyclic-import
import trnsysGUI.connection.undo as _cundo
import trnsysGUI.hydraulicLoops.merge as _hlmerge  # pylint: disable=cyclic-import
import trnsysGUI.hydraulicLoops.model as _hlmodel
import trnsysGUI.hydraulicLoops.split as _hlsplit  # pylint: disable=cyclic-import
import trnsysGUI.names.undo as _un


class DeleteSinglePipeConnectionCommand(_qtw.QUndoCommand):  # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        connection: _spc.SinglePipeConnection,
        undoNamingHelper: _un.UndoNamingHelper,
        hydraulicLoops: _hlmodel.HydraulicLoops,
        fluids: _tp.Sequence[_hlmodel.Fluid],
        defaultFluid: _hlmodel.Fluid,
        scene: _qtw.QGraphicsScene,
        parentCommand: _tp.Optional[_qtw.QUndoCommand],
    ):
        super().__init__("Delete single pipe connection", parentCommand)
        self._connection = connection

        self._undoNamingHelper = undoNamingHelper

        self._hydraulicLoops = hydraulicLoops
        self._fluids = fluids
        self._defaultFluid = defaultFluid

        self._scene = scene

        self._splitSummary: _tp.Optional[_hlsplit.SplitSummary] = None

    def redo(self) -> None:
        assert self._connection

        splitLoopsSummary = self._splitSummary.after if self._splitSummary else None  # pylint: disable=no-member

        cancellable = _hlsplit.split(self._connection, self._hydraulicLoops, self._fluids, splitLoopsSummary)
        if cancellable == "cancelled":
            self.setObsolete(True)
            return
        self._splitSummary = cancellable

        self._scene.removeItem(self._connection)
        self._connection.deleteConnection()
        self._undoNamingHelper.removeNameForDelete(self._connection.displayName)

    def undo(self) -> None:
        mergedLoopSummary = self._splitSummary.before if self._splitSummary else None  # pylint: disable=no-member

        cancellable = _hlmerge.merge(
            self._connection, self._hydraulicLoops, self._fluids, self._defaultFluid, mergedLoopSummary
        )
        assert cancellable != "cancelled" and not _res.isError(cancellable)

        _cundo.setDisplayNameForReAdd(self._connection, self._undoNamingHelper)
        _cundo.reAddConnection(self._connection)
        self._scene.addItem(self._connection)
