import trnsysGUI.connection.connectorsAndPipesExportHelpers as _helper

_EXPECTED_TYPE_2221_UNIT_TEXT = """\
UNIT 11 TYPE 2221
PARAMETERS 2
mfrSolverAbsTol
dpTIniCold
INPUTS 3
MSCnr1Cold_A TSCnr1_DTeeACold TSCnr1_QSrc1
***
0 dpTIniCold dpTIniCold
EQUATIONS 1
TSCnr1Cold = [11,1]

"""


class TestConnectorsAndPipesExportHelpers:
    def testExportType2221(self):
        unitText = _helper.getIfThenElseUnit(
            unitNumber=11,
            outputTemp="TSCnr1Cold",
            initialTemp="dpTIniCold",
            massFlowRate="MSCnr1Cold_A",
            posFlowInputTemp="TSCnr1_DTeeACold",
            negFlowInputTemp="TSCnr1_QSrc1",
            extraNewlines="\n\n",
        )

        assert unitText == _EXPECTED_TYPE_2221_UNIT_TEXT
