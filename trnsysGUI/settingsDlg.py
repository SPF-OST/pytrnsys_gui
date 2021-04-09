__all__ = ["SettingsDlg", "MaybeCancelled", "CANCELLED"]

import pathlib as _pl
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtWidgets as _widgets

import trnsysGUI.settings as _settings


class _Cancelled:
    pass


CANCELLED = _Cancelled()

_TCo = _tp.TypeVar("_TCo", covariant=True)

MaybeCancelled = _tp.Union[_TCo, _Cancelled]


class SettingsDlg(_widgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        settings = _settings.Settings.tryLoadOrNone()
        oldTrnsysPath = settings.trnsysBinaryDirPath if settings else ""

        label = _widgets.QLabel("Trnsys Path:")
        self.lineEdit = _widgets.QLineEdit(oldTrnsysPath)
        self.lineEdit.setDisabled(True)

        setButton = _widgets.QPushButton("Set Trnsys Path")
        setButton.setFixedWidth(100)
        setButton.clicked.connect(self._onSetButtonClicked)

        layout = _widgets.QHBoxLayout()
        layout.addWidget(label)
        layout.addWidget(setButton)

        okButton = _widgets.QPushButton("Done")
        okButton.setFixedWidth(50)
        okButton.clicked.connect(self._onOkButtonClicked)
        buttonLayout = _widgets.QHBoxLayout()
        buttonLayout.addWidget(okButton, alignment=_qtc.Qt.AlignCenter)

        overallLayout = _widgets.QVBoxLayout()
        overallLayout.addLayout(layout)
        overallLayout.addLayout(buttonLayout)
        self.setLayout(overallLayout)
        self.setFixedWidth(800)

        self.setWindowTitle("Set Paths")

        self._settings: MaybeCancelled[_settings.Settings] = CANCELLED

    @staticmethod
    def showDialogAndGetSettings(parent=None) -> MaybeCancelled[_settings.Settings]:
        dialog = SettingsDlg(parent)
        dialog.exec()
        return dialog._settings

    def _onSetButtonClicked(self) -> None:
        newTrnsysPath = str(_widgets.QFileDialog.getExistingDirectory(self, "Select Trnsys Path"))
        self.lineEdit.setText(newTrnsysPath)

    def _onOkButtonClicked(self) -> None:
        settings = _settings.Settings.tryLoadOrNone()

        newTrnsysPath = _pl.Path(self.lineEdit.text())

        if not settings and not newTrnsysPath:
            msgBox = _widgets.QMessageBox()
            msgBox.setText("Please set Trnsys path!")
            msgBox.exec()
            return

        if settings:
            settings.trnsysBinaryDirPath = newTrnsysPath
        else:
            settings = _settings.Settings.create(newTrnsysPath)

        self._settings = settings

        self.close()

    def cancel(self) -> None:
        self._settings = CANCELLED
        self.close()
