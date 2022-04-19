import dataclasses as _dc
import typing as _tp

import trnsysGUI.PortItemBase as _pib

import trnsysGUI.massFlowSolver as _mfs
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.common as _com


@_dc.dataclass
class GlobalNetwork:
    realNodes: _tp.Sequence[_mfn.RealNodeBase]
    internalPortItemToExternalRealNode: _tp.Mapping[_mfn.PortItem, _mfn.RealNodeBase]


def getGlobalNetwork(massFlowContributors: _tp.Sequence[_mfs.MassFlowNetworkContributorMixin]) -> GlobalNetwork:
    allRealNodes, modelsToGraphicalPortItem = _getAllRealNodesAndModelsToGraphicalPortItem(massFlowContributors)

    modelPortItemsToRealNode = {n: rn for rn in allRealNodes for n in rn.getNeighbours() if isinstance(n, _mfn.PortItem)}

    graphicalPortItemsToModels = _getGraphicalPortItemsToModels(modelsToGraphicalPortItem)

    internalPortItemToExternalRealNode = _getInternalPortItemToExternalRealNode(
        allRealNodes, modelsToGraphicalPortItem, graphicalPortItemsToModels, modelPortItemsToRealNode
    )

    return GlobalNetwork(allRealNodes, internalPortItemToExternalRealNode)


def _getAllRealNodesAndModelsToGraphicalPortItem(
    massFlowContributors: _tp.Sequence[_mfs.MassFlowNetworkContributorMixin],
) -> _tp.Tuple[_tp.Sequence[_mfn.RealNodeBase], _tp.Mapping[_mfn.PortItem, _pib.PortItemBase]]:
    allRealNodes: _tp.List[_mfn.RealNodeBase] = []
    modelsToGraphicalPortItem: _tp.Dict[_mfn.PortItem, _pib.PortItemBase] = {}
    for massFlowContributor in massFlowContributors:
        internalPiping = massFlowContributor.getInternalPiping()
        realNodes = internalPiping.getAllRealNodes()
        allRealNodes.extend(realNodes)
        modelsToGraphicalPortItem.update(internalPiping.modelPortItemsToGraphicalPortItem)
    return allRealNodes, modelsToGraphicalPortItem


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


def _getInternalPortItemToExternalRealNode(
    allRealNodes: _tp.Sequence[_mfn.RealNodeBase],
    modelsToGraphicalPortItem: _tp.Mapping[_mfn.PortItem, _pib.PortItemBase],
    graphicalPortItemsToModels: _tp.Mapping[_pib.PortItemBase, _tp.Sequence[_mfn.PortItem]],
    modelPortItemsToRealNode: _tp.Mapping[_mfn.PortItem, _mfn.RealNodeBase],
) -> _tp.Mapping[_mfn.PortItem, _mfn.RealNodeBase]:
    portItemsToJoin = {}
    for internalRealNode in allRealNodes:
        for neighbor in internalRealNode.getNeighbours():
            if not isinstance(neighbor, _mfn.PortItem):
                continue

            portItem = neighbor
            graphicalPortItem = modelsToGraphicalPortItem[portItem]
            candidates = graphicalPortItemsToModels[graphicalPortItem]

            externalPortItem = _com.getSingle(c for c in candidates if c.canOverlapWith(portItem))

            externalRealNode = modelPortItemsToRealNode[externalPortItem]

            portItemsToJoin[portItem] = externalRealNode

    return portItemsToJoin
