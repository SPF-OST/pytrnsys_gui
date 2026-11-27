# pylint: disable=too-many-lines
"""The panel for choosing the ddcks of a diagram component (the "ddcks" tab
of the component window).

Left: the ddck library (`COMMON$`), right: the component's ddcks as listed
in its block of the run config. Nothing is written (neither the config nor
copied files) before `apply`, i.e. before the window's OK.
"""

import dataclasses as _dc
import pathlib as _pl
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

import trnsysGUI.runConfig as _rc
import trnsysGUI.runConfig.importing as _imp

from . import libraryBrowser as _lb

_COLUMN_DDCK = 0
_COLUMN_SOURCE = 1
_COLUMN_AS = 2
_COLUMN_NAME = 3
_COLUMN_OPEN = 4

_SOURCE_COPY = "Copy"
_SOURCE_LIBRARY = "Library"

OpenFileCallback = _tp.Callable[[_pl.Path], None]


@_dc.dataclass
class _Row:
    entry: _rc.ComponentEntry
    pendingCopy: _imp.CopyPlan | None = None  # executed on OK
    hasCustomName: bool = False  # the "as" checkbox


class ComponentDdckPanel(
    _qtw.QWidget
):  # pylint: disable=too-many-instance-attributes
    def __init__(  # pylint: disable=too-many-arguments
        self,
        componentName: str,
        projectDirPath: _pl.Path,
        config: _rc.RunConfig,
        libraryDirPath: _pl.Path | None,
        *,
        openFile: OpenFileCallback | None = None,
        parent: _qtw.QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._componentName = componentName
        self._projectDirPath = projectDirPath
        self._config = config
        self._libraryDirPath = libraryDirPath
        self._openFile = openFile
        self._isModified = False
        self._isUpdatingTable = False

        self._rows = [
            self._createRow(e)
            for e in config.getComponentEntries(componentName)
        ]

        self._adoptionBanner = self._createAdoptionBanner()
        self._messageLabel = _qtw.QLabel()
        self._messageLabel.setWordWrap(True)
        self._messageLabel.hide()

        self._table = _qtw.QTableWidget(0, 5)

        self._library = self._createLibraryBrowser()
        self._splitter = _qtw.QSplitter(_qtc.Qt.Horizontal)
        self._splitter.addWidget(self._library)
        self._splitter.addWidget(self._createComponentPanel())
        self._splitter.setSizes([400, 700])

        layout = _qtw.QVBoxLayout(self)
        layout.addWidget(self._createHeader())
        layout.addWidget(self._adoptionBanner)
        layout.addWidget(self._messageLabel)
        layout.addWidget(self._splitter, 1)

        self._updateAdoptionBanner()
        self._rebuildTable()

    # Public API

    @property
    def isModified(self) -> bool:
        return self._isModified

    def getEntries(self) -> _tp.Sequence[_rc.ComponentEntry]:
        return [row.entry for row in self._rows]

    def apply(self) -> bool:
        """Copies pending files and writes the config. False on failure."""
        for row in self._rows:
            if row.pendingCopy:
                try:
                    _imp.executeCopy(row.pendingCopy, overwrite=True)
                except OSError as error:
                    self._showWarning(f"Could not copy the ddck: {error}")
                    return False
                row.pendingCopy = None

        if any(
            r.entry.include.pathVariable == _rc.LIBRARY_PATH_VARIABLE
            for r in self._rows
        ):
            if self._libraryDirPath:
                warning = _imp.ensureLibraryPathVariable(
                    self._config, self._libraryDirPath
                )
                if warning:
                    self._showWarning(warning)

        self._config.setComponentEntries(
            self._componentName, self.getEntries()
        )

        try:
            self._config.write()
        except OSError as error:
            self._showWarning(f"Could not write the config: {error}")
            return False

        self._isModified = False
        return True

    # Header and banner

    def _createHeader(self) -> _qtw.QWidget:
        configName = (
            self._config.filePath.name if self._config.filePath else "?"
        )
        label = _qtw.QLabel(f"Config: <code>{configName}</code>")
        label.setToolTip(str(self._config.filePath))
        return label

    def _createAdoptionBanner(self) -> _qtw.QFrame:
        banner = _qtw.QFrame()
        banner.setFrameShape(_qtw.QFrame.StyledPanel)
        layout = _qtw.QHBoxLayout(banner)
        self._adoptionLabel = _qtw.QLabel()
        self._adoptionLabel.setWordWrap(True)
        adoptButton = _qtw.QPushButton("Adopt")
        adoptButton.setToolTip(
            "Move these lines (with the `deck` lines following them) into"
            " this component's block of the config."
        )
        adoptButton.clicked.connect(self._adopt)
        layout.addWidget(self._adoptionLabel, 1)
        layout.addWidget(adoptButton)
        return banner

    # Library

    def _createLibraryBrowser(self) -> _lb.LibraryBrowser:
        browser = _lb.LibraryBrowser(
            self._libraryDirPath,
            self._projectDirPath,
            "Copy the ddck (and the data files it ASSIGNs) into"
            f" ddck/{self._componentName}/ of the project.",
        )
        browser.importAsCopyRequested.connect(
            lambda p: self._addFromLibraryFile(p, asCopy=True)
        )
        browser.useOriginalRequested.connect(
            lambda p: self._addFromLibraryFile(p, asCopy=False)
        )
        browser.nothingSelected.connect(
            lambda: self._showMessage(
                "Select a ddck file in the library first."
            )
        )
        browser.libraryChanged.connect(self._setLibraryDirPath)
        return browser

    def _setLibraryDirPath(self, libraryDirPath: _pl.Path) -> None:
        self._libraryDirPath = libraryDirPath

    def _addFromLibrary(self, asCopy: bool) -> None:
        filePath = self._library.getSelectedFile()
        if not filePath:
            self._showMessage("Select a ddck file in the library first.")
            return
        self._addFromLibraryFile(filePath, asCopy)

    def _addFromLibraryFile(self, filePath: _pl.Path, asCopy: bool) -> None:
        assert self._libraryDirPath

        if asCopy:
            row = self._createCopyRow(filePath)
            if not row:
                return
        else:
            include = _imp.createLibraryReference(
                self._libraryDirPath, filePath, self._componentName
            )
            row = self._createRow(_rc.ComponentEntry(include))

        self._rows.append(row)
        self._setModified()
        self._rebuildTable()
        self._table.selectRow(len(self._rows) - 1)

    def _createCopyRow(self, filePath: _pl.Path) -> _Row | None:
        assert self._libraryDirPath
        try:
            plan = _imp.planCopy(
                self._libraryDirPath,
                filePath,
                self._projectDirPath / "ddck",
                self._componentName,
            )
        except _imp.DdckImportError as error:
            self._showWarning(str(error))
            return None

        existingFilePaths = plan.getExistingTargetFilePaths()
        if existingFilePaths:
            fileList = "\n".join(
                f"  • {p.relative_to(self._projectDirPath)}"
                for p in existingFilePaths
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
                return None

        if plan.warnings:
            self._showMessage("\n".join(plan.warnings))

        return self._createRow(_rc.ComponentEntry(plan.include), plan)

    def _createRow(
        self,
        entry: _rc.ComponentEntry,
        pendingCopy: _imp.CopyPlan | None = None,
    ) -> _Row:
        hasCustomName = entry.include.componentName != self._componentName
        return _Row(entry, pendingCopy, hasCustomName)

    # Component panel

    def _createComponentPanel(self) -> _qtw.QWidget:
        panel = _qtw.QWidget()
        layout = _qtw.QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(
            _qtw.QLabel(f"<b>ddcks of {self._componentName}</b> (in order)")
        )

        self._table.setHorizontalHeaderLabels(
            ["ddck", "Source", "as", "Name", ""]
        )
        asHeaderItem = self._table.horizontalHeaderItem(_COLUMN_AS)
        if asHeaderItem:
            asHeaderItem.setToolTip(
                "Check to give the ddck another component name"
                " (`as <name>`). Unchecked: the component's name."
            )
        self._table.setSelectionBehavior(_qtw.QAbstractItemView.SelectRows)
        self._table.setSelectionMode(_qtw.QAbstractItemView.SingleSelection)
        self._table.verticalHeader().hide()
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(_COLUMN_DDCK, _qtw.QHeaderView.Stretch)
        for column in (_COLUMN_SOURCE, _COLUMN_AS, _COLUMN_OPEN):
            header.setSectionResizeMode(
                column, _qtw.QHeaderView.ResizeToContents
            )
        header.setSectionResizeMode(_COLUMN_NAME, _qtw.QHeaderView.Interactive)
        self._table.setColumnWidth(_COLUMN_NAME, 140)
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

    def _rebuildTable(self) -> None:
        self._isUpdatingTable = True
        try:
            self._table.setRowCount(len(self._rows))
            for rowIndex, row in enumerate(self._rows):
                self._fillRow(rowIndex, row)
        finally:
            self._isUpdatingTable = False

    def _fillRow(self, rowIndex: int, row: _Row) -> None:
        include = row.entry.include

        ddckItem = _qtw.QTableWidgetItem(include.relativePath)
        ddckItem.setFlags(_qtc.Qt.ItemIsEnabled | _qtc.Qt.ItemIsSelectable)
        toolTip = include.toLine()
        if row.entry.trailingLines:
            toolTip += "\n" + "\n".join(row.entry.trailingLines)
            ddckItem.setText(
                f"{include.relativePath}   (+{len(row.entry.trailingLines)}"
                " lines)"
            )
        if row.pendingCopy:
            toolTip += "\n\nWill be copied when you press OK."
        ddckItem.setToolTip(toolTip)
        self._table.setItem(rowIndex, _COLUMN_DDCK, ddckItem)

        sourceItem = _qtw.QTableWidgetItem(self._getSourceText(include))
        sourceItem.setFlags(_qtc.Qt.ItemIsEnabled | _qtc.Qt.ItemIsSelectable)
        self._table.setItem(rowIndex, _COLUMN_SOURCE, sourceItem)

        hasCustomName = row.hasCustomName
        asItem = _qtw.QTableWidgetItem()
        asItem.setFlags(
            _qtc.Qt.ItemIsEnabled
            | _qtc.Qt.ItemIsSelectable
            | _qtc.Qt.ItemIsUserCheckable
        )
        asItem.setCheckState(
            _qtc.Qt.Checked if hasCustomName else _qtc.Qt.Unchecked
        )
        self._table.setItem(rowIndex, _COLUMN_AS, asItem)

        nameItem = _qtw.QTableWidgetItem(
            include.alias if hasCustomName and include.alias else ""
        )
        flags = _qtc.Qt.ItemIsEnabled | _qtc.Qt.ItemIsSelectable
        if hasCustomName:
            flags |= _qtc.Qt.ItemIsEditable
        else:
            nameItem.setForeground(_qtg.QColor("#8c8c8c"))
            nameItem.setText(self._componentName)
        nameItem.setFlags(flags)
        self._table.setItem(rowIndex, _COLUMN_NAME, nameItem)

        openButton = _qtw.QPushButton("Open")
        filePath = self._resolve(row)
        canOpen = bool(
            self._openFile
            and not row.pendingCopy
            and filePath
            and filePath.is_file()
        )
        openButton.setEnabled(canOpen)
        openButton.setToolTip(
            str(filePath)
            if canOpen
            else "Not available (not copied yet or not found)."
        )
        openButton.clicked.connect(lambda _, r=row: self._openRow(r))
        self._table.setCellWidget(rowIndex, _COLUMN_OPEN, openButton)

    def _getSourceText(self, include: _rc.DdckInclude) -> str:
        if include.pathVariable == _rc.PROJECT_PATH_VARIABLE:
            return _SOURCE_COPY
        if include.pathVariable == _rc.LIBRARY_PATH_VARIABLE:
            return _SOURCE_LIBRARY
        return include.pathVariable

    def _getDefaultAlias(self, include: _rc.DdckInclude) -> str | None:
        """The alias meaning "the component's name": none if pytrnsys
        derives it from the ddck's directory anyway."""
        directoryName = _pl.PurePosixPath(
            include.relativePath.replace("\\", "/")
        ).parent.name
        if directoryName == self._componentName:
            return None
        return self._componentName

    def _onItemChanged(self, item: _qtw.QTableWidgetItem) -> None:
        if self._isUpdatingTable:
            return

        row = self._rows[item.row()]
        include = row.entry.include
        alias: str | None

        if item.column() == _COLUMN_AS:
            row.hasCustomName = item.checkState() == _qtc.Qt.Checked
            if row.hasCustomName:
                alias = include.alias or self._componentName
            else:
                alias = self._getDefaultAlias(include)
            self._setAlias(row, alias)
        elif item.column() == _COLUMN_NAME:
            name = item.text().strip()
            if not _rc.isValidComponentName(name):
                self._showMessage(
                    "The name must not be empty or contain spaces or `#`."
                )
                self._rebuildTable()
                return
            alias = (
                self._getDefaultAlias(include)
                if name == self._componentName
                else name
            )
            self._setAlias(row, alias)

    def _setAlias(self, row: _Row, alias: str | None) -> None:
        newInclude = _dc.replace(
            row.entry.include,
            alias=alias,
            isGlobal=False if alias else row.entry.include.isGlobal,
        )
        row.entry = _dc.replace(row.entry, include=newInclude)
        self._setModified()
        self._rebuildTable()

    def _removeSelected(self) -> None:
        rowIndex = self._table.currentRow()
        if rowIndex < 0:
            return
        removed = self._rows.pop(rowIndex)
        self._setModified()
        self._rebuildTable()

        include = removed.entry.include
        if include.pathVariable == _rc.PROJECT_PATH_VARIABLE:
            self._showMessage(
                f"Removed `{include.relativePath}` from the config. Its file"
                " stays in the project's ddck folder."
            )

    def _moveSelected(self, delta: int) -> None:
        rowIndex = self._table.currentRow()
        newIndex = rowIndex + delta
        if rowIndex < 0 or not 0 <= newIndex < len(self._rows):
            return
        self._rows[rowIndex], self._rows[newIndex] = (
            self._rows[newIndex],
            self._rows[rowIndex],
        )
        self._setModified()
        self._rebuildTable()
        self._table.selectRow(newIndex)

    def _resolve(self, row: _Row) -> _pl.Path | None:
        if row.pendingCopy:
            return row.pendingCopy.targetDdckFilePath
        variables = dict(self._config.getPathVariables())
        # pytrnsys' default for run.config
        variables.setdefault(
            _rc.PROJECT_PATH_VARIABLE, str(self._projectDirPath / "ddck")
        )
        if self._libraryDirPath:
            variables.setdefault(
                _rc.LIBRARY_PATH_VARIABLE, str(self._libraryDirPath)
            )
        return row.entry.include.resolve(variables, self._config.configDirPath)

    def _openRow(self, row: _Row) -> None:
        filePath = self._resolve(row)
        if self._openFile and filePath:
            self._openFile(filePath)

    # Adoption

    def _updateAdoptionBanner(self) -> None:
        adoptables = self._config.findAdoptableEntries(self._componentName)
        if not adoptables:
            self._adoptionBanner.hide()
            return

        lines = "<br>".join(
            f"<code>{a.entry.include.toLine()}</code>" for a in adoptables
        )
        self._adoptionLabel.setText(
            f"The config has {len(adoptables)} ddck(s) outside of component"
            f" blocks that belong to <b>{self._componentName}</b> (by their"
            f" <code>as</code> or folder):<br>{lines}"
        )
        self._adoptionBanner.show()

    def _adopt(self) -> None:
        """Without a block yet, it's created where the adopted lines were
        and they come first; else they're appended to the block."""
        hasBlock = bool(self._config.getComponentEntries(self._componentName))
        if hasBlock:
            self._config.setComponentEntries(
                self._componentName, self.getEntries()
            )
            self._config.adoptEntries(self._componentName)
            adoptedRows: list[_Row] = []
            keptRows = [
                self._createRow(e, self._findPendingCopy(e))
                for e in self._config.getComponentEntries(self._componentName)
            ]
        else:
            self._config.adoptEntries(self._componentName)
            adoptedRows = [
                self._createRow(e)
                for e in self._config.getComponentEntries(self._componentName)
            ]
            keptRows = self._rows

        self._rows = [*adoptedRows, *keptRows]
        self._setModified()
        self._updateAdoptionBanner()
        self._rebuildTable()

    def _findPendingCopy(
        self, entry: _rc.ComponentEntry
    ) -> _imp.CopyPlan | None:
        for row in self._rows:
            if row.pendingCopy and row.entry.include == entry.include:
                return row.pendingCopy
        return None

    # Helpers

    def _setModified(self) -> None:
        self._isModified = True

    def _showMessage(self, message: str) -> None:
        self._messageLabel.setText(message)
        self._messageLabel.show()

    def _showWarning(self, message: str) -> None:
        _qtw.QMessageBox.warning(self, "ddcks", message)
