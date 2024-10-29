import pathlib as _pl
from unittest.mock import Mock

import PyQt5.QtWidgets as _qtw
import pytest
import pytrnsys.utils.log as _ulog

import tests.trnsysGUI.constants as testConstants
import trnsysGUI.mainWindow as mw
import trnsysGUI.menus.hydraulicModesMenu.hydraulicModes as hm
import trnsysGUI.project as prj
from trnsysGUI import constants
from trnsysGUI.recentProjectsHandler import RecentProjectsHandler


class TestHydraulicModesGui:

    @pytest.fixture()
    def project(self):
        project = prj.LoadProject(_pl.Path(testConstants.PATH_TO_DIAGRAM_WITH_TAP_FOR_REGIMES))
        return project

    def testGenerateModesTemplate(self, monkeypatch, project):
        mockedMessageBox = Mock()
        monkeypatch.setattr("trnsysGUI.messageBox.MessageBox.create", mockedMessageBox)
        monkeypatch.setattr(
            "trnsysGUI.pythonInterface.regimeExporter.exportRegimes.exportRegimeTemplate",
            lambda jsonFilePath, modesTemplateFile: None,
        )

        hm.createModesTemplate(project)

        mockedMessageBox.assert_called_once_with(messageText=constants.MODE_CSV_CRATED, buttons=[_qtw.QMessageBox.Ok])

    def testRunModesFailure(self, qtbot, project, monkeypatch):
        mockedMessageBox = Mock()
        monkeypatch.setattr("trnsysGUI.messageBox.MessageBox.create", mockedMessageBox)
        monkeypatch.setattr(RecentProjectsHandler, RecentProjectsHandler.save.__name__, lambda: None)
        logger = _ulog.getOrCreateCustomLogger("root", "INFO")
        mainWindow = mw.MainWindow(logger, project)
        qtbot.addWidget(mainWindow)

        hm.runModes(project, mainWindow)

        mockedMessageBox.assert_called_once_with(
            messageText=constants.ERROR_RUNNING_MODES,
            informativeText=testConstants.EXPECTED_EXCEPTION_TEXT,
            buttons=[_qtw.QMessageBox.Ok],
        )
