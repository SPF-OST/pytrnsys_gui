import pytest as _pt

from trnsysGUI.segmentDlg import respondToUnacceptableNaming

unacceptableNames = [" name with spaces ", "_name_with_underscores_", "name%with^strange$characters+"]
acceptableNames = ["nameisnoncapitalwithonlyletters", "1337", "NameIsCamelCaseWithOnlyLetters",
                   "name1contains2numbers3without4capital5letters", "name1contains2numbers3with4CAPITAL5LETTERS"]


# todo: apply these tests to the class segmentDlg
@_pt.mark.parametrize("userInput", unacceptableNames)
def testNameContainsUnacceptableCharacters(userInput):
    responseClass = respondToUnacceptableNaming(userInput)

    assert responseClass.unAcceptableName is True


@_pt.mark.parametrize("userInput", acceptableNames)
def testNameContainsOnlyAcceptableCharacters(userInput):
    responseClass = respondToUnacceptableNaming(userInput)

    assert responseClass.unAcceptableName is False


@_pt.mark.parametrize("userInput", unacceptableNames)
def testResponseToUnacceptableName(userInput):
    expected_response = "Found unacceptable characters (this includes spaces at the start and the end)\n" \
                        "Please use only letters and numbers."
    responseClass = respondToUnacceptableNaming(userInput)
    print(responseClass.response)
    assert responseClass.response == expected_response
