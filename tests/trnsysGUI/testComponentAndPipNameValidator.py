import pytest as _pt

import trnsysGUI.componentAndPipeNameValidator as _cpn

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
    ("SCnrA_QSnkA", "Name already exist (note: names are case insensitive)."),
    ("SCnra_QSnkA", "Name already exist (note: names are case insensitive).")
]

_INVALID_NAMES = [n for n, _ in _NAMES_AND_ERROR_MESSAGES]


class TestComponentAndPipeNameValidator:
    @_pt.mark.parametrize("newName", _INVALID_NAMES)
    def testValidateNameInvalidNames(self, newName):
        validator = _cpn.ComponentAndPipeNameValidator(_EXISTING_NAMES)
        errorMessage = validator.validateName(newName)

        assert errorMessage

    @_pt.mark.parametrize("newName", _VALID_NAMES)
    def testValidateNameValidNames(self, newName):
        validator = _cpn.ComponentAndPipeNameValidator(_EXISTING_NAMES)
        errorMessage = validator.validateName(newName)

        assert not errorMessage

    @_pt.mark.parametrize("newName, expectedErrorMessage", _NAMES_AND_ERROR_MESSAGES)
    def testResponseToUnacceptableName(self, newName, expectedErrorMessage):
        validator = _cpn.ComponentAndPipeNameValidator(_EXISTING_NAMES)
        errorMessage = validator.validateName(newName)

        assert errorMessage == expectedErrorMessage
