from __future__ import annotations

import dataclasses as _dc
import typing as _tp

import trnsysGUI.singlePipePortItem as _spi

from . import _search
from . import common as _common
from . import model as _model, _helpers
from ._dialogs.merge import dialog as _md

if _tp.TYPE_CHECKING:
    from trnsysGUI.connection import singlePipeConnection as _spc


@_dc.dataclass
class MergeSummary:
    before: _common.SplitLoopsSummary
    after: _common.MergedLoopSummary

    @staticmethod
    def fromLoops(
        fromLoop: _model.HydraulicLoop,
        toLoop: _model.HydraulicLoop,
        mergedLoop: _model.HydraulicLoop,
    ) -> "MergeSummary":
        splitLoopsSummary = _common.SplitLoopsSummary.fromLoops(fromLoop, toLoop)
        mergedLoopSummary = _common.MergedLoopSummary.fromLoop(mergedLoop)
        mergeSummary = MergeSummary(splitLoopsSummary, mergedLoopSummary)
        return mergeSummary


def merge(
    connection: _spc.SinglePipeConnection,  # type: ignore[name-defined]
    hydraulicLoops: _model.HydraulicLoops,
    fluids: _tp.Sequence[_model.Fluid],
    defaultFluid: _model.Fluid,
    mergedLoopSummary: _tp.Optional[_common.MergedLoopSummary] = None,
) -> _common.Cancellable[_tp.Optional[MergeSummary]]:
    merger = _Merger(hydraulicLoops, fluids, defaultFluid)

    return merger.merge(connection, mergedLoopSummary)


class _Merger:
    def __init__(
        self, hydraulicLoops: _model.HydraulicLoops, fluids: _tp.Sequence[_model.Fluid], defaultFluid: _model.Fluid
    ) -> None:
        self._hydraulicLoops = hydraulicLoops
        self._fluids = fluids
        self._defaultFluid = defaultFluid

    def merge(
        self,
        connection: _spc.SinglePipeConnection,  # type: ignore[name-defined]
        mergedLoopSummary: _tp.Optional[_common.MergedLoopSummary],
    ) -> _common.Cancellable[_tp.Optional[MergeSummary]]:
        fromLoop, toLoop = getFromAndToLoopForNewlyCreatedConnection(self._hydraulicLoops, connection)

        if not fromLoop and not toLoop:
            self._createLoop(connection)
            return None

        if fromLoop and not toLoop:
            self._addConnection(connection, fromLoop)
            return None

        if not fromLoop and toLoop:
            self._addConnection(connection, toLoop)
            return None

        if fromLoop == toLoop:
            loop = fromLoop
            self._addConnection(connection, loop)
            return None

        # This line is needed to help mypy along
        assert fromLoop and toLoop

        return self._mergeLoops(fromLoop, toLoop, connection, mergedLoopSummary)

    @staticmethod
    def _addConnection(connection, loop):
        loop.addConnection(connection)

    def _createLoop(self, connection: _spc.SinglePipeConnection) -> None:  # type: ignore[name-defined]
        name = self._hydraulicLoops.generateName()
        connections = [connection]
        loop = _model.HydraulicLoop(name, self._defaultFluid, connections)
        self._hydraulicLoops.addLoop(loop)

    def _mergeLoops(
        self,
        fromLoop: _model.HydraulicLoop,
        toLoop: _model.HydraulicLoop,
        connection: _spc.SinglePipeConnection,  # type: ignore[name-defined]
        mergedLoopSummary: _tp.Optional[_common.MergedLoopSummary],
    ) -> _common.Cancellable[MergeSummary]:
        connections = [*fromLoop.connections, connection, *toLoop.connections]
        _common.setConnectionsSelected(connections, True)

        if not mergedLoopSummary:
            mergedLoopSummary = self._askUserForMergedLoopSummaryOrNone(fromLoop, toLoop)

        _common.setConnectionsSelected(connections, False)

        if not mergedLoopSummary:
            return "cancelled"

        mergedConnections = [*fromLoop.connections, *toLoop.connections, connection]
        mergedConnections.sort(key=lambda c: c.displayName)
        mergedLoop = _model.HydraulicLoop(mergedLoopSummary.name, mergedLoopSummary.fluid, mergedConnections)
        self._hydraulicLoops.removeLoop(fromLoop)
        self._hydraulicLoops.removeLoop(toLoop)
        self._hydraulicLoops.addLoop(mergedLoop)

        return MergeSummary.fromLoops(fromLoop, toLoop, mergedLoop)

    def _askUserForMergedLoopSummaryOrNone(
        self, loop1: _model.HydraulicLoop, loop2: _model.HydraulicLoop
    ) -> _tp.Optional[_common.MergedLoopSummary]:
        mergedName = self._getMergedNameOrNone(loop1.name, loop2.name)
        areSameFluids = loop1.fluid == loop2.fluid

        if areSameFluids and mergedName:
            mergedFluid = loop1.fluid
            return _common.MergedLoopSummary(mergedName, mergedFluid)

        allNames = {l.name.value for l in self._hydraulicLoops.hydraulicLoops}
        occupiedNames = allNames - {loop1.name.value, loop2.name.value}

        cancellable = _md.MergeLoopsDialog.showDialogAndGetResult(loop1, loop2, occupiedNames, self._fluids)
        if cancellable == "cancelled":
            return None
        mergedLoopSummary = cancellable

        return mergedLoopSummary

    def _getMergedNameOrNone(self, name1: _model.Name, name2: _model.Name) -> _tp.Optional[_model.Name]:
        if name1.isUserDefined and not name2.isUserDefined:
            return name1

        if not name1.isUserDefined and name2.isUserDefined:
            return name2

        if not name1.isUserDefined and not name2.isUserDefined:
            return self._hydraulicLoops.generateName()

        return None


def getFromAndToLoopForNewlyCreatedConnection(
    hydraulicLoops: _model.HydraulicLoops, connection: _spc.SinglePipeConnection  # type: ignore[name-defined]
) -> _tp.Tuple[_tp.Optional[_model.HydraulicLoop], _tp.Optional[_model.HydraulicLoop]]:
    fromPort, toPort = _helpers.getFromAndToPort(connection)

    fromLoop = _getLoopIgnoringConnection(fromPort, connection, hydraulicLoops)
    toLoop = _getLoopIgnoringConnection(toPort, connection, hydraulicLoops)

    return fromLoop, toLoop


def _getLoopIgnoringConnection(
    portItem: _spi.SinglePipePortItem,  # type: ignore[name-defined]
    connection: _spc.SinglePipeConnection,  # type: ignore[name-defined]
    hydraulicLoops: _model.HydraulicLoops,
) -> _tp.Optional[_model.HydraulicLoop]:
    connections = _search.getReachableConnections(portItem, ignoreConnections={connection})
    if not connections:
        return None

    loops = {hydraulicLoops.getLoopForExistingConnection(c) for c in connections}
    loop = _helpers.getSingle(loops)
    return loop