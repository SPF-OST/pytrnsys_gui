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
        project = prj.LoadProject(
            _pl.Path(testConstants.PATH_TO_DIAGRAM_WITH_TAP_FOR_REGIMES)
        )
        return project

    def runModesSetup(
        self, qtbot, monkeypatch, project, csv
    ) -> tuple[Mock, mw.MainWindow]:  # type: ignore[name-defined]
        mockedMessageBox = Mock()
        monkeypatch.setattr(
            "trnsysGUI.messageBox.MessageBox.create", mockedMessageBox
        )
        monkeypatch.setattr(
            RecentProjectsHandler,
            RecentProjectsHandler.save.__name__,
            lambda: None,
        )
        monkeypatch.setattr(
            _qtw.QFileDialog,
            "getOpenFileName",
            lambda caption, filter, directory: (csv, "*.csv"),
        )
        logger = _ulog.getOrCreateCustomLogger("root", "INFO")
        mainWindow = mw.MainWindow(logger, project)  # type: ignore[attr-defined]
        qtbot.addWidget(mainWindow)

        return (mockedMessageBox, mainWindow)

    def testGenerateModesTemplate(self, monkeypatch, project):
        """this test is on gui level and only interacts with the file system"""
        mockedMessageBox = Mock()
        monkeypatch.setattr(
            "trnsysGUI.messageBox.MessageBox.create", mockedMessageBox
        )
        monkeypatch.setattr(
            "trnsysGUI.pythonInterface.regimeExporter.exportRegimes.exportRegimeTemplate",
            lambda jsonFilePath, modesTemplateFile: None,
        )

        hm.createModesTemplate(project)

        mockedMessageBox.assert_called_once_with(
            messageText=constants.MODES_CSV_CREATED,
            informativeText=constants.MODES_CSV_CREATED_ADDITIONAL,
            buttons=[_qtw.QMessageBox.Ok],
        )

    def testRunModesFileNotFoundFailure(self, qtbot, project, monkeypatch):
        doesNotExistCsv = "doesNotExist.csv"
        mockedMessageBox, mainWindow = self.runModesSetup(
            qtbot, monkeypatch, project, doesNotExistCsv
        )

        hm.runModes(project, mainWindow)

        mockedMessageBox.assert_called_once_with(
            messageText=constants.ERROR_RUNNING_MODES_FILE_NOT_FOUND,
            informativeText=str(
                testConstants.PATH_TO_DIAGRAM_WITH_TAP_FOR_REGIMES.parent
                / doesNotExistCsv
            ),
            buttons=[_qtw.QMessageBox.Ok],
        )

    def testRunModesInvalidDckUnmodifiedDlls(
        self, qtbot, project, monkeypatch
    ):
        """When using the unmodified dlls for trnsys, in a diagram that requires the modified ones.
        Trnsys will fail and not create the prt file, which causes a FileNotFound exception
        """
        mockedMessageBox, mainWindow = self.runModesSetup(
            qtbot, monkeypatch, project, "regimes.csv"
        )
        monkeypatch.setattr(
            "trnsysGUI.diagram.Editor.Editor.exportHydraulics",
            lambda *args, **kwargs: str(
                testConstants.DATA_FOLDER / "No_equations.dck"
            ),
        )

        hm.runModes(project, mainWindow)

        mockedMessageBox.assert_called_once_with(
            messageText=constants.ERROR_RUNNING_MODES_FILE_NOT_FOUND,
            informativeText=str(
                testConstants.PATH_TO_DIAGRAM_WITH_TAP_FOR_REGIMES.parent
                / "diagramWithTapForRegimes_Mfr.prt"
            ),
            buttons=[_qtw.QMessageBox.Ok],
        )

    def testRunModesWithBreakingPumpAndValveValues(
        self, qtbot, project, monkeypatch
    ):
        mockedMessageBox, mainWindow = self.runModesSetup(
            qtbot, monkeypatch, project, "modesWithFail.csv"
        )
        hm.runModes(project, mainWindow)

        mockedMessageBox.assert_called_once_with(
            messageText=f"{constants.ERROR_RUNNING_MODES}failure",
            informativeText=constants.ERROR_RUNNING_MODES_TRNSYS_ADDITIONAL,
            buttons=[_qtw.QMessageBox.Ok],
        )
