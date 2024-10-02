import collections.abc as _cabc
import dataclasses as _dc
import importlib.resources as _ilr
import typing as _tp

import pytrnsys.utils.result as _res
import trnsysGUI.BlockItem as _bi
import trnsysGUI.PortItemBase as _pib
import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.doublePipePortItem as _dpi
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn
from . import graphics as _graphics
from . import plugin as _plugin
from .specification import load as _sload
from .specification import model as _smodel

_T_co = _tp.TypeVar("_T_co", covariant=True, bound=_pib.PortItemBase)


@_dc.dataclass
class Factory:
    specificationLoader: _sload.Loader

    @staticmethod
    def createDefault() -> "Factory":
        packageResourceLoader = _sload.Loader.createPackageResourceLoader()
        return Factory(packageResourceLoader)

    @staticmethod
    def getTypeNames() -> _cabc.Sequence[str]:
        traversable = _ilr.files(_plugin.__name__).joinpath("data")
        typeNames = [tt.name for tt in traversable.iterdir()]
        return typeNames

    @staticmethod
    def hasTypeName(candidateTypeName: str) -> bool:
        return candidateTypeName in Factory.getTypeNames()

    def create(self, typeName: str) -> _res.Result[_plugin.Plugin]:
        if not self.hasTypeName(typeName):
            raise ValueError("Unknown type.", typeName)

        specificationResult = self.specificationLoader.load(typeName)
        if _res.isError(specificationResult):
            return _res.error(specificationResult)
        specification = _res.value(specificationResult)

        width, height = specification.size
        graphics = _graphics.Graphics.createForTypeNameAndSize(typeName, width=width, height=height)

        internalPipingFactory = InternalPipingFactory(specification)

        plugin = _plugin.Plugin(typeName, specification.defaultName, graphics, internalPipingFactory)

        return plugin


@_dc.dataclass
class _PortProperties:
    defaultName: str
    directionLabel: str
    direction: _mfn.PortItemDirection

    def getName(self, nameSpec: str | None) -> str:
        return nameSpec or self.defaultName


_INPUT_PORT_PROPERTIES = _PortProperties("In", "in", _mfn.PortItemDirection.INPUT)
_OUTPUT_PORT_PROPERTIES = _PortProperties("Out", "out", _mfn.PortItemDirection.OUTPUT)
_OUTPUT0_PORT_PROPERTIES = _PortProperties("Out0", "out", _mfn.PortItemDirection.OUTPUT)
_OUTPUT1_PORT_PROPERTIES = _PortProperties("Out1", "out", _mfn.PortItemDirection.OUTPUT)


