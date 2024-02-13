import typing as _tp

import pytest as _pt

import pytrnsys.utils.result as _res
import trnsysGUI.componentAndPipeNameValidator as _cpn
import trnsysGUI.idGenerator as _idgen

_EXISTING_NAMES = ["SCnrA_QSnkA", "SCnrB_QSnkB", "SCnrC_QSnkC", "SCnrD_QSnkD"]
_VALID_NAMES = [
    "nameisnoncapitalwithonlyletters",
    "NameIsCamelCaseWithOnlyLetters",
    "name1contains2numbers3without4capital5letters",
    "name1contains2numbers3with4CAPITAL5LETTERS",
    "_name_with_underscores_",
]
_INVALID_CHARACTER_ERROR_MESSAGE = (
    "Found unacceptable characters (this includes spaces at the start and the end)\n"
    "Please use only letters, numbers, and underscores."
)
_NAME_ALREADY_EXISTS_ERROR_MESSAGE = "Name already exist (note: names are case insensitive)."

_NAMES_AND_ERROR_MESSAGES = [
    (" name with spaces ", _INVALID_CHARACTER_ERROR_MESSAGE),
    ("name%with^strange$characters+", _INVALID_CHARACTER_ERROR_MESSAGE),
    (
        "1337",
        _INVALID_CHARACTER_ERROR_MESSAGE,
    ),
    (
        "1337_2556",
        _INVALID_CHARACTER_ERROR_MESSAGE,
    ),
    ("", "Please enter a name."),
    ("SCnrA_QSnkA", _NAME_ALREADY_EXISTS_ERROR_MESSAGE),
    ("SCnra_QSnkA", _NAME_ALREADY_EXISTS_ERROR_MESSAGE),
]

_INVALID_NAMES = [n for n, _ in _NAMES_AND_ERROR_MESSAGES]


class _DummyDdckFileOrDirNamesProvider(_cpn.AbstractDdckDirFileOrDirNamesProvider):
    @_tp.override
    def hasFileOrDirName(self, name: str) -> bool:
        raise AssertionError("Shouldn't get here")


class TestComponentAndPipeNameValidator:
    @_pt.mark.parametrize(["newName", "expectedErrorMessage"], _NAMES_AND_ERROR_MESSAGES)
    def testValidateNameInvalidNames(self, newName: str, expectedErrorMessage: str) -> None:
        validator = self._createValidator()
        result = validator.validateName(newName, checkDdckFolder=False)

        assert _res.isError(result)

        errorMessage = _res.error(result).message
        assert errorMessage == expectedErrorMessage

    @_pt.mark.parametrize("newName", _VALID_NAMES)
    def testValidateNameValidNames(self, newName: str) -> None:
        validator = self._createValidator()
        result = validator.validateName(newName, checkDdckFolder=False)

        assert not _res.isError(result)

    @staticmethod
    def _createValidator() -> _cpn.ComponentAndPipeNameValidator:
        validator = _cpn.ComponentAndPipeNameValidator(
            _EXISTING_NAMES, _DummyDdckFileOrDirNamesProvider(), _idgen.IdGenerator()
        )
        return validator
