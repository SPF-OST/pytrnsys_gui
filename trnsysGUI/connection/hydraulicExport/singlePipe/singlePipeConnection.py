import dataclasses as _dc

import trnsysGUI.connection.hydraulicExport.common as _com
import trnsysGUI.globalNames as _gnames
import trnsysGUI.massFlowSolver.names as _mnames
import trnsysGUI.temperatures as _temps


@_dc.dataclass
class Pipe:
    inputPort: _com.InputPort
    outputPort: _com.OutputPort


@_dc.dataclass
class ExportHydraulicSinglePipeConnection:
    displayName: str
    pipe: Pipe

    @property
    def outputTemperatureVariableName(self):
        return _temps.getTemperatureVariableName(
            shallRenameOutputInHydraulicFile=False, componentDisplayName=self.displayName, nodeName=None
        )

    @property
    def canonicalMassFlowRateVariableName(self):
        return _mnames.getCanonicalMassFlowVariableName(componentDisplayName=self.displayName, pipeName=None)

    initialOutputTemperatureVariableName = _gnames.SinglePipes.INITIAL_TEMPERATURE


ExportSinglePipeConnection = _com.GenericConnection[ExportHydraulicSinglePipeConnection]
