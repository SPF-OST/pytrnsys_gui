import abc as _abc
import dataclasses as _dc

import trnsysGUI.globalNames as _gnames
import trnsysGUI.massFlowSolver.names as _mnames
import trnsysGUI.temperatures as _temps


@_dc.dataclass
class PortBase(_abc.ABC):
    inputTemperatureVariableName: str


@_dc.dataclass
class InputPort(PortBase):
    massFlowRateVariableName: str


@_dc.dataclass
class OutputPort(PortBase):
    pass


@_dc.dataclass
class SinglePipe:
    name: str
    inputPort: InputPort
    outputPort: OutputPort


@_dc.dataclass
class HydraulicDoublePipeConnection:
    displayName: str
    coldPipe: SinglePipe
    hotPipe: SinglePipe

    def getOutputTemperatureVariableName(self, pipe: SinglePipe) -> str:
        return _temps.getTemperatureVariableName(
            shallRenameOutputInHydraulicFile=False, componentDisplayName=self.displayName, nodeName=pipe.name
        )

    def getInitialOutputTemperatureVariableName(self, pipe: SinglePipe) -> str:
        if pipe is self.coldPipe:
            return _gnames.DoublePipes.INITIAL_COLD_TEMPERATURE

        if pipe is self.hotPipe:
            return _gnames.DoublePipes.INITIAL_HOT_TEMPERATURE

        raise ValueError("`pipe` single pipe does not belong to this double pipe")

    def getCanonicalMassFlowRateVariableName(self, pipe: SinglePipe) -> str:
        return _mnames.getCanonicalMassFlowVariableName(componentDisplayName=self.displayName, pipeName=pipe.name)


@_dc.dataclass
class DoublePipeConnection:
    hydraulicConnection: HydraulicDoublePipeConnection
    lengthInM: float
    shallBeSimulated: bool
