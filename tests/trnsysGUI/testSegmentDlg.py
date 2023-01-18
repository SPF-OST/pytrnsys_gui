import pytest as _pt

from trnsysGUI.segmentDlg import NameContainsUnacceptableCharacters


def testNameContainsUnacceptableCharacters():
    userInput = " name with spaces "
    response = NameContainsUnacceptableCharacters(userInput)

    assert response == True

