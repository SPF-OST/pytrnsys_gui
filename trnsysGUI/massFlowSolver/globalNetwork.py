import dataclasses as _dc
import typing as _tp

import trnsysGUI.PortItemBase as _pib
import trnsysGUI.common as _com
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn


@_dc.dataclass
class NodeWithParent:
    node: _mfn.Node
    parent: _ip.HasInternalPiping


@_dc.dataclass
class GlobalNetwork:
    nodesWithParent: _tp.Sequence[NodeWithParent]
    internalPortItemToExternalNode: _tp.Mapping[_mfn.PortItem, _mfn.Node]


def getGlobalNetwork(hasInternalPipings: _tp.Sequence[_ip.HasInternalPiping]) -> GlobalNetwork:
    allNodesWithParent, modelsToGraphicalPortItem = (
        _getAllNodesWithParentAndModelsToGraphicalPortItem(hasInternalPipings)
    )

    allNodes = [nwp.node for nwp in allNodesWithParent]

    modelPortItemsToNode = {
        mpi: n for n in allNodes for mpi in n.getPortItems()
    }

    graphicalPortItemsToModels = _getGraphicalPortItemsToModels(modelsToGraphicalPortItem)

    internalPortItemToExternalNode = _getInternalPortItemToExternalNode(
        allNodes, modelsToGraphicalPortItem, graphicalPortItemsToModels, modelPortItemsToNode
    )

    return GlobalNetwork(allNodesWithParent, internalPortItemToExternalNode)


def _getAllNodesWithParentAndModelsToGraphicalPortItem(
    hasInternalPipings: _tp.Sequence[_ip.HasInternalPiping],
) -> _tp.Tuple[_tp.Sequence[NodeWithParent], _tp.Mapping[_mfn.PortItem, _pib.PortItemBase]]:
    allNodes: _tp.List[NodeWithParent] = []
    modelsToGraphicalPortItem: _tp.Dict[_mfn.PortItem, _pib.PortItemBase] = {}
    for hasInternalPiping in hasInternalPipings:
        internalPiping = hasInternalPiping.getInternalPiping()
        nodesWithParent = [NodeWithParent(n, hasInternalPiping) for n in internalPiping.nodes]
        allNodes.extend(nodesWithParent)
        modelsToGraphicalPortItem.update(internalPiping.modelPortItemsToGraphicalPortItem)
    return allNodes, modelsToGraphicalPortItem


def _getGraphicalPortItemsToModels(
    modelsToGraphicalPortItem: _tp.Mapping[_mfn.PortItem, _pib.PortItemBase]
) -> _tp.Mapping[_pib.PortItemBase, _tp.Sequence[_mfn.PortItem]]:
    graphicalPortItemsToModels: _tp.Dict[_pib.PortItemBase, _tp.List[_mfn.PortItem]] = {}
    for model, graphicalPortItem in modelsToGraphicalPortItem.items():
        models = graphicalPortItemsToModels.get(graphicalPortItem)

        if models:
            models.append(model)
        else:
            graphicalPortItemsToModels[graphicalPortItem] = [model]
    return graphicalPortItemsToModels


def _getInternalPortItemToExternalNode(
    nodes: _tp.Sequence[_mfn.Node],
    modelsToGraphicalPortItem: _tp.Mapping[_mfn.PortItem, _pib.PortItemBase],
    graphicalPortItemsToModels: _tp.Mapping[_pib.PortItemBase, _tp.Sequence[_mfn.PortItem]],
    modelPortItemsToNode: _tp.Mapping[_mfn.PortItem, _mfn.Node],
) -> _tp.Mapping[_mfn.PortItem, _mfn.Node]:
    portItemsToJoin = {}
    for internalNode in nodes:
        for portItem in internalNode.getPortItems():
            graphicalPortItem = modelsToGraphicalPortItem[portItem]
            candidates = graphicalPortItemsToModels[graphicalPortItem]

            externalPortItem = _com.getSingle(
                c for c in candidates if c != portItem and c.canOverlapWith(portItem)
            )

            externalNode = modelPortItemsToNode[externalPortItem]

            portItemsToJoin[portItem] = externalNode

    return portItemsToJoin
