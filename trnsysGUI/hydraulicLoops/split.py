from __future__ import annotations

import dataclasses as _dc
import typing as _tp

from . import _helpers
from . import _search
from . import common as _common
from . import model as _model

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
    splitLoopsSummary: _tp.Optional[_common.SplitLoopsSummary],
) -> _common.Cancellable[_tp.Optional[SplitSummary]]:
    splitter = _Splitter(hydraulicLoops)

    return splitter.split(connection, splitLoopsSummary)


class _Splitter:
    def __init__(self, hydraulicLoops: _model.HydraulicLoops) -> None:
        self._hydraulicLoops = hydraulicLoops

    def split(
        self,
        connection: _spc.SinglePipeConnection,  # type: ignore[name-defined]
        splitLoopsSummary: _tp.Optional[_common.SplitLoopsSummary] = None,
    ) -> _common.Cancellable[_tp.Optional[SplitSummary]]:
        fromPort, toPort = _helpers.getFromAndToPort(connection)

        loop = self._hydraulicLoops.getLoopForExistingConnection(connection)

        isFromLeaf = _search.isLeaf(fromPort)
        isToLeaf = _search.isLeaf(toPort)

        if isFromLeaf and isToLeaf:
            self._removeLoop(loop)
            return None

        if isFromLeaf or isToLeaf:
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
    ) -> SplitSummary:
        if not splitLoopsSummary:
            # TODO@damian.birchler ask user what to do here
            fromLoopSummary = _common.LoopSummary(loop.name, loop.fluid)

            toLoopName = self._hydraulicLoops.generateName()
            toLoopSummary = _common.LoopSummary(toLoopName, loop.fluid)

            splitLoopsSummary = _common.SplitLoopsSummary(fromLoopSummary, toLoopSummary)

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
