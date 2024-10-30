import trnsysGUI.connection.hydraulicExport.doublePipe.getDoublePipeEnergyBalanceEquations as _ge

SIMULATED_PIPE = _ge.DoublePipe("Bob", "BobCold", "BobHot", True)
DUMMY_PIPE = _ge.DoublePipe("Bob", "BobCold", "BobHot", False)

SIMULATED_EQUATIONS = """*** Double pipe energy balance
EQUATIONS 5
dpPipeConvectedTot = BobBobColdConv + BobBobHotConv
dpToFFieldTot = BobSlFf
dpPipeIntTot = BobBobColdInt + BobBobHotInt
dpSoilIntTot = BobSlInt
dpImbalance = dpPipeConvectedTot - dpToFFieldTot  - dpPipeIntTot - dpSoilIntTot
"""


class TestGetDoublePipeEnergyBalanceEquations:
    def testSimulatedPipe(self):
        equations = _ge.getDoublePipeEnergyBalanceEquations([SIMULATED_PIPE])
        assert equations == SIMULATED_EQUATIONS

    def testDummyPipe(self):
        equations = _ge.getDoublePipeEnergyBalanceEquations([DUMMY_PIPE])
        assert equations == ""

    def testMixing(self):
        equations = _ge.getDoublePipeEnergyBalanceEquations(
            [SIMULATED_PIPE, DUMMY_PIPE]
        )
        assert equations == SIMULATED_EQUATIONS
