import trnsysGUI.massFlowSolver.networkModel as _mfn


class DoublePipeHydraulicModel:
    @property
    def coldPipe(self) -> _mfn.Pipe:
        raise NotImplementedError()

    @property
    def hotPipe(self) -> _mfn.Pipe:
        raise NotImplementedError()
