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
        "thermDrivenHP",
        _model.Specification(
            defaultName="thDrivenHp",
            description="Thermally driven heat pump",
            connections=[
                _model.Connection(
                    name="Cold",
                    input=_model.Port(name=None, position=(0, 20)),
                    output=_model.Port(name=None, position=(0, 100)),
                ),
                _model.Connection(
                    name="Medium",
                    input=_model.Port(name=None, position=(120, 20)),
                    output=_model.Port(name=None, position=(120, 100)),
                ),
                _model.Connection(
                    name="Hot",
                    input=_model.Port(name=None, position=(80, 0)),
                    output=_model.Port(name=None, position=(40, 0)),
                ),
            ],
            size=(120, 120),
        ),
    )
    yield TestCase(
        "Invalid",
        "thermDrivenHPInvalidSpec",
        _res.Error(
            f"""\
Error in specification `{_BASE_RESOURCE_PATH}/thermDrivenHPInvalidSpec/spec.yaml`:
1 validation error for Specification
connections.0.output.position
  Input should be a valid tuple [type=tuple_type, input_value=100, input_type=int]
    For further information visit https://errors.pydantic.dev/2.7/v/tuple_type"""
        ),
    )

    yield TestCase(
        "Missing",
        "thermDrivenHPMissingSpec",
        _res.Error(
            f"`{_BASE_RESOURCE_PATH}/thermDrivenHPMissingSpec/spec.yaml` could not be found."
        ),
    )
    yield TestCase(
        "SyntaxError",
        "thermDrivenHPSyntaxError",
        _res.Error(
            f"""\
Syntax error in `{_BASE_RESOURCE_PATH}/thermDrivenHPSyntaxError/spec.yaml`:
while parsing a flow sequence
  in "<byte string>", line 13, column 17:
          position: [120, 100
                    ^
expected ',' or ']', but got ':'
  in "<byte string>", line 14, column 9:
      - name: hot
            ^"""
        ),
    )


class TestLoad:
    @_pt.mark.parametrize(
        "testCase", [_pt.param(tc, id=tc.id) for tc in getTestCases()]
    )
    def test(self, testCase: TestCase) -> None:
        loader = self._createLoader()
        actualResult = loader.load(testCase.typeName)
        if _res.isError(actualResult):
            error = _res.error(actualResult)
            print(error.message)

        assert actualResult == testCase.expectedResult

    @staticmethod
    def _createLoader() -> _load.Loader:
        fileResourceLoader = _load.FileResourceLoader()
        loader = _load.Loader(_BASE_RESOURCE_PATH, fileResourceLoader)
        return loader
