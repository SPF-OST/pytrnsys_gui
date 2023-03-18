import pytest as _pt
import trnsysGUI.ddckFields.getHeaderAndParametersGenerator as _ghp
import trnsysGUI.ddckFields.headerAndParameters.getDoublePipeConnectionHeaderAndParameters as _gdpchp
import tests.trnsysGUI.ddckFields.headerAndParameters.doublePipeConnectionHeaderAndParameters as _dpchp


class _StrictMock:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class TestGetHeaderAndParameters:
    def testGetHeaderAndParametersRaises(self):
        with _pt.raises(ValueError):
            _ghp.getHeaderAndParametersGenerator("test")

    def testDoublePipeConnection(self):
        textBlockGenerator = _ghp.getHeaderAndParametersGenerator("DoublePipeConnection")
        assert textBlockGenerator == _gdpchp.getDoublePipeConnectionHeaderAndParameters

    def testDoublePipeConnectionText(self):
        textBlockGenerator = _ghp.getHeaderAndParametersGenerator("DoublePipeConnection")
        connection = _StrictMock(lengthInM=2.0, displayName="Con35")
        text = textBlockGenerator(connection, 12)
        assert text == _dpchp.HEADER_AND_PARAMETERS
