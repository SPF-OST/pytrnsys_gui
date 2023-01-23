import pytest as _pt

import trnsysGUI.segmentDlg as _sd

unacceptableNames = [" name with spaces ", "name%with^strange$characters+", "1337"]
acceptableNames = ["nameisnoncapitalwithonlyletters",  "NameIsCamelCaseWithOnlyLetters",
                   "name1contains2numbers3without4capital5letters", "name1contains2numbers3with4CAPITAL5LETTERS",
                   "_name_with_underscores_"]


# todo: apply these tests to the class segmentDlg
@_pt.mark.parametrize("userInput", unacceptableNames)
def testNameContainsUnacceptableCharacters(userInput):
    responseClass = _sd.respondToUnacceptableNaming(userInput)

    assert responseClass.unAcceptableName is True


@_pt.mark.parametrize("userInput", acceptableNames)
def testNameContainsOnlyAcceptableCharacters(userInput):
    responseClass = _sd.respondToUnacceptableNaming(userInput)

    assert responseClass.unAcceptableName is False


@_pt.mark.parametrize("userInput", unacceptableNames)
def testResponseToUnacceptableName(userInput):
    expected_response = "Found unacceptable characters (this includes spaces at the start and the end)\n" \
                        "Please use only letters and numbers."
    responseClass = _sd.respondToUnacceptableNaming(userInput)
    print(responseClass.response)
    assert responseClass.response == expected_response
