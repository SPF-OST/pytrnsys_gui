import pytest as _pt

import trnsysGUI.checkPipeName as _cpn

_existingNames = ["SCnrA_QSnkA", "SCnrB_QSnkB", "SCnrC_QSnkC", "SCnrD_QSnkD"]
_unacceptableNames = [" name with spaces ", "name%with^strange$characters+", "1337", "1337_2556", ""]
_acceptableNames = ["nameisnoncapitalwithonlyletters", "NameIsCamelCaseWithOnlyLetters",
                   "name1contains2numbers3without4capital5letters", "name1contains2numbers3with4CAPITAL5LETTERS",
                   "_name_with_underscores_"]
_booleans = [False] * 5
_booleans[2] = True
_RESPONSE1 = "Found unacceptable characters (this includes spaces at the start and the end)\n" \
                            "Please use only letters, numbers, and underscores."
_responsesUnacceptableNames = [_RESPONSE1] * 4
_responsesUnacceptableNames.append('Please Enter a name!')
_casesResponse = [(_unacceptableNames[i], _responsesUnacceptableNames[i]) for i in range(len(_unacceptableNames))]
_casesOnlyNumbers = [(_unacceptableNames[i], _booleans[i]) for i in range(len(_unacceptableNames))]


class TestCheckPipeName:
    @_pt.mark.parametrize("userInput", _unacceptableNames)
    def testNameContainsUnacceptableCharacters(self, userInput):
        response = _cpn.CheckPipeName(userInput, _existingNames).nameContainsUnacceptableCharacters()

        assert response is True

    @_pt.mark.parametrize("userInput", _acceptableNames)
    def testNameContainsOnlyAcceptableCharacters(self, userInput):
        response = _cpn.CheckPipeName(userInput, _existingNames).nameContainsUnacceptableCharacters()

        assert response is False

    @_pt.mark.parametrize("userInput, expectedResponse", _casesResponse)
    def testResponseToUnacceptableName(self, userInput, expectedResponse):
        errorMessage = _cpn.CheckPipeName(userInput, _existingNames).errorMessage
        assert errorMessage == expectedResponse

    @_pt.mark.parametrize("userInput, booleans", _casesOnlyNumbers)
    def testOnlyNumbers(self, userInput, booleans):
        response = _cpn.CheckPipeName(userInput, _existingNames).containsOnlyNumbers(userInput)
        assert response is booleans
