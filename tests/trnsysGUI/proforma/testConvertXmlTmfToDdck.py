import dataclasses as _dc
import pathlib as _pl
import pkgutil as _pu
import pprint as _pp
import typing as _tp

import pytest as _pt
import xmlschema as _xml

import pytrnsys.utils.result as _res

import trnsysGUI.proforma.convertXmlTmfToDdck as _pc
import trnsysGUI.proforma.dialogs.editHydraulicConnectionsDialog as _ehcd

_DATA_DIR_PATH = _pl.Path(__file__).parent / "data"
_INPUT_DIR_PATH = _DATA_DIR_PATH / "input"


def testValidateXmlTmf() -> None:
    schema = _getSchema()

    xmlFilePath = _INPUT_DIR_PATH / "Type71.xmltmf"
    schema.validate(xmlFilePath)


def testDecodeXmlTmf() -> None:
    schema = _getSchema()

    xmlFilePath = _INPUT_DIR_PATH / "Type71.xmltmf"
    deserializedData = schema.to_dict(xmlFilePath)
    _pp.pprint(deserializedData, indent=4)


def _getSchema() -> _xml.XMLSchema11:
    data = _pu.get_data(_pc.__name__, "xmltmf.xsd")
    assert data
    string = data.decode("UTF8")
    schema = _xml.XMLSchema11(string)
    return schema


@_dc.dataclass
class TestCase:
    inputFilePath: _pl.Path
    actualOutputFilePath: _pl.Path
    expectedOutputFilePath: _pl.Path

    @property
    def fileStem(self) -> str:
        return self.inputFilePath.stem

    @staticmethod
    def createForStem(fileNameStem: str) -> "TestCase":
        inputFilePath = (_INPUT_DIR_PATH / fileNameStem).with_suffix(".xmltmf")
        actualOutputFilePath = (_DATA_DIR_PATH / "actual" / fileNameStem).with_suffix(".ddck")
        expectedOutputFilePath = (_DATA_DIR_PATH / "expected" / fileNameStem).with_suffix(".ddck")
        testCase = TestCase(inputFilePath, actualOutputFilePath, expectedOutputFilePath)
        return testCase


def _getTestCases() -> _tp.Iterable[TestCase]:
    inputDirPath = _INPUT_DIR_PATH
    for inputFilePath in inputDirPath.iterdir():
        assert inputFilePath.is_file()

        yield TestCase.createForStem(inputFilePath.stem)


@_pt.mark.parametrize("testCase", [_pt.param(tc, id=tc.fileStem) for tc in _getTestCases()])
def testConvertXmlTmfStringToDdck(testCase: TestCase, monkeypatch) -> None:
    xmlFileContent = testCase.inputFilePath.read_text(encoding="utf8")

    def returnConnectionsUnmodified(connections, _):
        return connections

    monkeypatch.setattr(
        _ehcd.EditHydraulicConnectionsDialog,
        _ehcd.EditHydraulicConnectionsDialog.showDialogAndGetResults.__name__,
        returnConnectionsUnmodified,
    )

    result = _pc.convertXmlTmfStringToDdck(xmlFileContent, suggestedHydraulicConnections=None)

    if testCase.expectedOutputFilePath.is_file():
        assert isinstance(result, str)
        actualDdckContent = _res.value(result)

        testCase.actualOutputFilePath.write_text(result)
        expectedDdckContent = testCase.expectedOutputFilePath.read_text(encoding="utf8")
        assert actualDdckContent == expectedDdckContent
    else:
        assert isinstance(result, _res.Error)
        print(result.message)
        assert not testCase.actualOutputFilePath.is_file()
