from __future__ import annotations

import dataclasses as _dc
import typing as _tp

from . import model as _model

if _tp.TYPE_CHECKING:
    import trnsysGUI.connection.singlePipeConnection as _spc


@_dc.dataclass
class LoopSummaryBase:
    name: _model.Name
    fluid: _model.Fluid


class LoopSummary(LoopSummaryBase):
    @staticmethod
    def fromLoop(loop: _model.HydraulicLoop) -> "LoopSummary":
        return LoopSummary(loop.name, loop.fluid)


class MergedLoopSummary(LoopSummaryBase):
    @staticmethod
    def fromLoop(loop: _model.HydraulicLoop) -> "MergedLoopSummary":
        return MergedLoopSummary(loop.name, loop.fluid)


@_dc.dataclass
class SplitLoopsSummary:
    fromLoop: LoopSummary
    toLoop: LoopSummary

    @staticmethod
    def fromLoops(
        fromLoop: _model.HydraulicLoop,
        toLoop: _model.HydraulicLoop,
    ) -> "SplitLoopsSummary":
        fromLoopSummary = LoopSummary.fromLoop(fromLoop)
        toLoopSummary = LoopSummary.fromLoop(toLoop)
        return SplitLoopsSummary(fromLoopSummary, toLoopSummary)


T = _tp.TypeVar("T")  # pylint: disable=invalid-name
Cancellable = _tp.Union[_tp.Literal["cancelled"], T]


def setConnectionsSelected(
        connections: _tp.Iterable[_spc.SinglePipeConnection],  # type: ignore[name-defined]
        isSelected: bool) -> None:
    for connection in connections:
        if isSelected:
            connection.selectConnection()
        else:
            connection.deselectConnection()
