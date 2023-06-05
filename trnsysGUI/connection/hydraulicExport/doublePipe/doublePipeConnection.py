import dataclasses as _dc

import trnsysGUI.connection.hydraulicExport.common as _com
import trnsysGUI.globalNames as _gnames
import trnsysGUI.massFlowSolver.names as _mnames
import trnsysGUI.temperatures as _temps


@_dc.dataclass
class DoublePipe:
    name: str
    inputPort: _com.InputPort
    outputPort: _com.OutputPort


@_dc.dataclass
class ExportHydraulicDoublePipeConnection:
    displayName: str
    coldPipe: DoublePipe
    hotPipe: DoublePipe

    def getOutputTemperatureVariableName(self, pipe: DoublePipe) -> str:
        self._ensureIsOurPipe(pipe)
        return _temps.getTemperatureVariableName(
            shallRenameOutputInHydraulicFile=False, componentDisplayName=self.displayName, nodeName=pipe.name
        )

    def getInitialOutputTemperatureVariableName(self, pipe: DoublePipe) -> str:
        if pipe is self.coldPipe:
            return _gnames.DoublePipes.INITIAL_COLD_TEMPERATURE

        if pipe is self.hotPipe:
            return _gnames.DoublePipes.INITIAL_HOT_TEMPERATURE

        raise ValueError("`pipe` single pipe does not belong to this double pipe")

    def getCanonicalMassFlowRateVariableName(self, pipe: DoublePipe) -> str:
        self._ensureIsOurPipe(pipe)
        return _mnames.getCanonicalMassFlowVariableName(componentDisplayName=self.displayName, pipeName=pipe.name)

    def _ensureIsOurPipe(self, pipe: DoublePipe) -> None:
        if pipe not in [self.coldPipe, self.hotPipe]:
            raise ValueError("Not our pipe.", pipe)


ExportDoublePipeConnection = _com.GenericConnection[ExportHydraulicDoublePipeConnection]
