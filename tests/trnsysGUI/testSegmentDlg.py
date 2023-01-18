import pytest as _pt

from trnsysGUI.segmentDlg import NameContainsUnacceptableCharacters


@_pt.mark.parametrize("userInput", [
    " name with spaces ",
    "_name_with_underscores_",
    "name%with^strange$characters+",
])
def testNameContainsUnacceptableCharacters(userInput):
    response = NameContainsUnacceptableCharacters(userInput)

    assert response is True


@_pt.mark.parametrize("userInput", [
    "nameisnoncapitalwithonlyletters",
    "1337",
    "NameIsCamelCaseWithOnlyLetters",
    "name1contains2numbers3without4capital5letters",
    "name1contains2numbers3with4CAPITAL5LETTERS",
])
def testNameContainsOnlyAcceptableCharacters(userInput):
    response = NameContainsUnacceptableCharacters(userInput)

    assert response is False

    # response = "Found unacceptable characters (this includes spaces at the start and the end)\n" \
    #                "Please use only letters and numbers. "
