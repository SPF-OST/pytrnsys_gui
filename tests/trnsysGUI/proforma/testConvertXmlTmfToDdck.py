import dataclasses as _dc
import pathlib as _pl
import pkgutil as _pu
import pprint as _pp
import typing as _tp

import pytest as _pt
import xmlschema as _xml

import pytrnsys.ddck.replaceTokens.defaultVisibility as _dv
import pytrnsys.utils.result as _res

import trnsysGUI.common.cancelled as _cancel
import trnsysGUI.proforma.convertXmlTmfToDdck as _pc
import trnsysGUI.proforma.models as _models
import trnsysGUI.proforma.dialogs.editHydraulicConnectionsDialog as _ehcd

_DATA_DIR_PATH = _pl.Path(__file__).parent / "data"
_INPUT_DIR_PATH = _DATA_DIR_PATH / "input"


def testValidateXmlTmf() -> None:
    schema = _getSchema()

    xmlFilePath = _INPUT_DIR_PATH / "cases" / "Type71.xmltmf"
    schema.validate(xmlFilePath)


def testDecodeXmlTmf() -> None:
    schema = _getSchema()

    xmlFilePath = _INPUT_DIR_PATH / "cases" / "Type71.xmltmf"
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
        inputFilePath = (_INPUT_DIR_PATH / "cases" / fileNameStem).with_suffix(
            ".xmltmf"
        )
        actualOutputFilePath = (
            _DATA_DIR_PATH / "actual" / "cases" / fileNameStem
        ).with_suffix(".ddck")
        expectedOutputFilePath = (
            _DATA_DIR_PATH / "expected" / "cases" / fileNameStem
        ).with_suffix(".ddck")
        testCase = TestCase(
            inputFilePath, actualOutputFilePath, expectedOutputFilePath
        )
        return testCase


def _getTestCases() -> _tp.Iterable[TestCase]:
    inputDirPath = _INPUT_DIR_PATH / "cases"
    for inputFilePath in inputDirPath.iterdir():
        assert inputFilePath.is_file()

        yield TestCase.createForStem(inputFilePath.stem)


@_pt.mark.parametrize(
    "testCase", [_pt.param(tc, id=tc.fileStem) for tc in _getTestCases()]
)
def testConvertXmlTmfStringToDdck(testCase: TestCase, monkeypatch) -> None:
    xmlFileContent = testCase.inputFilePath.read_text(encoding="utf8")

    def returnConnectionsUnmodifiedWithGlobalDefaultVisibility(connections, _):
        dialogResult = _ehcd.DialogResult(
            connections, _dv.DefaultVisibility.GLOBAL
        )
        return dialogResult

    monkeypatch.setattr(
        _ehcd.EditHydraulicConnectionsDialog,
        _ehcd.EditHydraulicConnectionsDialog.showDialogAndGetResults.__name__,
        returnConnectionsUnmodifiedWithGlobalDefaultVisibility,
    )

    fileName = testCase.inputFilePath.with_suffix(".ddck").name
    result = _pc.convertXmlTmfStringToDdck(
        xmlFileContent, suggestedHydraulicConnections=None, fileName=fileName
    )

    if testCase.expectedOutputFilePath.is_file():
        assert isinstance(result, str)
        actualDdckContent = _res.value(result)

        testCase.actualOutputFilePath.write_text(result)
        expectedDdckContent = testCase.expectedOutputFilePath.read_text(
            encoding="utf8"
        )
        assert actualDdckContent == expectedDdckContent
    else:
        assert isinstance(result, _res.Error)
        print(result.message)
        assert not testCase.actualOutputFilePath.is_file()


