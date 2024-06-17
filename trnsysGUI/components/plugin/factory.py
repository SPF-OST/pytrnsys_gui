import abc as _abc
import collections.abc as _cabc
import dataclasses as _dc
import importlib.resources as _ilr
import typing as _tp

import pytrnsys.utils.result as _res
import trnsysGUI.BlockItem as _bi
import trnsysGUI.PortItemBase as _pib
import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.singlePipePortItem as _spi
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


class _PortPropertiesBase(_abc.ABC):
    def getName(self, nameSpec: str | None) -> str:
        return nameSpec or self.defaultName

    @property
    @_abc.abstractmethod
    def defaultName(self) -> str:
        raise NotImplementedError()

    @property
    @_abc.abstractmethod
    def directionLabel(self) -> str:
        raise NotImplementedError()

    @property
    @_abc.abstractmethod
    def direction(self) -> _mfn.PortItemDirection:
        raise NotImplementedError()


class _InputPortProperties(_PortPropertiesBase):
    @property
    @_tp.override
    def defaultName(self) -> str:
        return "In"

    @property
    @_tp.override
    def directionLabel(self) -> str:
        return "in"

    @property
    @_tp.override
    def direction(self) -> _mfn.PortItemDirection:
        return _mfn.PortItemDirection.INPUT


class _OutputPortProperties(_PortPropertiesBase):
    @property
    @_tp.override
    def defaultName(self) -> str:
        return "Out"

    @property
    @_tp.override
    def directionLabel(self) -> str:
        return "in"

    @property
    @_tp.override
    def direction(self) -> _mfn.PortItemDirection:
        return _mfn.PortItemDirection.OUTPUT


_INPUT_PORT_HELPER = _InputPortProperties()
_OUTPUT_PORT_HELPER = _OutputPortProperties()


@_dc.dataclass
class InternalPipingFactory(_plugin.AbstractInternalPipingFactory):
    specification: _smodel.Specification

    def createInternalPiping(self, blockItem: _bi.BlockItem) -> _plugin.CreatedInternalPiping:
        graphicalInputPorts = []
        graphicalOutputPorts = []

        nodes = []
        modelPortItemsToGraphicalPortItem = {}

        for connection in self.specification.connections:
            graphicalInputPort, modelInputPort = self._createGraphicalAndModelPort(
                connection.input, _INPUT_PORT_HELPER, blockItem
            )

            graphicalInputPorts.append(graphicalInputPort)
            modelPortItemsToGraphicalPortItem[modelInputPort] = graphicalInputPort

            graphicalOutputPort, modelOutputPort = self._createGraphicalAndModelPort(
                connection.output, _OUTPUT_PORT_HELPER, blockItem
            )

            graphicalOutputPorts.append(graphicalOutputPort)
            modelPortItemsToGraphicalPortItem[modelOutputPort] = graphicalOutputPort

            pipe = _mfn.Pipe(modelInputPort, modelOutputPort, connection.name)
            nodes.append(pipe)

        internalPiping = _ip.InternalPiping(nodes, modelPortItemsToGraphicalPortItem)

        createdInternalPiping = _plugin.CreatedInternalPiping(graphicalInputPorts, graphicalOutputPorts, internalPiping)

        return createdInternalPiping

    def _createGraphicalAndModelPort(
        self, portSpec: _smodel.Port, portHelper: _PortPropertiesBase, blockItem: _bi.BlockItem
    ) -> tuple[_pib.PortItemBase, _mfn.PortItem]:
        graphicalPort = self._createPort(portSpec, portHelper, blockItem)

        posX, posY = portSpec.position
        graphicalPort.setPos(posX, posY)

        portName = portHelper.getName(portSpec.name)
        portItemType = _mfn.PortItemType(portSpec.type)
        modelInputPort = _mfn.PortItem(portName, portHelper.direction, portItemType)

        return graphicalPort, modelInputPort

    def _createPort(
        self, portSpec: _smodel.Port, portHelper: _PortPropertiesBase, blockItem: _bi.BlockItem
    ) -> _pib.PortItemBase:
        side = self._getSide(portSpec.position)

        match portSpec.type:
            case "standard":
                return _cspi.createSinglePipePortItem(portHelper.directionLabel, side, blockItem)
            case "hot" | "cold":
                return _dpi.DoublePipePortItem(portHelper.directionLabel, side, blockItem)
            case _:
                _tp.assert_never(portSpec.type)

    def _getSide(self, portPosition: tuple[int, int]) -> _spi.Side:
        posX, posY = portPosition
        width, height = self.specification.size

        if posX == 0:
            return 0
        if posY == 0:
            return 1
        if posX == width:
            return 2
        if posY == height:
            return 3

        raise ValueError("Invalid port position.", portPosition)

    @staticmethod
    def _getDirectionLabel(direction: _mfn.PortItemDirection) -> _tp.Literal["i", "o"]:
        match direction:
            case _mfn.PortItemDirection.INPUT:
                return "i"
            case _mfn.PortItemDirection.OUTPUT:
                return "o"
            case _:
                _tp.assert_never(direction)
