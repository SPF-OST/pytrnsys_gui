"""The main window's handling of run configs: choosing the active config,
exporting a variant, synchronizing and preparing a run."""

import logging as _log
import pathlib as _pl
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtWidgets as _qtw

from . import active as _active
from . import library as _library
from . import model as _model
from . import sync as _sync
from . import syncDialog as _sd

_LOGGER = _log.getLogger("root")

_NAME_REF = "nameRef"


class _ConfigComboBox(_qtw.QComboBox):
    aboutToShowPopup = _qtc.pyqtSignal()

    def showPopup(self) -> None:  # pylint: disable=invalid-name
        # The configs in the project folder might have changed.
        self.aboutToShowPopup.emit()
        super().showPopup()


class RunConfigController(_qtc.QObject):
    def __init__(
        self,
        parentWidget: _qtw.QWidget,
        getProjectDirPath: _tp.Callable[[], _pl.Path],
        getTrnsysExePath: _tp.Callable[[], str],
    ) -> None:
        super().__init__(parentWidget)
        self._parentWidget = parentWidget
        self._getProjectDirPath = getProjectDirPath
        self._getTrnsysExePath = getTrnsysExePath

        self.comboBox = _ConfigComboBox()
        self.comboBox.setMinimumContentsLength(16)
        self.comboBox.setSizeAdjustPolicy(
            _qtw.QComboBox.AdjustToMinimumContentsLengthWithIcon
        )
        self.comboBox.setToolTip(
            "The active run config: the one the component windows edit and"
            ' "Run simulation" runs.'
        )
        self.comboBox.aboutToShowPopup.connect(self.refresh)
        self.comboBox.activated.connect(self._onActivated)

        self.exportAction = _qtw.QAction("Export config...", parentWidget)
        self.exportAction.setToolTip(
            "Save a copy of the active config under a new name and make it"
            " the active one."
        )
        self.exportAction.triggered.connect(self.exportConfig)

        self.syncAction = _qtw.QAction("Sync config", parentWidget)
        self.syncAction.setToolTip(
            "Add missing settings to the active config and list ddcks that"
            " are missing or not used. Nothing is removed."
        )
        self.syncAction.triggered.connect(self.syncConfig)

    # Active config

    @property
    def projectDirPath(self) -> _pl.Path:
        return self._getProjectDirPath()

    @property
    def activeConfigFileName(self) -> str:
        return _active.getActiveConfigName(self.projectDirPath)

    @property
    def activeConfigFilePath(self) -> _pl.Path:
        return self.projectDirPath / self.activeConfigFileName

    def refresh(self) -> None:
        names = list(_active.listRunConfigs(self.projectDirPath))
        activeName = self.activeConfigFileName
        if activeName not in names:
            names.insert(0, activeName)

        self.comboBox.blockSignals(True)
        try:
            self.comboBox.clear()
            for name in names:
                exists = (self.projectDirPath / name).is_file()
                text = name if exists else f"{name} (new)"
                self.comboBox.addItem(text, name)
            self.comboBox.setCurrentIndex(names.index(activeName))
        finally:
            self.comboBox.blockSignals(False)

    def loadActiveConfig(self) -> _model.RunConfig:
        """The active config, or a minimal new one if it doesn't exist yet
        (not written)."""
        return _sync.loadOrCreateConfig(
            self.activeConfigFilePath,
            self._getTrnsysExePath(),
            _library.getDdckLibraryDirPath(),
        )

    def _onActivated(self, index: int) -> None:
        name = self.comboBox.itemData(index)
        if name:
            _active.setActiveConfigName(self.projectDirPath, name)
            _LOGGER.info("Active run config: %s", name)

    # Export

    def exportConfig(self) -> None:
        sourceName = self.activeConfigFileName
        name, isOk = _qtw.QInputDialog.getText(
            self._parentWidget,
            "Export config",
            f"Name of the new config (a copy of {sourceName}):",
            text=f"{_pl.Path(sourceName).stem}_variant",
        )
        while isOk:
            errorMessage = _active.checkNewConfigName(
                self.projectDirPath, name
            )
            if not errorMessage:
                break
            name, isOk = _qtw.QInputDialog.getText(
                self._parentWidget,
                "Export config",
                f"{errorMessage}\n\nName of the new config:",
                text=name,
            )
        if not isOk:
            return

        try:
            newConfigFilePath = self.exportActiveConfigAs(name)
        except (OSError, _model.RunConfigError) as error:
            _qtw.QMessageBox.warning(
                self._parentWidget,
                "Export config",
                f"Could not export the config:\n\n{error}",
            )
            return

        self.refresh()
        _qtw.QMessageBox.information(
            self._parentWidget,
            "Export config",
            f"Saved `{newConfigFilePath.name}`, which is now the active"
            " config.",
        )

    def exportActiveConfigAs(self, name: str) -> _pl.Path:
        """Copies the active config as `<name>.config` and activates it. Its
        `nameRef` (which names the results) becomes the new config's name,
        so it doesn't overwrite the results of the original config."""
        newFileName = _active.toConfigFileName(name)
        newConfigFilePath = self.projectDirPath / newFileName

        config = self.loadActiveConfig()
        config.setString(_NAME_REF, _pl.Path(newFileName).stem)
        # E.g. `string PROJECT$`, which pytrnsys only defines itself for
        # run.config.
        _sync.syncConfig(
            config, self.projectDirPath, _library.getDdckLibraryDirPath()
        )
        config.write(newConfigFilePath)

        _active.setActiveConfigName(self.projectDirPath, newFileName)
        return newConfigFilePath

    # Sync

    def syncConfig(self) -> None:
        try:
            isNew = not self.activeConfigFilePath.is_file()
            config = self.loadActiveConfig()
            report = _sync.syncConfig(
                config, self.projectDirPath, _library.getDdckLibraryDirPath()
            )
            if report.addedSettings or isNew:
                config.write()
        except (OSError, _model.RunConfigError) as error:
            _qtw.QMessageBox.warning(
                self._parentWidget,
                "Sync config",
                f"Could not sync `{self.activeConfigFileName}`:\n\n{error}",
            )
            return

        self.refresh()

        dialog = _sd.SyncDialog(
            self.activeConfigFileName, report, self._parentWidget
        )
        if dialog.exec() != _qtw.QDialog.Accepted:
            return

        checkedDdckFiles = dialog.getCheckedDdckFiles()
        if not checkedDdckFiles:
            return

        _sync.addProjectDdcks(config, checkedDdckFiles)
        try:
            config.write()
        except OSError as error:
            _qtw.QMessageBox.warning(
                self._parentWidget,
                "Sync config",
                f"Could not write `{config.filePath}`:\n\n{error}",
            )

    # Running

    def prepareForRun(self) -> bool:
        """Creates the active config if needed and adds missing settings.
        Asks whether to run anyway if ddcks can't be found. False: don't
        run."""
        try:
            isNew = not self.activeConfigFilePath.is_file()
            config = self.loadActiveConfig()
            report = _sync.syncConfig(
                config, self.projectDirPath, _library.getDdckLibraryDirPath()
            )
            if report.addedSettings or isNew:
                config.write()
        except (OSError, _model.RunConfigError) as error:
            _qtw.QMessageBox.warning(
                self._parentWidget,
                "Run simulation",
                f"Could not prepare `{self.activeConfigFileName}`:\n\n{error}",
            )
            return False

        self.refresh()

        if not report.brokenIncludes:
            return True

        broken = "\n".join(
            f"  • {b.line}: {b.reason}" for b in report.brokenIncludes
        )
        answer = _qtw.QMessageBox.question(
            self._parentWidget,
            "Run simulation",
            f"These ddcks of `{self.activeConfigFileName}` can't be"
            f" found:\n\n{broken}\n\nRun anyway?",
            _qtw.QMessageBox.Yes | _qtw.QMessageBox.No,
            _qtw.QMessageBox.No,
        )
        return answer == _qtw.QMessageBox.Yes
