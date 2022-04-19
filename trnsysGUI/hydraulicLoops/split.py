from __future__ import annotations

import dataclasses as _dc
import typing as _tp

from . import _helpers
from . import _loopWideDefaults as _lwd
from . import search
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

        fromConnections = search.getReachableConnections(fromPort, ignoreConnections={connection})
        toConnections = search.getReachableConnections(toPort, ignoreConnections={connection})

        loop = self._hydraulicLoops.getLoopForExistingConnection(connection)

        otherConnections = {*loop.connections} - {connection}
        isOnlyConnection = not otherConnections
        if isOnlyConnection:
            self._removeLoop(loop)
            return None

        isConnectionRedundant = (
            fromConnections == otherConnections or toConnections == otherConnections  # pylint: disable=consider-using-in
        )
        if isConnectionRedundant:
            assert (not fromConnections or fromConnections == otherConnections) and (
                not toConnections or toConnections == otherConnections
            )

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
        fromPort, toPort = _helpers.getFromAndToPort(connection)

        fromConnections = search.getReachableConnections(fromPort, ignoreConnections={connection})
        toConnections = search.getReachableConnections(toPort, ignoreConnections={connection})

        if not splitLoopsSummary:
            cancellable = self._createSplitLoopsSummary(loop, fromConnections, connection, toConnections)
            if cancellable == "cancelled":
                return "cancelled"
            splitLoopsSummary = cancellable

        self._hydraulicLoops.removeLoop(loop)

        fromLoopName = splitLoopsSummary.fromLoop.name
        toLoopName = splitLoopsSummary.toLoop.name

        useLoopWideDefaults = loop.useLoopWideDefaults
        if useLoopWideDefaults:
            _lwd.resetConnectionPropertiesToLoopWideDefaults([*fromConnections], fromLoopName.value)
            _lwd.resetConnectionPropertiesToLoopWideDefaults([*toConnections], toLoopName.value)

        fromLoop = _model.HydraulicLoop(
            fromLoopName, splitLoopsSummary.fromLoop.fluid, useLoopWideDefaults, [*fromConnections]
        )

        toLoop = _model.HydraulicLoop(
            toLoopName, splitLoopsSummary.toLoop.fluid, useLoopWideDefaults, [*toConnections]
        )

        self._hydraulicLoops.addLoop(fromLoop)
        self._hydraulicLoops.addLoop(toLoop)

        return SplitSummary.fromLoops(loop, fromLoop, toLoop)

    def _createSplitLoopsSummary(
        self,
        loop: _model.HydraulicLoop,
        fromConnections: _tp.Set[_spc.SinglePipeConnection],  # type: ignore[name-defined]
        connection: _spc.SinglePipeConnection,  # type: ignore[name-defined]
        toConnections: _tp.Set[_spc.SinglePipeConnection],  # type: ignore[name-defined]
    ) -> _common.Cancellable[_common.SplitLoopsSummary]:
        if not loop.name.isUserDefined:
            return self._createSplitLoopsSummaryForAutomaticLoop(loop)

        return self._askUserForSplitLoopsSummary(loop, fromConnections, connection, toConnections)

    def _createSplitLoopsSummaryForAutomaticLoop(self, loop: _model.HydraulicLoop) -> _common.SplitLoopsSummary:
        fromLoopSummary = _common.LoopSummary(loop.name, loop.fluid)

        toLoopName = self._hydraulicLoops.generateName()
        toLoopSummary = _common.LoopSummary(toLoopName, loop.fluid)

        return _common.SplitLoopsSummary(fromLoopSummary, toLoopSummary)

    def _askUserForSplitLoopsSummary(
        self,
        loop: _model.HydraulicLoop,
        fromConnections: _tp.Set[_spc.SinglePipeConnection],  # type: ignore[name-defined]
        connection: _spc.SinglePipeConnection,  # type: ignore[name-defined]
        toConnections: _tp.Set[_spc.SinglePipeConnection],  # type: ignore[name-defined]
    ) -> _common.Cancellable[_common.SplitLoopsSummary]:
        occupiedNames = {l.name.value for l in self._hydraulicLoops.hydraulicLoops} - {loop.name.value}

        setLoop1Selected = self._createSetConnectionsSelectedCallback(fromConnections)
        setLoop2Selected = self._createSetConnectionsSelectedCallback(toConnections)

        connection.deselectConnection()

        cancellable = _dialog.SplitLoopDialog.showDialogAndGetResult(
            loop,
            occupiedNames,
            self._fluids,
            setLoop1Selected,
            setLoop2Selected,
        )

        return cancellable

    @staticmethod
    def _createSetConnectionsSelectedCallback(
        connections: _tp.Set[_spc.SinglePipeConnection],  # type: ignore[name-defined]
    ) -> _tp.Callable[[bool], None]:
        def callback(isSelected: bool) -> None:
            _common.setConnectionsSelected(connections, isSelected)

        return callback
