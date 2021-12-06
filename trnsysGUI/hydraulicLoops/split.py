from __future__ import annotations

import dataclasses as _dc
import typing as _tp

from . import _helpers
from . import _search
from . import common as _common
from . import model as _model
from ._dialogs.split import dialog as _dialog

if _tp.TYPE_CHECKING:
    import trnsysGUI.connection.singlePipeConnection as _spc


@_dc.dataclass
class SplitSummary:
    before: _common.MergedLoopSummary
    after: _common.SplitLoopsSummary

    @staticmethod
    def fromLoops(
        mergedLoop: _model.HydraulicLoop, fromLoop: _model.HydraulicLoop, toLoop: _model.HydraulicLoop
    ) -> "SplitSummary":
        mergedLoopSummary = _common.MergedLoopSummary.fromLoop(mergedLoop)
        splitLoopsSummary = _common.SplitLoopsSummary.fromLoops(fromLoop, toLoop)
        return SplitSummary(mergedLoopSummary, splitLoopsSummary)


def split(
    connection: _spc.SinglePipeConnection,  # type: ignore[name-defined]
    hydraulicLoops: _model.HydraulicLoops,
    fluids: _tp.Sequence[_model.Fluid],
    splitLoopsSummary: _tp.Optional[_common.SplitLoopsSummary],
) -> _common.Cancellable[_tp.Optional[SplitSummary]]:
    splitter = _Splitter(hydraulicLoops, fluids)

    return splitter.split(connection, splitLoopsSummary)


class _Splitter:
    def __init__(self, hydraulicLoops: _model.HydraulicLoops, fluids: _tp.Sequence[_model.Fluid]) -> None:
        self._hydraulicLoops = hydraulicLoops
        self._fluids = fluids

    def split(
        self,
        connection: _spc.SinglePipeConnection,  # type: ignore[name-defined]
        splitLoopsSummary: _tp.Optional[_common.SplitLoopsSummary] = None,
    ) -> _common.Cancellable[_tp.Optional[SplitSummary]]:
        fromPort, toPort = _helpers.getFromAndToPort(connection)

        fromConnections = _search.getReachableConnections(fromPort, ignoreConnections={connection})
        toConnections = _search.getReachableConnections(toPort, ignoreConnections={connection})

        loop = self._hydraulicLoops.getLoopForExistingConnection(connection)

        otherConnections = {*loop.connections} - {connection}
        isOnlyConnection = not otherConnections
        if isOnlyConnection:
            self._removeLoop(loop)
            return None

        isConnectionRedundant = fromConnections == otherConnections or toConnections == otherConnections
        if isConnectionRedundant:
            assert fromConnections == otherConnections and toConnections == otherConnections

            self._removeConnection(connection, loop)
            return None

        return self._splitLoop(loop, connection, splitLoopsSummary)

    @staticmethod
    def _removeConnection(connection, loop):
        loop.removeConnection(connection)

    def _removeLoop(self, loop: _model.HydraulicLoop) -> None:
        self._hydraulicLoops.removeLoop(loop)

    def _splitLoop(
        self,
        loop: _model.HydraulicLoop,
        connection: _spc.SinglePipeConnection,  # type: ignore[name-defined]
        splitLoopsSummary: _tp.Optional[_common.SplitLoopsSummary],
    ) -> _common.Cancellable[SplitSummary]:
        if not splitLoopsSummary:
            occupiedNames = {l.name.value for l in self._hydraulicLoops.hydraulicLoops} - {loop.name.value}
            cancellable = _dialog.SplitLoopDialog.showDialogAndGetResult(loop, occupiedNames, self._fluids)
            if cancellable == "cancelled":
                return "cancelled"
            splitLoopsSummary = cancellable

        self._hydraulicLoops.removeLoop(loop)

        fromPort, toPort = _helpers.getFromAndToPort(connection)

        fromConnections = _search.getReachableConnections(fromPort, ignoreConnections={connection})
        fromLoop = _model.HydraulicLoop(
            splitLoopsSummary.fromLoop.name, splitLoopsSummary.fromLoop.fluid, [*fromConnections]
        )

        toConnections = _search.getReachableConnections(toPort, ignoreConnections={connection})
        toLoop = _model.HydraulicLoop(splitLoopsSummary.toLoop.name, splitLoopsSummary.toLoop.fluid, [*toConnections])

        self._hydraulicLoops.addLoop(fromLoop)
        self._hydraulicLoops.addLoop(toLoop)

        return SplitSummary.fromLoops(loop, fromLoop, toLoop)
