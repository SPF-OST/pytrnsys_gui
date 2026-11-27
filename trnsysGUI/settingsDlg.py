import pathlib as _pl
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtWidgets as _widgets

import trnsysGUI.runConfig as _rc
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

        libraryLayout = self._createDdckLibraryLayout()

        self._okButton = _widgets.QPushButton("Done")
        self._okButton.setFixedWidth(50)
        self._okButton.clicked.connect(self._onOkButtonClicked)
        canOk = bool(settings)
        self._okButton.setEnabled(canOk)
        buttonLayout = _widgets.QHBoxLayout()
        buttonLayout.addWidget(self._okButton, alignment=_qtc.Qt.AlignCenter)

        overallLayout = _widgets.QVBoxLayout()
        overallLayout.addLayout(layout)
        overallLayout.addLayout(libraryLayout)
        overallLayout.addLayout(buttonLayout)
        self.setLayout(overallLayout)
        self.setFixedWidth(800)

        self.setWindowTitle("Set Paths")

        self._settings: _cancel.MaybeCancelled[_settings.Settings] = (
            _cancel.CANCELLED
        )

    def _createDdckLibraryLayout(self) -> _widgets.QHBoxLayout:
        label = _widgets.QLabel("ddck library:")

        self._libraryLineEdit = _widgets.QLineEdit(
            _rc.loadConfiguredLibraryPath()
        )
        autoDetectedPath = _rc.findDefaultDdckLibrary()
        self._libraryLineEdit.setPlaceholderText(
            f"Auto-detected: {autoDetectedPath}"
            if autoDetectedPath
            else "Not found: please set the path to pytrnsys_gui's data/ddck"
        )
        self._libraryLineEdit.setToolTip(
            "Folder with the default ddck files (data/ddck of the pytrnsys_gui"
            " repository, `COMMON$` in run configs). Leave empty to"
            " auto-detect it."
        )

        browseButton = _widgets.QPushButton("Browse...")
        browseButton.setFixedWidth(100)
        browseButton.clicked.connect(self._onBrowseLibraryClicked)

        autoButton = _widgets.QPushButton("Auto-detect")
        autoButton.setFixedWidth(100)
        autoButton.clicked.connect(self._libraryLineEdit.clear)

        libraryLayout = _widgets.QHBoxLayout()
        libraryLayout.addWidget(label)
        libraryLayout.addWidget(self._libraryLineEdit)
        libraryLayout.addWidget(browseButton)
        libraryLayout.addWidget(autoButton)
        return libraryLayout

    def _onBrowseLibraryClicked(self) -> None:
        startDirPath = self._libraryLineEdit.text() or str(
            _rc.findDefaultDdckLibrary() or ""
        )
        dirPath = _widgets.QFileDialog.getExistingDirectory(
            self, "Select ddck library", startDirPath
        )
        if dirPath:
            self._libraryLineEdit.setText(dirPath)

    @staticmethod
    def showDialogAndGetSettings(
        parent=None,
    ) -> _cancel.MaybeCancelled[_settings.Settings]:
        dialog = SettingsDlg(parent)
        dialog.exec()
        return dialog._settings  # pylint: disable=protected-access

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

        _rc.saveConfiguredLibraryPath(self._libraryLineEdit.text().strip())

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
