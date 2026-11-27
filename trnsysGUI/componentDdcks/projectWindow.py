# pylint: disable=too-many-lines
"""The "Project ddcks" window: the ddcks of the active config that don't
belong to a component (head, control, weather, ..., end) and the order of
everything, with each component block as one row.

Edits are made on the config in memory; files are copied and the config is
written on OK only.
"""

import dataclasses as _dc
import pathlib as _pl
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

import trnsysGUI.runConfig as _rc
import trnsysGUI.runConfig.importing as _imp
import trnsysGUI.runConfig.sync as _sync

from . import libraryBrowser as _lb
from . import panel as _panel

_COLUMN_DDCK = 0
_COLUMN_SOURCE = 1
_COLUMN_GLOBAL = 2
_COLUMN_AS = 3
_COLUMN_NAME = 4
_COLUMN_OPEN = 5

_DDCK_DIR_NAME = "ddck"


class ProjectDdckWindow(
    _qtw.QDialog
):  # pylint: disable=too-many-instance-attributes
    def __init__(  # pylint: disable=too-many-arguments
        self,
        projectDirPath: _pl.Path,
        config: _rc.RunConfig,
        libraryDirPath: _pl.Path | None,
        *,
        componentNames: _tp.Collection[str] = (),
        openFile: _panel.OpenFileCallback | None = None,
        parent: _qtw.QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._projectDirPath = projectDirPath
        self._config = config
        self._libraryDirPath = libraryDirPath
        self._componentNames = set(componentNames)
        self._openFile = openFile
        self._pendingCopies: list[_imp.CopyPlan] = []
        self._isModified = False
        self._isUpdatingTable = False

        configName = config.filePath.name if config.filePath else "?"
        self.setWindowTitle(f"Project ddcks – {configName}")
        self.resize(1150, 650)

        self._library = _lb.LibraryBrowser(
            libraryDirPath,
            projectDirPath,
            "Copy the ddck (and the data files it ASSIGNs) into a folder of"
            " the project's ddck folder (you choose which).",
        )
        self._library.importAsCopyRequested.connect(self._importAsCopy)
        self._library.useOriginalRequested.connect(self._useOriginal)
        self._library.nothingSelected.connect(
            lambda: self._showMessage(
                "Select a ddck file in the library first."
            )
        )
        self._library.libraryChanged.connect(self._setLibraryDirPath)

        self._table = _qtw.QTableWidget(0, 6)
        self._messageLabel = _qtw.QLabel()
        self._messageLabel.setWordWrap(True)
        self._orderWarningLabel = _qtw.QLabel()
        self._orderWarningLabel.setWordWrap(True)
        self._orderWarningLabel.setStyleSheet("color: #9a6700;")

        splitter = _qtw.QSplitter(_qtc.Qt.Horizontal)
        splitter.addWidget(self._library)
        splitter.addWidget(self._createSectionPanel())
        splitter.setSizes([400, 750])

        buttonBox = _qtw.QDialogButtonBox(
            _qtw.QDialogButtonBox.Ok | _qtw.QDialogButtonBox.Cancel
        )
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        header = _qtw.QLabel(
            f"Config: <code>{configName}</code> &nbsp; • &nbsp; the"
            " order below is the order of the ddcks in the deck."
        )
        header.setToolTip(str(config.filePath))

        layout = _qtw.QVBoxLayout(self)
        layout.addWidget(header)
        layout.addWidget(splitter, 1)
        layout.addWidget(self._orderWarningLabel)
        layout.addWidget(self._messageLabel)
        layout.addWidget(buttonBox)

        self._rebuildTable()

    # Public API

    @property
    def isModified(self) -> bool:
        return self._isModified

    @property
    def config(self) -> _rc.RunConfig:
        return self._config

    def apply(self) -> bool:
        for plan in self._pendingCopies:
            try:
                _imp.executeCopy(plan, overwrite=True)
            except OSError as error:
                self._showWarning(f"Could not copy the ddck: {error}")
                return False
        self._pendingCopies = []

        usesLibrary = any(
            il.include.pathVariable == _rc.LIBRARY_PATH_VARIABLE
            for il in self._config.getIncludeLines()
        )
        if usesLibrary and self._libraryDirPath:
            warning = _imp.ensureLibraryPathVariable(
                self._config, self._libraryDirPath
            )
            if warning:
                self._showWarning(warning)

        try:
            self._config.write()
        except OSError as error:
            self._showWarning(f"Could not write the config: {error}")
            return False

        self._isModified = False
        return True

    # Qt overrides

    def accept(self) -> None:
        if self._isModified and not self.apply():
            return
        super().accept()

    def reject(self) -> None:
        if self._isModified:
            answer = _qtw.QMessageBox.question(
                self,
                "Discard changes?",
                "Discard the changes to the project's ddcks?",
                _qtw.QMessageBox.Discard | _qtw.QMessageBox.Cancel,
                _qtw.QMessageBox.Cancel,
            )
            if answer != _qtw.QMessageBox.Discard:
                return
        super().reject()

    # Section panel

    def _createSectionPanel(self) -> _qtw.QWidget:
        panel = _qtw.QWidget()
        layout = _qtw.QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(_qtw.QLabel("<b>ddcks of the config</b> (in order)"))

        self._table.setHorizontalHeaderLabels(
            ["ddck", "Source", "global", "as", "Name", ""]
        )
        self._table.setSelectionBehavior(_qtw.QAbstractItemView.SelectRows)
        self._table.setSelectionMode(_qtw.QAbstractItemView.SingleSelection)
        self._table.verticalHeader().hide()
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(_COLUMN_DDCK, _qtw.QHeaderView.Stretch)
        for column in (
            _COLUMN_SOURCE,
            _COLUMN_GLOBAL,
            _COLUMN_AS,
            _COLUMN_OPEN,
        ):
            header.setSectionResizeMode(
                column, _qtw.QHeaderView.ResizeToContents
            )
        self._table.setColumnWidth(_COLUMN_NAME, 120)
        self._table.itemChanged.connect(self._onItemChanged)
        layout.addWidget(self._table, 1)

        buttons = _qtw.QHBoxLayout()
        for text, slot in [
            ("Remove", self._removeSelected),
            ("Up", lambda: self._moveSelected(-1)),
            ("Down", lambda: self._moveSelected(1)),
        ]:
            button = _qtw.QPushButton(text)
            button.clicked.connect(slot)
            buttons.addWidget(button)
        buttons.addStretch()
        layout.addLayout(buttons)
        return panel

    def _getItems(self) -> _tp.Sequence[_rc.SectionItem]:
        return self._config.getSectionItems()

    def _rebuildTable(self) -> None:
        items = self._getItems()
        self._isUpdatingTable = True
        try:
            self._table.clearContents()
            self._table.setRowCount(len(items))
            for rowIndex, item in enumerate(items):
                if item.isComponentBlock:
                    self._fillBlockRow(rowIndex, item)
                else:
                    self._fillEntryRow(rowIndex, item)
        finally:
            self._isUpdatingTable = False
        self._updateOrderWarning(items)

    def _fillBlockRow(self, rowIndex: int, item: _rc.SectionItem) -> None:
        assert item.componentName
        count = len(self._config.getComponentIncludes(item.componentName))
        ddckItem = _qtw.QTableWidgetItem(
            f"▸ {item.componentName}   ({count} ddck{'s' * (count != 1)})"
        )
        font = ddckItem.font()
        font.setBold(True)
        ddckItem.setFont(font)
        ddckItem.setToolTip(
            "A component's ddcks: edit them by double-clicking the component"
            " in the diagram. Here, you can move or remove the whole block."
        )
        self._setReadOnly(ddckItem)
        self._table.setItem(rowIndex, _COLUMN_DDCK, ddckItem)

        sourceItem = _qtw.QTableWidgetItem("Component")
        self._setReadOnly(sourceItem)
        self._table.setItem(rowIndex, _COLUMN_SOURCE, sourceItem)
        for column in (_COLUMN_GLOBAL, _COLUMN_AS, _COLUMN_NAME):
            emptyItem = _qtw.QTableWidgetItem()
            self._setReadOnly(emptyItem)
            self._table.setItem(rowIndex, column, emptyItem)
        self._table.removeCellWidget(rowIndex, _COLUMN_OPEN)

    def _fillEntryRow(self, rowIndex: int, item: _rc.SectionItem) -> None:
        assert item.entry
        include = item.entry.include

        text = include.relativePath
        toolTip = include.toLine()
        if item.entry.trailingLines:
            text += f"   (+{len(item.entry.trailingLines)} lines)"
            toolTip += "\n" + "\n".join(item.entry.trailingLines)
        pendingCopy = self._findPendingCopy(include)
        if pendingCopy:
            toolTip += "\n\nWill be copied when you press OK."
        ddckItem = _qtw.QTableWidgetItem(text)
        ddckItem.setToolTip(toolTip)
        self._setReadOnly(ddckItem)
        self._table.setItem(rowIndex, _COLUMN_DDCK, ddckItem)

        sourceItem = _qtw.QTableWidgetItem(_getSourceText(include))
        self._setReadOnly(sourceItem)
        self._table.setItem(rowIndex, _COLUMN_SOURCE, sourceItem)

        self._table.setItem(
            rowIndex, _COLUMN_GLOBAL, _createCheckItem(include.isGlobal)
        )
        hasAlias = include.alias is not None
        self._table.setItem(rowIndex, _COLUMN_AS, _createCheckItem(hasAlias))

        nameItem = _qtw.QTableWidgetItem(
            include.alias or include.componentName
        )
        if hasAlias:
            nameItem.setFlags(
                _qtc.Qt.ItemIsEnabled
                | _qtc.Qt.ItemIsSelectable
                | _qtc.Qt.ItemIsEditable
            )
        else:
            nameItem.setForeground(_qtg.QColor("#8c8c8c"))
            self._setReadOnly(nameItem)
        self._table.setItem(rowIndex, _COLUMN_NAME, nameItem)

        filePath = self._resolve(include)
        canOpen = bool(
            self._openFile
            and not pendingCopy
            and filePath
            and filePath.is_file()
        )
        openButton = _qtw.QPushButton("Open")
        openButton.setEnabled(canOpen)
        openButton.setToolTip(str(filePath) if canOpen else "Not available.")
        openButton.clicked.connect(
            lambda _, p=filePath: self._openFile(p)  # type: ignore[misc]
        )
        self._table.setCellWidget(rowIndex, _COLUMN_OPEN, openButton)

    def _updateOrderWarning(
        self, items: _tp.Sequence[_rc.SectionItem]
    ) -> None:
        names = [
            (
                _pl.PurePosixPath(
                    i.entry.include.relativePath.replace("\\", "/")
                ).name.lower()
                if i.entry
                else None
            )
            for i in items
        ]
        warnings = []
        if "head" in names and names[0] != "head":
            warnings.append("`head` should be the first ddck.")
        if "end" in names and names[-1] != "end":
            warnings.append("`end` should be the last ddck.")
        self._orderWarningLabel.setText(" ".join(warnings))
        self._orderWarningLabel.setVisible(bool(warnings))

    # Editing

    def _onItemChanged(self, tableItem: _qtw.QTableWidgetItem) -> None:
        if self._isUpdatingTable:
            return

        rowIndex = tableItem.row()
        sectionItem = self._getItems()[rowIndex]
        if not sectionItem.entry:
            return
        include = sectionItem.entry.include
        isChecked = tableItem.checkState() == _qtc.Qt.Checked

        if tableItem.column() == _COLUMN_GLOBAL:
            newInclude = _dc.replace(
                include,
                isGlobal=isChecked,
                alias=None if isChecked else include.alias,
            )
        elif tableItem.column() == _COLUMN_AS:
            newInclude = _dc.replace(
                include,
                alias=include.componentName if isChecked else None,
                isGlobal=False if isChecked else include.isGlobal,
            )
            if isChecked and not _rc.isValidComponentName(
                newInclude.alias or ""
            ):
                newInclude = _dc.replace(newInclude, alias="name")
        elif tableItem.column() == _COLUMN_NAME:
            name = tableItem.text().strip()
            if not _rc.isValidComponentName(name):
                self._showMessage(
                    "The name must not be empty or contain spaces or `#`."
                )
                self._rebuildTable()
                return
            newInclude = _dc.replace(include, alias=name)
        else:
            return

        self._config.replaceSectionInclude(rowIndex, newInclude)
        self._replacePendingCopyInclude(include, newInclude)
        self._setModified()
        self._rebuildTable()
        self._table.selectRow(rowIndex)

    def _removeSelected(self) -> None:
        rowIndex = self._table.currentRow()
        if rowIndex < 0:
            return
        sectionItem = self._getItems()[rowIndex]

        if sectionItem.isComponentBlock:
            answer = _qtw.QMessageBox.question(
                self,
                "Remove component block?",
                f"Remove all ddcks of the component"
                f" `{sectionItem.componentName}` from the config?",
                _qtw.QMessageBox.Yes | _qtw.QMessageBox.No,
                _qtw.QMessageBox.No,
            )
            if answer != _qtw.QMessageBox.Yes:
                return

        self._config.removeSectionItem(rowIndex)
        if sectionItem.entry:
            plan = self._findPendingCopy(sectionItem.entry.include)
            if plan:
                self._pendingCopies.remove(plan)
        self._setModified()
        self._rebuildTable()

    def _moveSelected(self, delta: int) -> None:
        rowIndex = self._table.currentRow()
        newIndex = rowIndex + delta
        if rowIndex < 0 or not 0 <= newIndex < self._table.rowCount():
            return
        self._config.moveSectionItem(rowIndex, newIndex)
        self._setModified()
        self._rebuildTable()
        self._table.selectRow(newIndex)

    # Importing

    def _setLibraryDirPath(self, libraryDirPath: _pl.Path) -> None:
        self._libraryDirPath = libraryDirPath

    def _useOriginal(self, filePath: _pl.Path) -> None:
        assert self._libraryDirPath
        include = _imp.createLibraryReference(
            self._libraryDirPath, filePath, None
        )
        self._insertInclude(include)

    def _importAsCopy(self, filePath: _pl.Path) -> None:
        assert self._libraryDirPath
        folderName = self._askForFolder(filePath)
        if not folderName:
            return

        try:
            plan = _imp.planCopy(
                self._libraryDirPath,
                filePath,
                self._projectDirPath / _DDCK_DIR_NAME,
                folderName,
            )
        except _imp.DdckImportError as error:
            self._showWarning(str(error))
            return

        existing = plan.getExistingTargetFilePaths()
        if existing:
            fileList = "\n".join(
                f"  • {p.relative_to(self._projectDirPath)}" for p in existing
            )
            answer = _qtw.QMessageBox.question(
                self,
                "Overwrite files?",
                "These files already exist in the project and will be"
                f" overwritten when you press OK:\n\n{fileList}\n\nContinue?",
                _qtw.QMessageBox.Yes | _qtw.QMessageBox.No,
                _qtw.QMessageBox.No,
            )
            if answer != _qtw.QMessageBox.Yes:
                return

        if plan.warnings:
            self._showMessage("\n".join(plan.warnings))
        self._pendingCopies.append(plan)
        self._insertInclude(plan.include)

    def _askForFolder(self, libraryDdckFilePath: _pl.Path) -> str | None:
        folders = getFolderSuggestions(
            self._projectDirPath / _DDCK_DIR_NAME,
            self._componentNames,
            self._getLibraryRelativePath(libraryDdckFilePath),
        )
        while True:
            folderName, isOk = _qtw.QInputDialog.getItem(
                self,
                "Import as copy",
                "Folder of the project's ddck folder to copy the ddck into"
                " (choose or type a new one):",
                folders,
                0,
                True,
            )
            if not isOk:
                return None
            folderName = folderName.strip()
            if _rc.isValidComponentName(folderName) and "/" not in folderName:
                if folderName in self._componentNames:
                    self._showMessage(
                        f"`{folderName}` is a component's folder: add its"
                        " ddcks in the component's window instead."
                    )
                    return None
                return folderName
            _qtw.QMessageBox.warning(
                self,
                "Invalid folder",
                "The folder name must not be empty or contain spaces, `#`"
                " or `/`.",
            )

    def _getLibraryRelativePath(self, filePath: _pl.Path) -> _pl.PurePath:
        assert self._libraryDirPath
        try:
            return filePath.resolve().relative_to(
                self._libraryDirPath.resolve()
            )
        except ValueError:
            return _pl.PurePath(filePath.name)

    def _insertInclude(self, include: _rc.DdckInclude) -> None:
        self._config.insertIncludeBeforeEnd(include)
        self._setModified()
        self._rebuildTable()
        for rowIndex, item in enumerate(self._getItems()):
            if item.entry and item.entry.include == include:
                self._table.selectRow(rowIndex)

    # Helpers

    def _findPendingCopy(
        self, include: _rc.DdckInclude
    ) -> _imp.CopyPlan | None:
        for plan in self._pendingCopies:
            if (
                plan.include.pathVariable == include.pathVariable
                and plan.include.relativePath == include.relativePath
            ):
                return plan
        return None

    def _replacePendingCopyInclude(
        self, oldInclude: _rc.DdckInclude, newInclude: _rc.DdckInclude
    ) -> None:
        plan = self._findPendingCopy(oldInclude)
        if plan:
            index = self._pendingCopies.index(plan)
            self._pendingCopies[index] = _dc.replace(plan, include=newInclude)

    def _resolve(self, include: _rc.DdckInclude) -> _pl.Path | None:
        pendingCopy = self._findPendingCopy(include)
        if pendingCopy:
            return pendingCopy.targetDdckFilePath
        variables = _sync.getEffectivePathVariables(
            self._config, self._projectDirPath
        )
        if self._libraryDirPath:
            variables.setdefault(
                _rc.LIBRARY_PATH_VARIABLE, str(self._libraryDirPath)
            )
        return include.resolve(variables, self._projectDirPath)

    def _setModified(self) -> None:
        self._isModified = True

    def _showMessage(self, message: str) -> None:
        self._messageLabel.setText(message)

    def _showWarning(self, message: str) -> None:
        _qtw.QMessageBox.warning(self, "Project ddcks", message)

    @staticmethod
    def _setReadOnly(item: _qtw.QTableWidgetItem) -> None:
        item.setFlags(_qtc.Qt.ItemIsEnabled | _qtc.Qt.ItemIsSelectable)


def getFolderSuggestions(
    projectDdckDirPath: _pl.Path,
    componentNames: _tp.Collection[str],
    libraryRelativePath: _pl.PurePath,
) -> list[str]:
    """The non-component folders of the project's ddck folder, the best
    match for the library ddck first (an existing folder whose name starts
    a folder of the ddck's path in the library, e.g. `weather` for
    `Weather_SPF/...`), else the name of the ddck's folder in the library."""
    existing = (
        sorted(
            p.name
            for p in projectDdckDirPath.iterdir()
            if p.is_dir()
            and p.name not in componentNames
            and not p.name.startswith(".")
        )
        if projectDdckDirPath.is_dir()
        else []
    )

    libraryFolders = [part.lower() for part in libraryRelativePath.parts[:-1]]
    for folder in existing:
        if any(part.startswith(folder.lower()) for part in libraryFolders):
            return [folder, *(f for f in existing if f != folder)]

    fallback = (
        libraryRelativePath.parts[-2]
        if len(libraryRelativePath.parts) > 1
        else "ddcks"
    )
    return [fallback, *(f for f in existing if f != fallback)]


def _getSourceText(include: _rc.DdckInclude) -> str:
    if include.pathVariable == _rc.PROJECT_PATH_VARIABLE:
        return "Copy"
    if include.pathVariable == _rc.LIBRARY_PATH_VARIABLE:
        return "Library"
    return include.pathVariable


def _createCheckItem(isChecked: bool) -> _qtw.QTableWidgetItem:
    item = _qtw.QTableWidgetItem()
    item.setFlags(
        _qtc.Qt.ItemIsEnabled
        | _qtc.Qt.ItemIsSelectable
        | _qtc.Qt.ItemIsUserCheckable
    )
    item.setCheckState(_qtc.Qt.Checked if isChecked else _qtc.Qt.Unchecked)
    return item


def showProjectDdckWindow(  # pylint: disable=too-many-arguments
    projectDirPath: _pl.Path,
    loadConfig: _tp.Callable[[], _rc.RunConfig],
    libraryDirPath: _pl.Path | None,
    *,
    componentNames: _tp.Collection[str],
    openFile: _panel.OpenFileCallback | None,
    parent: _qtw.QWidget | None,
) -> bool:
    """True if the config was changed."""
    try:
        config = loadConfig()
    except (OSError, _rc.RunConfigError) as error:
        _qtw.QMessageBox.warning(
            parent, "Project ddcks", f"Could not read the config:\n\n{error}"
        )
        return False

    window = ProjectDdckWindow(
        projectDirPath,
        config,
        libraryDirPath,
        componentNames=componentNames,
        openFile=openFile,
        parent=parent,
    )
    return window.exec() == _qtw.QDialog.Accepted
