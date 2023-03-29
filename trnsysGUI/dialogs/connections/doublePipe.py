import dataclasses as _dc

import PyQt5.QtCore as _qtc
import PyQt5.QtWidgets as _qtw

import trnsysGUI.errors as _error

try:
    from . import _UI_doublePipe_generated as _gen
except ImportError as importError:
    UI_File_Missing = "Could not find the generated Python code for a .ui or .qrc file. Please run the " \
                      "`dev-tools\\generateGuiClassesFromQtCreatorStudioUiFiles.py' script from your " \
                      "`pytrnsys_gui` directory."
    raise AssertionError(UI_File_Missing) from importError


@_dc.dataclass
class ConnectionModel:
    name: str
    lengthInM: float
    shallBeSimulated: bool


class DoublePipeConnectionPropertiesDialog(_qtw.QDialog, _gen.Ui_doublePipeDialog):
    def __init__(self, connection: "ConnectionModel") -> None:
        super().__init__()
        self.setupUi(self)

        self.setWindowTitle(f'Properties of "{connection.name}"')
        self.adjustSize()

        self.model = connection

        self._configureLengthLineEdit()
        self._configureShallBeSimulatedCheckBox()

        self.lengthInMLineEdit.setText(str(self.model.lengthInM))
        self.shallBeSimulatedCheckBox.setChecked(self.model.shallBeSimulated)

    def _configureLengthLineEdit(self) -> None:
        def setLengthOrShowError() -> None:
            try:
                lengthText = self.lengthInMLineEdit.text()
                lengthInM = _parsePositiveFloat(lengthText)
                self.model.lengthInM = lengthInM
            except ValueError:
                _error.showErrorMessageBox("Could not parse the length. Please make sure it's a non-negative number.")
                self.lengthInMLineEdit.setText(str(self.model.lengthInM))

        self.lengthInMLineEdit.editingFinished.connect(setLengthOrShowError)

    def _configureShallBeSimulatedCheckBox(self) -> None:
        def setShallBeSimulated(shallBeSimulated: _qtc.Qt.CheckState) -> None:
            self.model.shallBeSimulated = shallBeSimulated == _qtc.Qt.Checked

        self.shallBeSimulatedCheckBox.stateChanged.connect(setShallBeSimulated)


def _parsePositiveFloat(text: str) -> float:
    value = float(text)

    if value <= 0:
        raise ValueError("Value must be positive.")

    return value
