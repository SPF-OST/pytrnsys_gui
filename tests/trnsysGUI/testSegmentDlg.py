import pytest as _pt
import trnsysGUI.segmentDlg as _sd

unacceptableNames = [" name with spaces ", "name%with^strange$characters+", "1337", "1337_2556", ""]
acceptableNames = ["nameisnoncapitalwithonlyletters", "NameIsCamelCaseWithOnlyLetters",
                   "name1contains2numbers3without4capital5letters", "name1contains2numbers3with4CAPITAL5LETTERS",
                   "_name_with_underscores_"]


class TestCheckPipeName:
    # todo: apply these tests to the class segmentDlg
    @_pt.mark.parametrize("userInput", unacceptableNames)
    def testNameContainsUnacceptableCharacters(self, userInput):
        responseClass = _sd.CheckPipeName(userInput)

        assert responseClass.unacceptableName is True

    @_pt.mark.parametrize("userInput", acceptableNames)
    def testNameContainsOnlyAcceptableCharacters(self, userInput):
        responseClass = _sd.CheckPipeName(userInput)

        assert responseClass.unacceptableName is False

    @_pt.mark.parametrize("userInput", unacceptableNames)
    def testResponseToUnacceptableName(self, userInput):
        expectedResponse = "Found unacceptable characters (this includes spaces at the start and the end)\n" \
                            "Please use only letters, numbers, and underscores."
        responseClass = _sd.CheckPipeName(userInput)
        assert responseClass.response == expectedResponse

    @_pt.mark.parametrize("userInput, booleans", [
        (unacceptableNames[0], False),
        (unacceptableNames[1], False),
        (unacceptableNames[2], True),
        (unacceptableNames[3], False),
    ])
    def testOnlyNumbers(self, userInput, booleans):
        response = _sd.CheckPipeName(userInput).containsOnlyNumbers(userInput)
        assert response is booleans
