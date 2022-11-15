from __future__ import annotations

import dataclasses as _dc
import typing as _tp

import trnsysGUI.massFlowSolver.networkModel as _mfn

if _tp.TYPE_CHECKING:
    import trnsysGUI.PortItemBase as _pi


@_dc.dataclass
class InternalPiping:
    nodes: _tp.Sequence[_mfn.Node]
    modelPortItemsToGraphicalPortItem: _tp.Mapping[_mfn.PortItem, _pi.PortItemBase]  # type: ignore[name-defined]

    def __post_init__(self):
        if not all(
            mpi in self.modelPortItemsToGraphicalPortItem for n in self.nodes for mpi in n.getPortItems()
        ):
            raise ValueError("Error a port item of a node was not contained in `modelPortItemsToGraphicalPortItem`.")

    def getModelPortItem(
        self, graphicalPortItem: _pi.PortItemBase, portItemType: _mfn.PortItemType  # type: ignore[name-defined]
    ) -> _mfn.PortItem:
        modelPortItems = [mpi for mpi in self.getModelPortItems(graphicalPortItem) if mpi.type == portItemType]

        if not modelPortItems:
            raise ValueError(
                f"Could not find a model port item for graphical port {graphicalPortItem} of type {portItemType}."
            )

        assert (
            len(modelPortItems) == 1
        ), "One one model port item of a given type can be associated with a graphical port item."

        return modelPortItems[0]

    def getModelPortItems(self, graphicalPortItem: _pi.PortItemBase) -> _tp.Sequence[_mfn.PortItem]:
        modelPortItems = [mpi for mpi, gpi in self.modelPortItemsToGraphicalPortItem.items() if gpi == graphicalPortItem]
        return modelPortItems

    def getNode(
        self, graphicalPortItem: _pi.PortItemBase, portItemType: _mfn.PortItemType  # type: ignore[name-defined]
    ) -> _mfn.Node:
        nodes = [n for n, t in self._getNodesAndPortItemType(graphicalPortItem) if t == portItemType]

        if not nodes:
            raise ValueError(
                f"Could not find a port of type {portItemType} associated with graphical port item."
            )

        if len(nodes) > 1:
            raise AssertionError(
                "At most one model port item of a given type can be associated with a graphical port itme."
            )

        return nodes[0]

    def _getNodesAndPortItemType(
        self, graphicalPortItem: _pi.PortItemBase  # type: ignore[name-defined]
    ) -> _tp.Iterable[_tp.Tuple[_mfn.Node, _mfn.PortItemType]]:
        for node in self.nodes:
            for portItem in node.getPortItems():
                candidateGraphicalPortItem = self.modelPortItemsToGraphicalPortItem[portItem]
                if candidateGraphicalPortItem == graphicalPortItem:
                    yield node, portItem.type


class HasInternalPiping:
    def getDisplayName(self) -> str:
        raise NotImplementedError()

    def hasDdckPlaceHolders(self) -> bool:
        return True

    def shallRenameOutputTemperaturesInHydraulicFile(self):
        return True

    def getInternalPiping(self) -> InternalPiping:
        raise NotImplementedError()
