import dataclasses as _dc

import trnsysGUI.connection.hydraulicExport.common as _com
import trnsysGUI.globalNames as _gnames
from trnsysGUI import temperatures as _temps
from trnsysGUI.massFlowSolver import names as _mnames


@_dc.dataclass
class Pipe:
    name: str
    inputPort: _com.InputPort
    outputPort: _com.OutputPort


@_dc.dataclass
class ExportHydraulicDoublePipeConnection:
    displayName: str
    coldPipe: Pipe
    hotPipe: Pipe

    @property
    def coldOutputTemperatureVariableName(self) -> str:
        return _temps.getTemperatureVariableName(
            shallRenameOutputInHydraulicFile=False, componentDisplayName=self.displayName, nodeName=self.coldPipe.name
        )

    @property
    def hotOutputTemperatureVariableName(self) -> str:
        return _temps.getTemperatureVariableName(
            shallRenameOutputInHydraulicFile=False, componentDisplayName=self.displayName, nodeName=self.hotPipe.name
        )

    @property
    def initialColdOutputTemperatureVariableName(self) -> str:
        return _gnames.DoublePipes.INITIAL_COLD_TEMPERATURE

    @property
    def initialHotOutputTemperatureVariableName(self) -> str:
        return _gnames.DoublePipes.INITIAL_HOT_TEMPERATURE

    @property
    def coldCanonicalMassFlowRateVariableName(self) -> str:
        return _mnames.getCanonicalMassFlowVariableName(
            componentDisplayName=self.displayName, pipeName=self.coldPipe.name
        )

    @property
    def hotCanonicalMassFlowRateVariableName(self) -> str:
        return _mnames.getCanonicalMassFlowVariableName(
            componentDisplayName=self.displayName, pipeName=self.hotPipe.name
        )


ExportDoublePipeConnection = _com.GenericConnection[ExportHydraulicDoublePipeConnection]
