import abc as _abc
import dataclasses as _dc

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
class DoublePipeConnection:
    displayName: str
    lengthInM: float
    shallBeSimulated: bool
    coldPipe: SinglePipe
    hotPipe: SinglePipe

    def getOutputTemperatureVariableName(self, pipe: SinglePipe) -> str:
        return _temps.getTemperatureVariableName(
            shallRenameOutputInHydraulicFile=False, componentDisplayName=self.displayName, nodeName=pipe.name
        )

    def getCanonicalMassFlowRateVariableName(self, pipe: SinglePipe) -> str:
        return _mnames.getCanonicalMassFlowVariableName(componentDisplayName=self.displayName, pipeName=pipe.name)