def testConvertXmlTmfStringToDdckTwoConnections(monkeypatch) -> None:
    xmlFilePath = _INPUT_DIR_PATH / "Type5b.xmltmf"

    xmlFileContent = xmlFilePath.read_text(encoding="utf8")

    def returnConnectionsUnmodifiedWithLocalDefaultVisibility(connections, _):
        dialogResult = _ehcd.DialogResult(
            connections, _dv.DefaultVisibility.LOCAL
        )
        return dialogResult

    monkeypatch.setattr(
        _ehcd.EditHydraulicConnectionsDialog,
        _ehcd.EditHydraulicConnectionsDialog.showDialogAndGetResults.__name__,
        returnConnectionsUnmodifiedWithLocalDefaultVisibility,
    )

    outputFileName = xmlFilePath.with_suffix(".ddck").name

    suggestedHydraulicConnections = [
        _models.Connection(
            name="Cold",
            inputPort=_models.InputPort(
                name="In",
                temperature=_models.Variable(
                    tmfName="Load side inlet temperature",
                    definition=(
                        "The temperature of the fluid flowing into the load side of the "
                        'counter flow heat exchanger. NOTE: "source" and "load" are merely '
                        "convenient designations; energy will be transfered from the source side "
                        "to the load side if the source side is hotter than the load side. It "
                        "will be transfered from the load side to the source side if the load "
                        "side is hotter than the source side."
                    ),
                    order=9,
                    role="input",
                    roleOrder=3,
                    unit="C",
                    bounds="[-Inf,+Inf]",
                    defaultValue=20.0,
                ),
                massFlowRate=_models.Variable(
                    tmfName="Load side flow rate",
                    definition=(
                        "The flow rate of the fluid flowing through the load side of the "
                        'counter flow heat exchanger. NOTE: "source" and "load" are merely '
                        "convenient designations; energy will be transfered from the source side "
                        "to the load side if the source side is hotter than the load side. It "
                        "will be transfered from the load side to the source side if the load "
                        "side is hotter than the source side."
                    ),
                    order=10,
                    role="input",
                    roleOrder=4,
                    unit="kg/hr",
                    bounds="[0,+Inf]",
                    defaultValue=100.0,
                ),
            ),
            outputPort=_models.OutputPort(
                name="Out",
                temperature=_models.Variable(
                    tmfName="Load side outlet temperature",
                    definition=(
                        "The temperature of the fluid leaving the load side of the counter "
                        'flow heat exchanger. NOTE: "source" and "load" are merely convenient '
                        "designations; energy will be transfered from the source side to the load "
                        "side if the source side is hotter than the load side. It will be "
                        "transfered from the load side to the source side if the load side is "
                        "hotter than the source side."
                    ),
                    order=3,
                    role="output",
                    roleOrder=3,
                    unit="C",
                    bounds="[-Inf,+Inf]",
                    defaultValue=0.0,
                ),
                reverseTemperature=None,
            ),
            fluid=_models.Fluid(
                density=None,
                heatCapacity=_models.Variable(
                    tmfName="Specific heat of load side fluid",
                    definition=(
                        "The specific heat of the fluid flowing through the load side of the "
                        'counter flow heat exchanger. NOTE: "source" and "load" are merely '
                        "convenient designations; energy will be transfered from the source side "
                        "to the load side if the source side is hotter than the load side. It "
                        "will be transfered from the load side to the source side if the load "
                        "side is hotter than the source side."
                    ),
                    order=14,
                    role="parameter",
                    roleOrder=3,
                    unit="kJ/kg.K",
                    bounds="[0,+Inf]",
                    defaultValue=4.19,
                ),
            ),
        ),
        _models.Connection(
            name="Hot",
            inputPort=_models.InputPort(
                name="In",
                temperature=_models.Variable(
                    tmfName="Source side inlet temperature",
                    definition=(
                        "The temperature of the fluid flowing into the source side of the "
                        'counter flow heat exchanger. NOTE: "source" and "load" are merely '
                        "convenient designations; energy will be transfered from the source side "
                        "to the load side if the source side is hotter than the load side. It "
                        "will be transfered from the load side to the source side if the load "
                        "side is hotter than the source side."
                    ),
                    order=7,
                    role="input",
                    roleOrder=1,
                    unit="C",
                    bounds="[-Inf,+Inf]",
                    defaultValue=20.0,
                ),
                massFlowRate=_models.Variable(
                    tmfName="Source side flow rate",
                    definition=(
                        "The flow rate of the fluid flowing through the source side of the "
                        'counter flow heat exchanger. NOTE: "source" and "load" are merely '
                        "convenient designations; energy will be transfered from the source side "
                        "to the load side if the source side is hotter than the load side. It "
                        "will be transfered from the load side to the source side if the load "
                        "side is hotter than the source side."
                    ),
                    order=8,
                    role="input",
                    roleOrder=2,
                    unit="kg/hr",
                    bounds="[0,+Inf]",
                    defaultValue=100.0,
                ),
            ),
            outputPort=_models.OutputPort(
                name="Out",
                temperature=_models.Variable(
                    tmfName="Source side outlet temperature",
                    definition=(
                        "The temperature of the fluid leaving the source side of the counter "
                        'flow heat exchanger. NOTE: "source" and "load" are merely convenient '
                        "designations; energy will be transfered from the source side to the load "
                        "side if the source side is hotter than the load side. It will be "
                        "transfered from the load side to the source side if the load side is "
                        "hotter than the source side."
                    ),
                    order=1,
                    role="output",
                    roleOrder=1,
                    unit="C",
                    bounds="[-Inf,+Inf]",
                    defaultValue=0.0,
                ),
                reverseTemperature=None,
            ),
            fluid=_models.Fluid(
                density=None,
                heatCapacity=_models.Variable(
                    tmfName="Specific heat of source side fluid",
                    definition=(
                        "The specific heat of the fluid flowing through the source side of "
                        'the counter flow heat exchanger. NOTE: "source" and "load" are merely '
                        "convenient designations; energy will be transfered from the source side "
                        "to the load side if the source side is hotter than the load side. It "
                        "will be transfered from the load side to the source side if the load "
                        "side is hotter than the source side."
                    ),
                    order=13,
                    role="parameter",
                    roleOrder=2,
                    unit="kJ/kg.K",
                    bounds="[0,+Inf]",
                    defaultValue=4.19,
                ),
            ),
        ),
    ]

    maybeCancelled = _pc.convertXmlTmfStringToDdck(
        xmlFileContent, suggestedHydraulicConnections, fileName=outputFileName
    )

    assert not _cancel.isCancelled(maybeCancelled)
    result = maybeCancelled

    assert not _res.isError(result)
    actualContent = _res.value(result)

    assert isinstance(actualContent, str)

    actualFilePath = _DATA_DIR_PATH / "actual" / outputFileName
    actualFilePath.write_text(actualContent)

    expectedFilePath = _DATA_DIR_PATH / "expected" / outputFileName

    assert actualContent == expectedFilePath.read_text("UTF8")
