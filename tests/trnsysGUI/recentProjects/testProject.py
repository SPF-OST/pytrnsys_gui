import pathlib as _pl

import PyQt5.QtWidgets as _qtw

from tests.trnsysGUI.constants import PATH_TO_PROJECT_1, PATH_TO_PROJECT_2
from trnsysGUI.messageBox import MessageBox
from trnsysGUI.project import (
    checkIfProjectEnviromentIsValid,
    LoadProject,
    MigrateProject,
)


class TestProject:

    def testIsValidProjectEnviromentValid(self, monkeypatch):
        monkeypatch.setattr(_pl.Path, _pl.Path.is_dir.__name__, lambda b: True)

        isValid = checkIfProjectEnviromentIsValid(
            PATH_TO_PROJECT_1.parent, PATH_TO_PROJECT_1
        )

        assert isValid == LoadProject(PATH_TO_PROJECT_1)

    def testIsValidProjectEnviromentInvalid(self, monkeypatch):
        monkeypatch.setattr(
            MessageBox,
            MessageBox.create.__name__,
            lambda messageText: _qtw.QMessageBox.Yes,
        )
        monkeypatch.setattr(
            "trnsysGUI.project.getExistingEmptyDirectory",
            lambda startingDirectoryPath: PATH_TO_PROJECT_2,
        )

        isValid = checkIfProjectEnviromentIsValid(
            PATH_TO_PROJECT_2.parent, PATH_TO_PROJECT_1
        )

        assert isValid == MigrateProject(PATH_TO_PROJECT_1, PATH_TO_PROJECT_2)
