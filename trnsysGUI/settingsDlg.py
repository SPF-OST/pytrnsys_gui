import pathlib as _pl
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtWidgets as _widgets

import trnsysGUI.settings as _settings

import trnsysGUI.common.cancelled as _cancel


class SettingsDlg(_widgets.QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        settings = self._getSettings()
        oldTrnsysPath = settings.trnsysBinaryPath if settings else ""

        label = _widgets.QLabel("Trnsys Path:")
        self._lineEdit = _widgets.QLineEdit(oldTrnsysPath)
        self._lineEdit.setDisabled(True)

        setButton = _widgets.QPushButton("Set Trnsys Path")
        setButton.setFixedWidth(100)
        setButton.clicked.connect(self._onSetButtonClicked)

        layout = _widgets.QHBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self._lineEdit)
        layout.addWidget(setButton)

        self._okButton = _widgets.QPushButton("Done")
        self._okButton.setFixedWidth(50)
        self._okButton.clicked.connect(self._onOkButtonClicked)
        canOk = bool(settings)
        self._okButton.setEnabled(canOk)
        buttonLayout = _widgets.QHBoxLayout()
        buttonLayout.addWidget(self._okButton, alignment=_qtc.Qt.AlignCenter)

        overallLayout = _widgets.QVBoxLayout()
        overallLayout.addLayout(layout)
        overallLayout.addLayout(buttonLayout)
        self.setLayout(overallLayout)
        self.setFixedWidth(800)

        self.setWindowTitle("Set Paths")

        self._settings: _cancel.MaybeCancelled[_settings.Settings] = (
            _cancel.CANCELLED
        )

    @staticmethod
    def showDialogAndGetSettings(
        parent=None,
    ) -> _cancel.MaybeCancelled[_settings.Settings]:
        dialog = SettingsDlg(parent)
        dialog.exec()
        return dialog._settings  # pylint: disable=protected-class

    @staticmethod
    def _getSettings() -> _tp.Optional[_settings.Settings]:
        return _settings.Settings.tryLoadOrNone()

    def _onSetButtonClicked(self) -> None:
        oldDirPath = self._lineEdit.text()

        newBinaryPath, _ = _widgets.QFileDialog.getOpenFileName(
            self, "Select TRNSYS exe", directory=oldDirPath, filter="*.exe"
        )

        self._lineEdit.setText(newBinaryPath)

        canOk = bool(self._getSettings() or newBinaryPath)
        self._okButton.setEnabled(canOk)

    def _onOkButtonClicked(self) -> None:
        newBinaryPath = self._lineEdit.text()

        settings = self._getSettings()
        if settings:
            settings.trnsysBinaryPath = newBinaryPath
        else:
            settings = _settings.Settings.create(_pl.Path(newBinaryPath), [])

        self._settings = settings

        self.close()

    def cancel(self) -> None:
        self._settings = _cancel.CANCELLED
        self.close()


def _createSettings(
    parent=None,
) -> _settings.Settings:
    while True:
        maybeCancelled = SettingsDlg.showDialogAndGetSettings(parent)
        if not _cancel.isCancelled(maybeCancelled):
            settings = _cancel.value(maybeCancelled)
            return settings


def ensureSettingsExist() -> None:
    existingSettings = _settings.Settings.tryLoadOrNone()
    if existingSettings:
        return

    settings = _createSettings()
    settings.save()
