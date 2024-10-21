import pathlib as _pl
import PyQt5.QtWidgets as _qtw


from tests.trnsysGUI.constants import PROJECT_1, PROJECT_2
from trnsysGUI.messageBox import MessageBox
from trnsysGUI.project import checkIfProjectEnviromentIsValid, LoadProject, MigrateProject


class TestProject:

    def testIsValidProjectEnviromentValid(self, monkeypatch):
        monkeypatch.setattr(_pl.Path, _pl.Path.is_dir.__name__, lambda b: True)

        isValid = checkIfProjectEnviromentIsValid(PROJECT_1.parent, PROJECT_1)

        assert isValid == LoadProject(PROJECT_1)

    def testIsValidProjectEnviromentInvalid(self, monkeypatch):
        monkeypatch.setattr(MessageBox, MessageBox.create.__name__, lambda messageText: _qtw.QMessageBox.Yes)
        monkeypatch.setattr("trnsysGUI.project.getExistingEmptyDirectory", lambda startingDirectoryPath: PROJECT_2)

        isValid = checkIfProjectEnviromentIsValid(PROJECT_2.parent, PROJECT_1)

        assert isValid == MigrateProject(PROJECT_1, PROJECT_2)
