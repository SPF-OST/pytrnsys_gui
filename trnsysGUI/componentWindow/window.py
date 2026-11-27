"""The window opened by double-clicking a component in the diagram.

Tabs: "General" (name, flips), the component's own settings (mass flow,
valve, tank, ports) and "ddcks" for components with a ddck folder.

Everything is applied on OK and Cancel reverts it, except for the "Tank" and
"Ports" tabs, whose changes (heat exchangers, direct ports, port pairs)
apply immediately, as before.
"""

from __future__ import annotations

import pathlib as _pl
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

import pytrnsys.utils.result as _res
import trnsysGUI.componentDdcks as _cdd
import trnsysGUI.components.ddckFolderHelpers as _dfh
import trnsysGUI.runConfig as _rc
import trnsysGUI.runConfig.sync as _rcsync

from . import prefixedIdentifiersDialog as _pid

if _tp.TYPE_CHECKING:
    import trnsysGUI.names.rename as _rename

_DEFAULT_CONFIG_FILE_NAME = "run.config"


class _Page(_tp.Protocol):
    title: str
    widget: _qtw.QWidget

    def validate(self) -> str | None:
        """An error message if the page's values can't be applied."""

    def apply(self) -> None: ...


class ComponentWindow(
    _qtw.QDialog
):  # pylint: disable=too-many-instance-attributes
    def __init__(  # pylint: disable=too-many-arguments
        self,
        item: _tp.Any,  # BlockItem or HeatExchanger
        projectDirPath: _pl.Path,
        renameHelper: _rename.RenameHelper,
        *,
        editor: _tp.Any = None,
        openFile: _cdd.panel.OpenFileCallback | None = None,
        libraryDirPath: _pl.Path | None = None,
        configFilePath: _pl.Path | None = None,
        trnsysExePath: str = "",
        parent: _qtw.QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._item = item
        self._projectDirPath = projectDirPath
        # The active run config.
        self._configFilePath = configFilePath or (
            projectDirPath / _DEFAULT_CONFIG_FILE_NAME
        )
        self._trnsysExePath = trnsysExePath
        self._renameHelper = renameHelper
        self._isHeatExchanger = _isHeatExchanger(item)

        self._originalName: str = item.displayName
        self._supportsFlips = _supportsFlips(item)
        self._originalFlipH = bool(getattr(item, "flippedH", False))
        self._originalFlipV = bool(getattr(item, "flippedV", False))

        self.setWindowTitle(item.displayName)

        self._tabs = _qtw.QTabWidget()
        self._nameLineEdit = _qtw.QLineEdit(item.displayName)
        self._tabs.addTab(self._createGeneralPage(), "General")

        self._pages: list[_Page] = _createComponentPages(
            item, projectDirPath, renameHelper, editor
        )
        for page in self._pages:
            self._tabs.addTab(page.widget, page.title)

        self._ddckPanel: _cdd.ComponentDdckPanel | None = None
        if not self._isHeatExchanger and _dfh.hasComponentDdckFolder(item):
            self._tabs.addTab(
                self._createDdckPage(openFile, libraryDirPath), "ddcks"
            )

        buttonBox = _qtw.QDialogButtonBox(
            _qtw.QDialogButtonBox.Ok | _qtw.QDialogButtonBox.Cancel
        )
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = _qtw.QVBoxLayout(self)
        layout.addWidget(self._tabs, 1)
        layout.addWidget(buttonBox)

        self._resizeForTabs()

    def _resizeForTabs(self) -> None:
        titles = self.tabTitles
        if "ddcks" in titles:
            self.resize(1100, 650)
        elif "Tank" in titles:
            self.resize(800, 650)
        else:
            self.resize(450, self.sizeHint().height())

    # Public API

    def selectTab(self, title: str) -> None:
        for index in range(self._tabs.count()):
            if self._tabs.tabText(index) == title:
                self._tabs.setCurrentIndex(index)
                return

    @property
    def tabTitles(self) -> _tp.Sequence[str]:
        return [self._tabs.tabText(i) for i in range(self._tabs.count())]

    # Qt overrides

    def accept(self) -> None:
        if not self._apply():
            return
        super().accept()

    def reject(self) -> None:
        if self._ddckPanel and self._ddckPanel.isModified:
            answer = _qtw.QMessageBox.question(
                self,
                "Discard changes?",
                f"Discard the changes to the ddcks of {self._originalName}?",
                _qtw.QMessageBox.Discard | _qtw.QMessageBox.Cancel,
                _qtw.QMessageBox.Cancel,
            )
            if answer != _qtw.QMessageBox.Discard:
                return

        self._revertFlips()
        super().reject()

    # General page

    def _createGeneralPage(self) -> _qtw.QWidget:
        page = _qtw.QWidget()
        layout = _qtw.QFormLayout(page)
        layout.addRow("Name:", self._nameLineEdit)

        if self._supportsFlips:
            flippedH = self._originalFlipH
            flippedV = self._originalFlipV
            self._flipHCheckBox = _qtw.QCheckBox("Horizontal")
            self._flipHCheckBox.setChecked(bool(flippedH))
            self._flipHCheckBox.toggled.connect(self._item.updateFlipStateH)
            self._flipVCheckBox = _qtw.QCheckBox("Vertical")
            self._flipVCheckBox.setChecked(bool(flippedV))
            self._flipVCheckBox.toggled.connect(self._item.updateFlipStateV)

            flipLayout = _qtw.QHBoxLayout()
            flipLayout.addWidget(self._flipHCheckBox)
            flipLayout.addWidget(self._flipVCheckBox)
            flipLayout.addStretch()
            layout.addRow("Flip:", flipLayout)

        return page

    def _revertFlips(self) -> None:
        if not self._supportsFlips:
            return
        flippedH = self._originalFlipH
        flippedV = self._originalFlipV
        if bool(self._item.flippedH) != bool(flippedH):
            self._item.updateFlipStateH(bool(flippedH))
        if bool(self._item.flippedV) != bool(flippedV):
            self._item.updateFlipStateV(bool(flippedV))

    # ddck page

    def _createDdckPage(
        self,
        openFile: _cdd.panel.OpenFileCallback | None,
        libraryDirPath: _pl.Path | None,
    ) -> _qtw.QWidget:
        configFilePath = self._configFilePath
        if libraryDirPath is None:
            libraryDirPath = _rc.getDdckLibraryDirPath()
        try:
            # A new config is only written on OK.
            config = _rcsync.loadOrCreateConfig(
                configFilePath, self._trnsysExePath, libraryDirPath
            )
        except (OSError, _rc.RunConfigError) as error:
            label = _qtw.QLabel(
                f"Could not read `{configFilePath}`:\n\n{error}"
            )
            label.setWordWrap(True)
            label.setAlignment(_qtc.Qt.AlignTop | _qtc.Qt.AlignLeft)
            return label

        self._ddckPanel = _cdd.ComponentDdckPanel(
            self._originalName,
            self._projectDirPath,
            config,
            libraryDirPath,
            openFile=openFile,
        )
        return self._ddckPanel

    # Applying

    def _apply(self) -> bool:
        newName = self._nameLineEdit.text().strip()
        isRenamed = newName != self._originalName

        if isRenamed and not self._checkCanRename(newName):
            return False

        for page in self._pages:
            errorMessage = page.validate()
            if errorMessage:
                self.selectTab(page.title)
                _qtw.QMessageBox.warning(self, "Invalid value", errorMessage)
                return False

        # ddcks first, under the old name: the rename below then moves the
        # component's ddck folder and its block in the config.
        if self._ddckPanel and self._ddckPanel.isModified:
            if not self._ddckPanel.apply():
                self.selectTab("ddcks")
                return False

        if isRenamed:
            self._rename(newName)

        for page in self._pages:
            page.apply()

        return True

    def _checkCanRename(self, newName: str) -> bool:
        if self._isHeatExchanger:
            if not newName:
                _qtw.QMessageBox.warning(
                    self, "Invalid name", "The name must not be empty."
                )
                return False
            return True

        hasDdckFolder = _dfh.hasComponentDdckFolder(self._item)
        result = self._renameHelper.canRename(
            self._originalName, newName, hasDdckFolder
        )
        if _res.isError(result):
            self.selectTab("General")
            _qtw.QMessageBox.warning(
                self, "Invalid name", _res.error(result).message
            )
            return False
        return True

    def _rename(self, newName: str) -> None:
        oldName = self._originalName

        if self._isHeatExchanger:
            self._item.rename(newName)
            return

        _dfh.moveComponentDdckFolderIfNecessary(
            self._item, newName, oldName, self._projectDirPath
        )
        self._item.setDisplayName(newName)
        self._renameHelper.rename(oldName, newName)

        if _dfh.hasComponentDdckFolder(self._item):
            self._renameInConfig(oldName, newName)

    def _renameInConfig(self, oldName: str, newName: str) -> None:
        configFilePath = self._configFilePath
        if not configFilePath.is_file():
            return
        try:
            config = _rc.RunConfig.read(configFilePath)
            textBefore = config.toText()
            config.renameComponent(oldName, newName)
            # E.g. `deck CollNbModTot 360`: local variables are prefixed
            # with the component's name.
            _pid.askAndRenamePrefixedIdentifiers(
                config, oldName, newName, self
            )
            if config.toText() != textBefore:
                config.write()
        except (OSError, _rc.RunConfigError) as error:
            _qtw.QMessageBox.warning(
                self,
                "Config not updated",
                f"The component was renamed, but its ddcks in"
                f" `{configFilePath.name}` could not be renamed:\n\n{error}",
            )


# Component specific pages


class _MassFlowPage:
    title = "Mass flow"

    def __init__(self, item: _tp.Any) -> None:
        self._item = item
        self.widget = _qtw.QWidget()
        self._lineEdit = _qtw.QLineEdit(str(item.massFlowRateInKgPerH))
        validator = _qtg.QDoubleValidator()
        validator.setLocale(_qtc.QLocale.c())
        self._lineEdit.setValidator(validator)
        layout = _qtw.QFormLayout(self.widget)
        layout.addRow("Mass flow rate [kg/h]:", self._lineEdit)

    def validate(self) -> str | None:
        try:
            float(self._lineEdit.text())
        except ValueError:
            return "The mass flow rate must be a number."
        return None

    def apply(self) -> None:
        self._item.massFlowRateInKgPerH = float(self._lineEdit.text())


class _ValvePage:
    title = "Valve"

    def __init__(self, item: _tp.Any) -> None:
        self._item = item
        self.widget = _qtw.QWidget()

        self._temperingCheckBox = _qtw.QCheckBox("Tempering valve")
        self._temperingCheckBox.setChecked(bool(item.isTempering))
        self._positionSpinBox = _qtw.QDoubleSpinBox()
        self._positionSpinBox.setDecimals(1)
        self._positionSpinBox.setSingleStep(0.1)
        self._positionSpinBox.setRange(0, 1.0)
        # Can be a string when loaded from older diagrams.
        self._positionSpinBox.setValue(float(item.positionForMassFlowSolver))
        self._temperingCheckBox.toggled.connect(self._updateEnabled)
        self._updateEnabled()

        note = _qtw.QLabel(
            "A tempering valve always has valve position 0 for the mass flow"
            " solver."
        )
        note.setWordWrap(True)

        layout = _qtw.QFormLayout(self.widget)
        layout.addRow(self._temperingCheckBox)
        layout.addRow(
            "Valve position (mass flow solver):", self._positionSpinBox
        )
        layout.addRow(note)

    def _updateEnabled(self) -> None:
        self._positionSpinBox.setEnabled(
            not self._temperingCheckBox.isChecked()
        )

    def validate(self) -> str | None:
        return None

    def apply(self) -> None:
        isTempering = self._temperingCheckBox.isChecked()
        self._item.setComplexDiv(isTempering)
        position = 0.0 if isTempering else self._positionSpinBox.value()
        self._item.setPositionForMassFlowSolver(position)
        self._item.posLabel.setPlainText(str(position))


class _EmbeddedDialogPage:
    """A page showing an existing dialog whose changes apply immediately."""

    def __init__(self, title: str, dialog: _qtw.QDialog) -> None:
        self.title = title
        dialog.setWindowFlags(_qtc.Qt.Widget)
        self.widget: _qtw.QWidget = dialog

    def validate(self) -> str | None:
        return None

    def apply(self) -> None:
        pass


def _createComponentPages(
    item: _tp.Any,
    projectDirPath: _pl.Path,
    renameHelper: _rename.RenameHelper,
    editor: _tp.Any,
) -> list[_Page]:
    # pylint: disable=import-outside-toplevel  # avoid import cycles
    import trnsysGUI.GenericBlock as _gb
    import trnsysGUI.GenericPortPairDlg as _gppd
    import trnsysGUI.TVentil as _tv
    import trnsysGUI.pumpsAndTaps._pumpsAndTabsBase as _ptb
    import trnsysGUI.storageTank.ConfigureStorageDialog as _csd
    import trnsysGUI.storageTank.widget as _stw

    if isinstance(item, _ptb.PumpsAndTabsBase):
        return [_MassFlowPage(item)]

    if isinstance(item, _tv.TVentil):
        return [_ValvePage(item)]

    if isinstance(item, _stw.StorageTank):
        dialog = _csd.ConfigureStorageDialog(
            item, editor, renameHelper, str(projectDirPath), embedded=True
        )
        return [_EmbeddedDialogPage("Tank", dialog)]

    if isinstance(item, _gb.GenericBlock):  # type: ignore[attr-defined]
        return [
            _EmbeddedDialogPage(
                "Ports",
                _gppd.GenericPortPairDlg(  # type: ignore[attr-defined]
                    item, embedded=True
                ),
            )
        ]

    return []


def _supportsFlips(item: _tp.Any) -> bool:
    """As in the previous dialogs: tanks, double pipe connectors and tee
    pieces and heat exchangers can't be flipped from the dialog."""
    # pylint: disable=import-outside-toplevel  # avoid import cycles
    import trnsysGUI.connection.connectors.doublePipeConnectorBase as _dpc
    import trnsysGUI.storageTank.widget as _stw
    import trnsysGUI.teePieces.doublePipeTeePiece as _dpt

    if _isHeatExchanger(item):
        return False
    noFlipTypes = (
        _stw.StorageTank,
        _dpc.DoublePipeConnectorBase,
        _dpt.DoublePipeTeePiece,
    )
    return not isinstance(item, noFlipTypes) and hasattr(
        item, "updateFlipStateH"
    )


def _isHeatExchanger(item: _tp.Any) -> bool:
    import trnsysGUI.heatExchanger as _hx  # pylint: disable=import-outside-toplevel

    return isinstance(item, _hx.HeatExchanger)


def showComponentWindow(
    item: _tp.Any,
    editor: _tp.Any,
    renameHelper: _rename.RenameHelper,
) -> ComponentWindow:
    projectDirPath = _pl.Path(editor.projectFolder)
    mainWindow = editor.mainWindow
    openFile = getattr(mainWindow, "openFileInDdckEditor", None)
    configFilePath = getattr(mainWindow, "activeConfigFilePath", None)
    getTrnsysExePath = getattr(mainWindow, "getTrnsysExePath", None)
    window = ComponentWindow(
        item,
        projectDirPath,
        renameHelper,
        editor=editor,
        openFile=openFile,
        configFilePath=configFilePath,
        trnsysExePath=getTrnsysExePath() if getTrnsysExePath else "",
        parent=mainWindow,
    )
    window.exec()
    return window
