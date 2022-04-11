import logging as _log
import pathlib as _pl

import PyQt5.QtWidgets as _qtw
import pytest as _pt

import pytrnsys.utils.result as _res
import trnsysGUI.diagram.Editor as _de

_DATA_DIR_ = _pl.Path(__file__).parent / "data"


class TestAutomaticConnection:
    def testConnectionJson(self, request: _pt.FixtureRequest):
        actualDirPath = _DATA_DIR_ / "TRIHP_dualSource"
        expectedDirPath = _DATA_DIR_ / "expected"
        actualJsonFilePath = actualDirPath / "DdckPlaceHolderValues.json"
        expectedJsonFilePath = expectedDirPath / "DdckPlaceHolderValues.json"

        # The following line is required otherwise QT will crash
        application = _qtw.QApplication([])

        def quitApplication():
            application.quit()

        request.addfinalizer(quitApplication)

        editor = self._createEditor(actualDirPath)
        result = editor.encodeDdckPlaceHolderValuesToJson(actualJsonFilePath)
        assert not _res.isError(result)

        actualJsonText = actualJsonFilePath.read_text()  # pylint: disable=bad-option-value,unspecified-encoding
        expectedJsonText = expectedJsonFilePath.read_text()  # pylint: disable=bad-option-value,unspecified-encoding

        assert actualJsonText == expectedJsonText

    @staticmethod
    def _createEditor(projectFolderPath):  # pylint: disable=duplicate-code
        logger = _log.Logger("root")
        editor = _de.Editor(
            parent=None,
            projectFolder=str(projectFolderPath),
            jsonPath=None,
            loadValue="load",
            logger=logger,
        )
        return editor