@_dc.dataclass
class InternalPipingFactory(_plugin.AbstractInternalPipingFactory):
    specification: _smodel.Specification

    def createInternalPiping(self, blockItem: _bi.BlockItem) -> _plugin.CreatedInternalPiping:
        connectionsCreatedInternalPiping = self._createInternalPipingForConnections(blockItem)
        teePiecesCreatedInternalPiping = self._createInternalPipingForTeePieces(blockItem)

        combinedCreatedInternalPiping = self._createCombinedCreatedInternalPiping(
            connectionsCreatedInternalPiping, teePiecesCreatedInternalPiping
        )
        return combinedCreatedInternalPiping

    def _createInternalPipingForConnections(self, blockItem: _bi.BlockItem) -> _plugin.CreatedInternalPiping:
        connections = self.specification.connections

        if not connections:
            return _plugin.CreatedInternalPiping.empty()

        graphicalInputPorts = []
        graphicalOutputPorts = []

        nodes = []
        modelPortItemsToGraphicalPortItem = {}

        for connection in connections:
            graphicalInputPort, modelInputPort = self._createGraphicalAndModelPort(
                connection.input, _INPUT_PORT_PROPERTIES, blockItem
            )

            graphicalInputPorts.append(graphicalInputPort)
            modelPortItemsToGraphicalPortItem[modelInputPort] = graphicalInputPort

            graphicalOutputPort, modelOutputPort = self._createGraphicalAndModelPort(
                connection.output, _OUTPUT_PORT_PROPERTIES, blockItem
            )

            graphicalOutputPorts.append(graphicalOutputPort)
            modelPortItemsToGraphicalPortItem[modelOutputPort] = graphicalOutputPort

            pipe = _mfn.Pipe(modelInputPort, modelOutputPort, connection.name)
            nodes.append(pipe)

        internalPiping = _ip.InternalPiping(nodes, modelPortItemsToGraphicalPortItem)

        createdInternalPiping = _plugin.CreatedInternalPiping(graphicalInputPorts, graphicalOutputPorts, internalPiping)

        return createdInternalPiping

    def _createInternalPipingForTeePieces(self, blockItem: _bi.BlockItem) -> _plugin.CreatedInternalPiping:
        graphicalInputPorts = []
        graphicalOutputPorts = []

        nodes = []
        modelPortItemsToGraphicalPortItem = {}

        teePieces = self.specification.teePieces

        if not teePieces:
            return _plugin.CreatedInternalPiping.empty()

        for teePiece in self.specification.teePieces:
            graphicalInputPort, modelInputPort = self._createGraphicalAndModelPort(
                teePiece.input, _INPUT_PORT_PROPERTIES, blockItem
            )

            graphicalOutput0Port, modelOutput0Port = self._createGraphicalAndModelPort(
                teePiece.output0, _OUTPUT0_PORT_PROPERTIES, blockItem
            )

            graphicalOutput1Port, modelOutput1Port = self._createGraphicalAndModelPort(
                teePiece.output1, _OUTPUT1_PORT_PROPERTIES, blockItem
            )

            graphicalInputPorts.append(graphicalInputPort)
            graphicalOutputPorts.append(graphicalOutput0Port)
            graphicalOutputPorts.append(graphicalOutput1Port)

            modelPortItemsToGraphicalPortItem[modelInputPort] = graphicalInputPort
            modelPortItemsToGraphicalPortItem[modelOutput0Port] = graphicalOutput0Port
            modelPortItemsToGraphicalPortItem[modelOutput1Port] = graphicalOutput1Port

            teePieceModel = _mfn.TeePiece(modelInputPort, modelOutput0Port, modelOutput1Port)

            nodes.append(teePieceModel)

        internalPiping = _ip.InternalPiping(nodes, modelPortItemsToGraphicalPortItem)

        createdInternalPiping = _plugin.CreatedInternalPiping(graphicalInputPorts, graphicalOutputPorts, internalPiping)

        return createdInternalPiping

    def _createGraphicalAndModelPort(
        self, portSpec: _smodel.Port, portProperties: _PortProperties, blockItem: _bi.BlockItem
    ) -> tuple[_pib.PortItemBase, _mfn.PortItem]:
        graphicalPort = self._createPort(portSpec, portProperties, blockItem)

        posX, posY = portSpec.position
        graphicalPort.setPos(posX, posY)

        portName = portProperties.getName(portSpec.name)
        portItemType = _mfn.PortItemType(portSpec.type)
        modelInputPort = _mfn.PortItem(portName, portProperties.direction, portItemType)

        return graphicalPort, modelInputPort

    @staticmethod
    def _createPort(
        portSpec: _smodel.Port, portProperties: _PortProperties, blockItem: _bi.BlockItem
    ) -> _pib.PortItemBase:
        match portSpec.type:
            case "standard":
                return _cspi.createSinglePipePortItem(portProperties.directionLabel, blockItem)
            case "hot" | "cold":
                return _dpi.DoublePipePortItem(portProperties.directionLabel, blockItem)
            case _:
                _tp.assert_never(portSpec.type)

    @staticmethod
    def _getDirectionLabel(direction: _mfn.PortItemDirection) -> _tp.Literal["i", "o"]:
        match direction:
            case _mfn.PortItemDirection.INPUT:
                return "i"
            case _mfn.PortItemDirection.OUTPUT:
                return "o"
            case _:
                _tp.assert_never(direction)

    @staticmethod
    def _createCombinedCreatedInternalPiping(
        connectionsCreatedInternalPiping: _plugin.CreatedInternalPiping,
        teePiecesCreatedInternalPiping: _plugin.CreatedInternalPiping,
    ) -> _plugin.CreatedInternalPiping:
        internalPiping = _ip.InternalPiping(
            [
                *connectionsCreatedInternalPiping.internalPiping.nodes,
                *teePiecesCreatedInternalPiping.internalPiping.nodes,
            ],
            {
                **connectionsCreatedInternalPiping.internalPiping.modelPortItemsToGraphicalPortItem,
                **teePiecesCreatedInternalPiping.internalPiping.modelPortItemsToGraphicalPortItem,
            },
        )
        createdInternalPiping = _plugin.CreatedInternalPiping(
            [*connectionsCreatedInternalPiping.inputPorts, *teePiecesCreatedInternalPiping.inputPorts],
            [*connectionsCreatedInternalPiping.outputPorts, *teePiecesCreatedInternalPiping.outputPorts],
            internalPiping,
        )
        return createdInternalPiping
