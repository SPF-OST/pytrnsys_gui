import dataclasses as _dc
import pathlib as _pl
from collections import abc as _cabc

import pytest as _pt

import pytrnsys.utils.result as _res
import pytrnsys.utils.warnings as _warn

import trnsysGUI.dlls.freeze as _freeze

from . import _inputs


@_dc.dataclass
class TestCase:
    id: str
    logFileContent: str
    expectedResult: _res.Result[_warn.ValueWithWarnings[_cabc.Sequence[_pl.Path]]]


def getTestCases() -> _cabc.Iterable[TestCase]:
    yield TestCase(
        "noDuplicates",
        _inputs.NO_DUPLICATES_CONTENT,
        _warn.ValueWithWarnings.create(
            [
                _pl.Path("atype1924_v38-rel.dll"),
                _pl.Path("aType929_v10-rel.dll"),
                _pl.Path("TRNDll.dll"),
                _pl.Path("type2221-fortrnsys-main-e62e03e-release.dll"),
                _pl.Path("type931-fortrnsys-main-e62e03e-release.dll"),
                _pl.Path("Type9352-fortrnsys-main-e62e03e-release.dll"),
                _pl.Path("type9511.dll"),
                _pl.Path("type991-fortrnsys-main-e62e03e-release.dll"),
                _pl.Path("Type993-fortrnsys-main-e62e03e-release.dll"),
            ]
        ),
    )

    yield TestCase(
        "duplicates",
        _inputs.DUPLICATES_CONTENT,
        _warn.ValueWithWarnings.create(
            [
                _pl.Path("atype1924_v38-rel.dll"),
                _pl.Path("aType929_v10-rel.dll"),
                _pl.Path("aType931.dll"),
                _pl.Path("aType993-v1-rel.dll"),
                _pl.Path("TRNDll.dll"),
                _pl.Path("type2221-fortrnsys-main-e62e03e-release.dll"),
                _pl.Path("Type9352-fortrnsys-main-e62e03e-release.dll"),
                _pl.Path("type9511.dll"),
                _pl.Path("type991-fortrnsys-main-e62e03e-release.dll"),
            ],
            """\
Multiple implementations for the following types were found ("=>" indicates actually
used implementations):

Type 929:
 => aType929_v10-rel.dll
    TESSHVACLibrary_v17.2.01_Release.dll

Type 931:
 => aType931.dll
    type931-fortrnsys-main-e62e03e-release.dll

Type 993:
 => aType993-v1-rel.dll
    Type993-fortrnsys-main-e62e03e-release.dll

Type 9511:
 => type9511.dll
    type9511-fortranTypes-dynamic-storage-c810a216-release.dll-ignore
    type9511-fortranTypes-master-1916e5ce-release.dll-ignore
    type9511-fortranTypes-master-f6a76470.dll-ignore
""",
        ),
    )

    yield TestCase(
        "missingTypes",
        _inputs.MISSING_TYPES_CONTENT,
        _res.Error(
            """\
No DLLs implementing the following types were found:

    9352

"""
        ),
    )


class TestFreeze:
    @_pt.mark.parametrize("testCase", [_pt.param(t, id=t.id) for t in getTestCases()])
    def testGetUsedDllRelativePaths(self, testCase: TestCase) -> None:
        actualResult = _freeze.getUsedDllRelativePaths(testCase.logFileContent)
        assert actualResult == testCase.expectedResult
