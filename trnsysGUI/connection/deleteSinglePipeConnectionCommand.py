from __future__ import annotations

import typing as _tp

from PyQt5 import QtWidgets as _qtw

import trnsysGUI.hydraulicLoops.model as _hlmodel
import trnsysGUI.hydraulicLoops.split as _hlsplit
import trnsysGUI.hydraulicLoops.merge as _hlmerge
import trnsysGUI.connection.singlePipeConnection as _spc


class DeleteSinglePipeConnectionCommand(_qtw.QUndoCommand):  # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        connection: _spc.SinglePipeConnection,  # type: ignore[name-defined]
        hydraulicLoops: _hlmodel.HydraulicLoops,
        fluids: _tp.Sequence[_hlmodel.Fluid],
        defaultFluid: _hlmodel.Fluid,
    ):
        super().__init__("Delete single pipe connection")
        self._connection: _tp.Optional[_spc.SinglePipeConnection] = connection  # type: ignore[name-defined]
        self._hydraulicLoops = hydraulicLoops
        self._fluids = fluids
        self._defaultFluid = defaultFluid

        self._fromPort = connection.fromPort
        self._toPort = connection.toPort
        self._connectionParent = self._connection.parent

        self._splitSummary: _tp.Optional[_hlsplit.SplitSummary] = None

    def redo(self) -> None:
        assert self._connection

        splitLoopsSummary = self._splitSummary.after if self._splitSummary else None  # pylint: disable=no-member

        cancellable = _hlsplit.split(self._connection, self._hydraulicLoops, self._fluids, splitLoopsSummary)
        if cancellable == "cancelled":
            self.setObsolete(True)
            return
        self._splitSummary = cancellable

        self._connection.deleteConn()
        self._connection = None

    def undo(self) -> None:
        self._connection = _spc.SinglePipeConnection(  # type: ignore[attr-defined]
            self._fromPort, self._toPort, self._connectionParent
        )

        mergedLoopSummary = self._splitSummary.before if self._splitSummary else None  # pylint: disable=no-member

        cancellable = _hlmerge.merge(
            self._connection, self._hydraulicLoops, self._fluids, self._defaultFluid, mergedLoopSummary
        )
        assert cancellable != "cancelled"