import collections.abc as _cabc
import dataclasses as _dc
import pathlib as _pl

import pytest as _pt

import pytrnsys.utils.result as _res

import trnsysGUI.components.plugin.specification.load as _load
import trnsysGUI.components.plugin.specification.model as _model


_BASE_RESOURCE_PATH = str(_pl.Path(__file__).parents[1] / "data")


@_dc.dataclass
class TestCase:
    id: str
    typeName: str
    expectedResult: _res.Result[_model.Specification]


def getTestCases() -> _cabc.Iterable[TestCase]:
    yield TestCase(
        "OK",
        "thermallyDrivenHeatPump",
        _model.Specification(
            defaultName="AbsHP",
            description="Ab-/Adsorption heat pump",
            connections=[
                _model.Connection(
                    name="cold",
                    input=_model.Port(name=None, position=(0, 0)),
                    output=_model.Port(name=None, position=(0, 0)),
                ),
                _model.Connection(
                    name="medium",
                    input=_model.Port(name=None, position=(0, 0)),
                    output=_model.Port(name=None, position=(0, 0)),
                ),
                _model.Connection(
                    name="hot",
                    input=_model.Port(name=None, position=(0, 0)),
                    output=_model.Port(name=None, position=(0, 0)),
                ),
            ],
            size=(0, 0),
        ),
    )
    yield TestCase(
        "Invalid",
        "thermallyDrivenHeatPumpInvalidSpec",
        _res.Error(
            f"""\
Error in specification `{_BASE_RESOURCE_PATH}/thermallyDrivenHeatPumpInvalidSpec/spec.yaml`:
1 validation error for Specification
connections.0.input.position
  Field required [type=missing, input_value={{'name': 'foo'}}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.7/v/missing"""
        ),
    )

    yield TestCase(
        "Missing",
        "thermallyDrivenHeatPumpMissingSpec",
        _res.Error(f"`{_BASE_RESOURCE_PATH}/thermallyDrivenHeatPumpMissingSpec/spec.yaml` could not be found."),
    )
    yield TestCase(
        "SyntaxError",
        "thermallyDrivenHeatPumpSyntaxError",
        _res.Error(
            f"""\
Syntax error in `{_BASE_RESOURCE_PATH}/thermallyDrivenHeatPumpSyntaxError/spec.yaml`:
while parsing a flow sequence
  in "<byte string>", line 13, column 17:
          position: [0, 0
                    ^
expected ',' or ']', but got ':'
  in "<byte string>", line 14, column 9:
      - name: hot
            ^"""
        ),
    )


class TestLoad:
    @_pt.mark.parametrize("testCase", [_pt.param(tc, id=tc.id) for tc in getTestCases()])
    def test(self, testCase: TestCase) -> None:
        loader = self._createLoader()
        actualResult = loader.load(testCase.typeName)
        assert actualResult == testCase.expectedResult

    @staticmethod
    def _createLoader() -> _load.Loader:
        fileResourceLoader = _load.FileResourceLoader()
        loader = _load.Loader(_BASE_RESOURCE_PATH, fileResourceLoader)
        return loader
