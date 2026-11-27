# pylint: disable=too-many-lines
import collections.abc as _cabc
import dataclasses as _dc
import logging as _log
import pathlib as _pl
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

import pytrnsys.ddck.replaceTokens.defaultVisibility as _dv
import trnsysGUI.runConfig as _rc
import trnsysGUI.runConfig.context as _ctx
import trnsysGUI.runConfig.importing as _imp

from . import codeEditor as _ce
from . import configTree as _ct
from . import highlighter as _hl
from . import placeholders as _ph
from . import validation as _val

_LOGGER = _log.getLogger("root")

# Returns the placeholder values for all components as currently given by the
# diagram, or None if they can't be determined (e.g. diagram not connected).
PlaceholderValuesProvider = _tp.Callable[[], _ph.ValuesByComponent | None]

# The active run config, or None if there's none (yet).
ConfigContextProvider = _tp.Callable[[], _ctx.ConfigContext | None]

_TEXT_FILE_SUFFIXES = {".ddck", ".dck", ".json", ".config", ".log", ".txt"}
_DECK_FILE_SUFFIXES = {".ddck", ".dck"}

_FALLBACK_ENCODING = "windows-1252"  # what pytrnsys uses to read ddck files


def isTextFile(path: _pl.Path) -> bool:
    return path.suffix.lower() in _TEXT_FILE_SUFFIXES


def _isDdckFile(path: _pl.Path) -> bool:
    return path.suffix.lower() == ".ddck"


@_dc.dataclass(frozen=True)
class _FileContent:
    text: str
    encoding: str
    newline: str

    @staticmethod
    def read(path: _pl.Path) -> "_FileContent":
        data = path.read_bytes()

        isDeckFile = path.suffix.lower() in _DECK_FILE_SUFFIXES
        try:
            text = data.decode("utf-8")
            # pytrnsys reads deck files as windows-1252: make sure
            # non-ASCII characters added to pure-ASCII deck files are
            # saved such that pytrnsys reads them correctly.
            encoding = (
                _FALLBACK_ENCODING
                if isDeckFile and data.isascii()
                else "utf-8"
            )
        except UnicodeDecodeError:
            text = data.decode(_FALLBACK_ENCODING, errors="replace")
            encoding = _FALLBACK_ENCODING

        newline = "\r\n" if "\r\n" in text else "\n"
        normalizedText = text.replace("\r\n", "\n")

        return _FileContent(normalizedText, encoding, newline)

    def toBytes(self) -> bytes:
        return self.text.replace("\n", self.newline).encode(self.encoding)


class _Document(_qtw.QWidget):  # pylint: disable=too-many-instance-attributes
    """One open file."""

    modificationChanged = _qtc.pyqtSignal()

    def __init__(self, filePath: _pl.Path, content: _FileContent) -> None:
        super().__init__()

        self.filePath = filePath
        self.encoding = content.encoding
        self.newline = content.newline
        self.problems: _tp.Sequence[_val.Problem] = []
        self.valuesByPort: _ph.ValuesByPort | None = None

        # How the active config includes the file (see `setInclusions`).
        self.inclusions: _tp.Sequence[_ctx.Inclusion] = []
        self._configDefaultVisibility = _dv.DefaultVisibility.LOCAL
        self.isLibraryFile = False
        self.wasUnlocked = False

        # What we last read from or wrote to disk, to tell our own saves
        # apart from external changes.
        self.lastKnownDiskText = content.text

        self.editor = _ce.CodeEditor(self)
        self.highlighter: _hl.DdckHighlighter | None = (
            _hl.DdckHighlighter(self.editor.document())
            if filePath.suffix.lower() in _DECK_FILE_SUFFIXES
            else None
        )

        self.editor.setPlainText(content.text)
        self.editor.document().setModified(False)
        self.editor.document().modificationChanged.connect(
            self.modificationChanged
        )

        self.lockBanner = _LockBanner(self)
        self.lockBanner.hide()

        self._contextLabel = _qtw.QLabel()
        self._contextLabel.setWordWrap(True)
        self.inclusionComboBox = _qtw.QComboBox()
        self.inclusionComboBox.setToolTip(
            "The file is included several times in the config: the inclusion"
            " to validate it (and show its placeholders) for."
        )
        self.inclusionComboBox.hide()
        contextLayout = _qtw.QHBoxLayout()
        contextLayout.setContentsMargins(4, 2, 4, 2)
        contextLayout.addWidget(self._contextLabel, 1)
        contextLayout.addWidget(self.inclusionComboBox)

        layout = _qtw.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.lockBanner)
        layout.addLayout(contextLayout)
        layout.addWidget(self.editor)

    @property
    def isLocked(self) -> bool:
        return self.editor.isReadOnly()

    def setLocked(self, isLocked: bool) -> None:
        self.editor.setReadOnly(isLocked)
        self.lockBanner.setVisible(isLocked)

    @property
    def selectedInclusion(self) -> _ctx.Inclusion | None:
        if not self.inclusions:
            return None
        index = self.inclusionComboBox.currentIndex()
        return self.inclusions[max(index, 0)]

    def setInclusions(
        self,
        inclusions: _tp.Sequence[_ctx.Inclusion],
        configDefaultVisibility: _dv.DefaultVisibility,
        configName: str | None,
    ) -> None:
        """`configName` None: there's no active config."""
        selected = self.selectedInclusion
        previousLine = selected.include.toLine() if selected else None
        self.inclusions = list(inclusions)
        self._configDefaultVisibility = configDefaultVisibility

        self.inclusionComboBox.blockSignals(True)
        try:
            self.inclusionComboBox.clear()
            for inclusion in self.inclusions:
                self.inclusionComboBox.addItem(inclusion.label)
            lines = [i.include.toLine() for i in self.inclusions]
            if previousLine in lines:
                self.inclusionComboBox.setCurrentIndex(
                    lines.index(previousLine)
                )
        finally:
            self.inclusionComboBox.blockSignals(False)
        self.inclusionComboBox.setVisible(len(self.inclusions) > 1)

        self.updateContextLabel(configName)

    def updateContextLabel(self, configName: str | None) -> None:
        if not self.isDdck:
            self._contextLabel.setText("")
            return
        visibility = self.defaultVisibility.name.lower()
        componentName = self.componentName or "(none)"
        if configName is None:
            text = (
                "No active config: validated as component"
                f" <b>{componentName}</b> ({visibility})."
            )
        elif not self.inclusions:
            text = (
                f"Not included in <code>{configName}</code>: validated as"
                f" component <b>{componentName}</b> ({visibility})."
            )
        elif len(self.inclusions) == 1:
            text = (
                f"In <code>{configName}</code> as component"
                f" <b>{componentName}</b> ({visibility})."
            )
        else:
            text = (
                f"Included {len(self.inclusions)} times in"
                f" <code>{configName}</code>. Validate as:"
            )
        self._contextLabel.setText(text)

    @property
    def defaultVisibility(self) -> _dv.DefaultVisibility:
        inclusion = self.selectedInclusion
        if inclusion:
            return inclusion.defaultVisibility
        return self._configDefaultVisibility

    @property
    def isModified(self) -> bool:
        return self.editor.document().isModified()

    @property
    def isDdck(self) -> bool:
        return _isDdckFile(self.filePath)

    @property
    def componentName(self) -> str:
        """As pytrnsys sees it for the selected inclusion in the active
        config, else the name of the file's folder."""
        inclusion = self.selectedInclusion
        if inclusion:
            return inclusion.componentName
        return _val.getComponentName(self.filePath)

    def getText(self) -> str:
        return self.editor.toPlainText()

    def reload(self, content: _FileContent) -> None:
        cursorPosition = self.editor.textCursor().position()
        scrollValue = self.editor.verticalScrollBar().value()

        self.encoding = content.encoding
        self.newline = content.newline
        self.lastKnownDiskText = content.text

        # Use a cursor edit (instead of `setPlainText`) so the reload can
        # be undone.
        cursor = _qtg.QTextCursor(self.editor.document())
        cursor.select(_qtg.QTextCursor.Document)
        cursor.insertText(content.text)
        self.editor.document().setModified(False)

        cursor = self.editor.textCursor()
        cursor.setPosition(min(cursorPosition, len(content.text)))
        self.editor.setTextCursor(cursor)
        self.editor.verticalScrollBar().setValue(scrollValue)

    def setPlaceholderValues(
        self, valuesByPort: _ph.ValuesByPort | None
    ) -> None:
        self.valuesByPort = valuesByPort
        self.editor.setPlaceholderValues(valuesByPort)
        if self.highlighter:
            self.highlighter.setPlaceholderValues(valuesByPort)

    def validate(self) -> None:
        if not self.isDdck:
            self.problems = []
        else:
            self.problems = _val.validateDdck(
                self.getText(),
                self.componentName,
                self.valuesByPort,
                self.filePath,
                self.defaultVisibility,
            )

        problemsByLineNumber: dict[int, str] = {}
        for problem in self.problems:
            if problem.lineNumber is not None:
                problemsByLineNumber.setdefault(
                    problem.lineNumber, problem.message
                )
        self.editor.setProblems(problemsByLineNumber)


class DdckEditorTab(
    _qtw.QWidget
):  # pylint: disable=too-many-instance-attributes,too-many-public-methods
    """Tab for editing the project's ddck (and other text) files.

    Files are opened by double-clicking them in the project's file tree.
    Saving a ddck file (Ctrl+S) validates it like pytrnsys does when
    building the deck, using the placeholder values given by the current
    diagram.
    """

    def __init__(
        self,
        placeholderValuesProvider: PlaceholderValuesProvider,
        parent: _qtw.QWidget | None = None,
        configContextProvider: ConfigContextProvider | None = None,
    ) -> None:
        super().__init__(parent)

        self._placeholderValuesProvider = placeholderValuesProvider
        self._valuesByComponent: _ph.ValuesByComponent | None = None
        self._configContextProvider = configContextProvider
        self._configContext: _ctx.ConfigContext | None = None

        self._configTree = _ct.ConfigTree(self)
        self._configTree.openRequested.connect(self.openFile)
        self._configTree.refreshRequested.connect(self.refreshConfigContext)

        self._fileWatcher = _qtc.QFileSystemWatcher(self)
        self._fileWatcher.fileChanged.connect(self._onFileChangedOnDisk)
        self._filesBeingHandled: set[_pl.Path] = set()

        self._documentTabs = self._createDocumentTabs()
        self._findBar = _FindBar(self)
        self._statusLabel = _qtw.QLabel()
        self._problemsList = self._createProblemsList()
        self._placeholderPanel = _PlaceholderPanel(self)
        self._placeholderPanel.insertRequested.connect(self._insertPlaceholder)

        self._emptyLabel = _qtw.QLabel(
            "Double-click a file in the project's file tree (in the"
            " Diagram tab) to open it here."
        )
        self._emptyLabel.setAlignment(_qtc.Qt.AlignCenter)
        self._emptyLabel.setEnabled(False)

        self._haveSplitterSizesBeenSet = False
        self._setupLayout()
        self._updateForCurrentDocument()

    # Public API

    def openFile(self, filePath: _pl.Path) -> bool:
        filePath = filePath.resolve()

        existingDocument = self._findDocument(filePath)
        if existingDocument:
            self._documentTabs.setCurrentWidget(existingDocument)
            existingDocument.editor.setFocus()
            return True

        try:
            content = _FileContent.read(filePath)
        except OSError as error:
            _showWarning(self, f"Could not open file `{filePath}`: {error}")
            return False

        document = _Document(filePath, content)
        document.modificationChanged.connect(
            lambda: self._updateTabTitle(document)
        )
        document.editor.saveRequested.connect(
            lambda: self.saveDocument(document)
        )
        document.editor.findRequested.connect(self._showFindBar)
        document.editor.closeRequested.connect(
            lambda: self._closeDocument(document)
        )
        document.editor.cursorPositionChanged.connect(self._updateStatus)
        document.inclusionComboBox.currentIndexChanged.connect(
            lambda _: self._onInclusionChanged(document)
        )
        document.lockBanner.unlockRequested.connect(
            lambda: self._unlock(document)
        )
        document.lockBanner.copyRequested.connect(
            lambda: self._copyToProject(document)
        )

        index = self._documentTabs.addTab(document, filePath.name)
        self._documentTabs.setTabToolTip(index, str(filePath))
        self._documentTabs.setCurrentIndex(index)

        self._fileWatcher.addPath(str(filePath))

        self._applyConfigContext(document)
        self.refreshPlaceholderValues()
        document.validate()
        self._updateForCurrentDocument()
        document.editor.setFocus()

        return True

    def saveDocument(self, document: "_Document") -> bool:
        if document.isLocked:
            _showWarning(
                self,
                f"`{document.filePath.name}` is an original of the ddck"
                " library and opened read-only. Unlock it or copy it into"
                " the project first.",
            )
            return False

        content = _FileContent(
            document.getText(), document.encoding, document.newline
        )

        try:
            data = content.toBytes()
        except UnicodeEncodeError as error:
            _showWarning(
                self,
                f"Could not save `{document.filePath.name}`: it contains"
                f" characters that can't be encoded as {document.encoding}"
                f" ({error}).",
            )
            return False

        self._filesBeingHandled.add(document.filePath)
        try:
            document.filePath.write_bytes(data)
        except OSError as error:
            _showWarning(
                self, f"Could not save `{document.filePath}`: {error}"
            )
            return False
        finally:
            self._filesBeingHandled.discard(document.filePath)

        document.lastKnownDiskText = content.text
        document.editor.document().setModified(False)

        # Some ways of writing replace the file, and the watcher stops
        # watching it.
        if str(document.filePath) not in self._fileWatcher.files():
            self._fileWatcher.addPath(str(document.filePath))

        self.refreshPlaceholderValues()
        document.validate()
        self._updateProblemsList()

        _LOGGER.info("Saved %s", document.filePath)

        return True

    def hasUnsavedChanges(self) -> bool:
        return any(d.isModified for d in self._getDocuments())

    def maybeSaveAll(self, allowCancel: bool = True) -> bool:
        """Asks the user whether to save modified files.

        Returns False if the user cancelled (only possible if `allowCancel`).
        """
        modifiedDocuments = [d for d in self._getDocuments() if d.isModified]
        if not modifiedDocuments:
            return True

        fileNames = "\n".join(f"  • {d.filePath}" for d in modifiedDocuments)
        buttons = _qtw.QMessageBox.SaveAll | _qtw.QMessageBox.Discard
        if allowCancel:
            buttons |= _qtw.QMessageBox.Cancel

        answer = _qtw.QMessageBox.question(
            self,
            "Unsaved changes",
            f"The following files have unsaved changes:\n\n{fileNames}\n\n"
            "Do you want to save them?",
            buttons,
            _qtw.QMessageBox.SaveAll,
        )

        if answer == _qtw.QMessageBox.Cancel:
            return False

        if answer == _qtw.QMessageBox.SaveAll:
            for document in modifiedDocuments:
                if not self.saveDocument(document) and allowCancel:
                    return False

        return True

    def refreshPlaceholderValues(self) -> None:
        try:
            self._valuesByComponent = self._placeholderValuesProvider()
        except Exception:  # pylint: disable=broad-exception-caught
            _LOGGER.exception("Could not determine placeholder values.")
            self._valuesByComponent = None

        for document in self._getDocuments():
            self._applyPlaceholderValues(document)

        self._updatePlaceholderPanel()

    def refreshConfigContext(self) -> None:
        context = None
        if self._configContextProvider:
            try:
                context = self._configContextProvider()
            except (OSError, _rc.RunConfigError) as error:
                _LOGGER.warning("Could not read the active config: %s", error)
        self._configContext = context
        self._configTree.setContext(context)

        for document in self._getDocuments():
            self._applyConfigContext(document)
            self._applyPlaceholderValues(document)
            document.validate()
        self._updateForCurrentDocument()

    # Config context, library originals

    def _applyConfigContext(self, document: "_Document") -> None:
        context = self._configContext
        if context is None:
            document.setInclusions([], _dv.DefaultVisibility.LOCAL, None)
            return

        inclusions = (
            _ctx.findInclusions(context, document.filePath)
            if document.isDdck
            else []
        )
        document.setInclusions(
            inclusions,
            _ctx.getDefaultVisibility(context.config),
            context.configName,
        )

        document.isLibraryFile = context.isLibraryFile(document.filePath)
        if document.isLibraryFile and not document.wasUnlocked:
            document.setLocked(True)
            document.lockBanner.setCanCopy(
                bool(document.inclusions)
                and context.libraryDirPath is not None
            )

    def _onInclusionChanged(self, document: "_Document") -> None:
        document.updateContextLabel(
            self._configContext.configName if self._configContext else None
        )
        self._applyPlaceholderValues(document)
        document.validate()
        self._updateProblemsList()
        self._updatePlaceholderPanel()

    def _unlock(self, document: "_Document") -> None:
        answer = _qtw.QMessageBox.question(
            self,
            "Edit the library's original?",
            f"`{document.filePath.name}` is part of the ddck library: changes"
            " affect every project that uses it.\n\nEdit it anyway?",
            _qtw.QMessageBox.Yes | _qtw.QMessageBox.No,
            _qtw.QMessageBox.No,
        )
        if answer != _qtw.QMessageBox.Yes:
            return
        document.wasUnlocked = True
        document.setLocked(False)
        document.editor.setFocus()

    def _copyToProject(self, document: "_Document") -> None:
        context = self._configContext
        inclusion = document.selectedInclusion
        if not context or not inclusion or not context.libraryDirPath:
            return

        folderName = inclusion.blockComponentName or self._askForFolder(
            context, document.filePath
        )
        if not folderName:
            return

        try:
            newFilePath = _copyLibraryDdckIntoProject(
                self, context, inclusion, document.filePath, folderName
            )
        except (OSError, _rc.RunConfigError, _imp.DdckImportError) as error:
            _showWarning(self, f"Could not copy the ddck: {error}")
            return
        if not newFilePath:
            return

        self._closeDocument(document)
        self.refreshConfigContext()
        self.openFile(newFilePath)

    def _askForFolder(
        self, context: _ctx.ConfigContext, libraryFilePath: _pl.Path
    ) -> str | None:
        # pylint: disable=import-outside-toplevel  # avoid import cycle
        import trnsysGUI.componentDdcks.projectWindow as _pw

        assert context.libraryDirPath
        relativePath = libraryFilePath.resolve().relative_to(
            context.libraryDirPath.resolve()
        )
        folders = _pw.getFolderSuggestions(
            context.projectDirPath / "ddck",
            context.config.getComponentNames(),
            relativePath,
        )
        folderName, isOk = _qtw.QInputDialog.getItem(
            self,
            "Copy into the project",
            "Folder of the project's ddck folder to copy the ddck into:",
            folders,
            0,
            True,
        )
        folderName = folderName.strip()
        if not isOk or not _rc.isValidComponentName(folderName):
            return None
        return folderName

    # Qt overrides

    def showEvent(
        self, event: _qtg.QShowEvent
    ) -> None:  # pylint: disable=invalid-name
        super().showEvent(event)

        _qtc.QTimer.singleShot(0, self._setInitialSplitterSizesOnce)

        # The diagram and the active config might have changed while the tab
        # was hidden.
        self.refreshConfigContext()
        self.refreshPlaceholderValues()
        for document in self._getDocuments():
            document.validate()
        self._updateProblemsList()

    # Layout

    def _createDocumentTabs(self) -> _qtw.QTabWidget:
        tabs = _qtw.QTabWidget()
        tabs.setTabsClosable(True)
        tabs.setMovable(True)
        tabs.setDocumentMode(True)
        tabs.tabCloseRequested.connect(
            lambda index: self._closeDocument(
                _tp.cast(_Document, tabs.widget(index))
            )
        )
        tabs.currentChanged.connect(self._updateForCurrentDocument)
        return tabs

    def _createProblemsList(self) -> _qtw.QListWidget:
        problemsList = _qtw.QListWidget()
        problemsList.setWordWrap(True)
        problemsList.itemActivated.connect(self._goToProblem)
        problemsList.itemClicked.connect(self._goToProblem)
        return problemsList

    def _setupLayout(self) -> None:
        self._documentStack = _qtw.QStackedWidget()
        self._documentStack.addWidget(self._emptyLabel)
        self._documentStack.addWidget(self._documentTabs)

        editorArea = _qtw.QWidget()
        editorLayout = _qtw.QVBoxLayout(editorArea)
        editorLayout.setContentsMargins(0, 0, 0, 0)
        editorLayout.addWidget(self._documentStack)
        editorLayout.addWidget(self._findBar)
        editorLayout.addWidget(self._statusLabel)

        problemsArea = _qtw.QWidget()
        problemsLayout = _qtw.QVBoxLayout(problemsArea)
        problemsLayout.setContentsMargins(0, 0, 0, 0)
        problemsLayout.addWidget(_qtw.QLabel("<b>Problems</b>"))
        problemsLayout.addWidget(self._problemsList)

        self._editorAndProblemsSplitter = _qtw.QSplitter(_qtc.Qt.Vertical)
        self._editorAndProblemsSplitter.addWidget(editorArea)
        self._editorAndProblemsSplitter.addWidget(problemsArea)
        self._editorAndProblemsSplitter.setStretchFactor(0, 1)
        self._editorAndProblemsSplitter.setStretchFactor(1, 0)

        self._mainSplitter = _qtw.QSplitter(_qtc.Qt.Horizontal)
        self._mainSplitter.addWidget(self._configTree)
        self._mainSplitter.addWidget(self._editorAndProblemsSplitter)
        self._mainSplitter.addWidget(self._placeholderPanel)
        self._mainSplitter.setStretchFactor(0, 0)
        self._mainSplitter.setStretchFactor(1, 1)
        self._mainSplitter.setStretchFactor(2, 0)

        layout = _qtw.QVBoxLayout(self)
        layout.addWidget(self._mainSplitter)

    def _setInitialSplitterSizesOnce(self) -> None:
        # Only possible once the widget has its actual size.
        if self._haveSplitterSizesBeenSet:
            return
        self._haveSplitterSizesBeenSet = True

        width = self._mainSplitter.width()
        self._mainSplitter.setSizes(
            [width * 3 // 20, width * 13 // 20, width // 5]
        )

        height = self._editorAndProblemsSplitter.height()
        self._editorAndProblemsSplitter.setSizes(
            [height * 4 // 5, height // 5]
        )

    # Documents

    def _getDocuments(self) -> _tp.Sequence[_Document]:
        return [
            _tp.cast(_Document, self._documentTabs.widget(i))
            for i in range(self._documentTabs.count())
        ]

    def _getCurrentDocument(self) -> _Document | None:
        return _tp.cast(_Document | None, self._documentTabs.currentWidget())

    def _findDocument(self, filePath: _pl.Path) -> _Document | None:
        for document in self._getDocuments():
            if document.filePath == filePath:
                return document
        return None

    def _closeDocument(self, document: _Document) -> bool:
        if document.isModified:
            self._documentTabs.setCurrentWidget(document)
            answer = _qtw.QMessageBox.question(
                self,
                "Unsaved changes",
                f"`{document.filePath.name}` has unsaved changes. Do you want"
                " to save them?",
                _qtw.QMessageBox.Save
                | _qtw.QMessageBox.Discard
                | _qtw.QMessageBox.Cancel,
                _qtw.QMessageBox.Save,
            )
            if answer == _qtw.QMessageBox.Cancel:
                return False
            if answer == _qtw.QMessageBox.Save and not self.saveDocument(
                document
            ):
                return False

        self._fileWatcher.removePath(str(document.filePath))
        self._documentTabs.removeTab(self._documentTabs.indexOf(document))
        document.deleteLater()
        self._updateForCurrentDocument()
        return True

    def _updateTabTitle(self, document: _Document) -> None:
        index = self._documentTabs.indexOf(document)
        if index < 0:
            return
        title = document.filePath.name
        if document.isModified:
            title += " *"
        self._documentTabs.setTabText(index, title)

    def _applyPlaceholderValues(self, document: _Document) -> None:
        if not document.isDdck or self._valuesByComponent is None:
            document.setPlaceholderValues(None)
            return

        # Same as pytrnsys when building the deck: a component without
        # entry provides no values.
        valuesByPort = self._valuesByComponent.get(document.componentName, {})
        document.setPlaceholderValues(valuesByPort)

    def _updateForCurrentDocument(self) -> None:
        hasDocuments = self._documentTabs.count() > 0
        self._documentStack.setCurrentWidget(
            self._documentTabs if hasDocuments else self._emptyLabel
        )
        if not hasDocuments:
            self._findBar.hide()

        self._findBar.setEditor(
            document.editor
            if (document := self._getCurrentDocument())
            else None
        )

        self._updateProblemsList()
        self._updatePlaceholderPanel()
        self._updateStatus()

    def _updateStatus(self) -> None:
        document = self._getCurrentDocument()
        if not document:
            self._statusLabel.setText("")
            return

        cursor = document.editor.textCursor()
        newline = "CRLF" if document.newline == "\r\n" else "LF"
        self._statusLabel.setText(
            f"Ln {cursor.blockNumber() + 1}, Col {cursor.positionInBlock() + 1}"
            f"   •   {document.encoding}   •   {newline}"
        )

    # Problems

    def _updateProblemsList(self) -> None:
        self._problemsList.clear()

        document = self._getCurrentDocument()
        if not document:
            return

        if not document.isDdck:
            item = _qtw.QListWidgetItem(
                "Only .ddck files are validated (on save)."
            )
            item.setFlags(_qtc.Qt.NoItemFlags)
            self._problemsList.addItem(item)
            return

        if not document.problems:
            item = _qtw.QListWidgetItem("✔ No problems found.")
            item.setForeground(_qtg.QColor("#1a7f37"))
            item.setFlags(_qtc.Qt.ItemIsEnabled)
            self._problemsList.addItem(item)
            return

        icon = self.style().standardIcon(_qtw.QStyle.SP_MessageBoxCritical)
        for problem in document.problems:
            location = (
                f"Line {problem.lineNumber}: "
                if problem.lineNumber is not None
                else ""
            )
            summary = problem.message.strip().splitlines()[0].rstrip(":")
            item = _qtw.QListWidgetItem(icon, location + summary)
            item.setToolTip(problem.message)
            item.setData(_qtc.Qt.UserRole, problem.lineNumber)
            self._problemsList.addItem(item)

    def _goToProblem(self, item: _qtw.QListWidgetItem) -> None:
        lineNumber = item.data(_qtc.Qt.UserRole)
        document = self._getCurrentDocument()
        if document and lineNumber:
            document.editor.goToLine(lineNumber)

    # Placeholders

    def _updatePlaceholderPanel(self) -> None:
        document = self._getCurrentDocument()

        if not document or not document.isDdck:
            self._placeholderPanel.showMessage(
                "Placeholders are shown for .ddck files."
            )
            return

        if self._valuesByComponent is None:
            self._placeholderPanel.showMessage(
                "The placeholder values can't be determined: connect all"
                " ports in the diagram first. Placeholders are validated"
                " against their defaults meanwhile."
            )
            return

        self._placeholderPanel.showValues(
            document.componentName, document.valuesByPort or {}
        )

    def _insertPlaceholder(self, text: str) -> None:
        document = self._getCurrentDocument()
        if not document:
            return
        document.editor.insertPlainText(text)
        document.editor.setFocus()

    # Find bar

    def _showFindBar(self) -> None:
        document = self._getCurrentDocument()
        if not document:
            return
        selectedText = document.editor.textCursor().selectedText()
        self._findBar.showFor(selectedText)

    # External changes

    def _onFileChangedOnDisk(self, filePathString: str) -> None:
        filePath = _pl.Path(filePathString)
        document = self._findDocument(filePath)
        if not document or filePath in self._filesBeingHandled:
            return

        if not filePath.exists():
            # Might be a "replace" write in progress: watch again later.
            _qtc.QTimer.singleShot(
                500, lambda: self._rewatchIfExists(document)
            )
            return

        if filePathString not in self._fileWatcher.files():
            self._fileWatcher.addPath(filePathString)

        try:
            content = _FileContent.read(filePath)
        except OSError:
            return

        if content.text == document.lastKnownDiskText:
            return

        if document.isModified:
            self._filesBeingHandled.add(filePath)
            try:
                answer = _qtw.QMessageBox.question(
                    self,
                    "File changed on disk",
                    f"`{filePath.name}` was changed outside the editor, but"
                    " you also have unsaved changes.\n\nReload it from disk"
                    " and lose your changes?",
                    _qtw.QMessageBox.Yes | _qtw.QMessageBox.No,
                    _qtw.QMessageBox.No,
                )
            finally:
                self._filesBeingHandled.discard(filePath)

            if answer != _qtw.QMessageBox.Yes:
                # Don't ask again for the same disk content.
                document.lastKnownDiskText = content.text
                return

        document.reload(content)
        document.validate()
        self._updateProblemsList()
        _LOGGER.info("Reloaded %s (changed on disk)", filePath)

    def _rewatchIfExists(self, document: _Document) -> None:
        if self._findDocument(document.filePath) is not document:
            return
        if not document.filePath.exists():
            _LOGGER.warning(
                "%s was deleted or moved on disk.", document.filePath
            )
            return
        self._fileWatcher.addPath(str(document.filePath))
        self._onFileChangedOnDisk(str(document.filePath))


class _FindBar(_qtw.QWidget):
    def __init__(self, parent: _qtw.QWidget) -> None:
        super().__init__(parent)

        self._editor: _ce.CodeEditor | None = None

        self._findEdit = _qtw.QLineEdit()
        self._findEdit.setPlaceholderText("Find")
        self._findEdit.returnPressed.connect(self.findNext)
        self._findEdit.textChanged.connect(self._updateMatchCount)

        self._replaceEdit = _qtw.QLineEdit()
        self._replaceEdit.setPlaceholderText("Replace with")
        self._replaceEdit.returnPressed.connect(self.replace)

        self._matchCaseCheckBox = _qtw.QCheckBox("Match case")
        self._matchCaseCheckBox.toggled.connect(self._updateMatchCount)

        self._matchCountLabel = _qtw.QLabel()

        layout = _qtw.QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.addWidget(self._findEdit, 2)
        layout.addWidget(self._createButton("Previous", self.findPrevious))
        layout.addWidget(self._createButton("Next", self.findNext))
        layout.addWidget(self._matchCaseCheckBox)
        layout.addWidget(self._replaceEdit, 2)
        layout.addWidget(self._createButton("Replace", self.replace))
        layout.addWidget(self._createButton("Replace all", self.replaceAll))
        layout.addWidget(self._matchCountLabel)
        closeButton = self._createButton("✕", self.hide)
        closeButton.setToolTip("Close (Esc)")
        layout.addWidget(closeButton)

        escape = _qtw.QShortcut(_qtg.QKeySequence(_qtc.Qt.Key_Escape), self)
        escape.setContext(_qtc.Qt.WidgetWithChildrenShortcut)
        escape.activated.connect(self._hideAndFocusEditor)

        self.hide()

    def setEditor(self, editor: _ce.CodeEditor | None) -> None:
        self._editor = editor
        self._updateMatchCount()

    def showFor(self, text: str) -> None:
        if text and " " not in text:  # no multi-line selections
            self._findEdit.setText(text)
        self.show()
        self._findEdit.setFocus()
        self._findEdit.selectAll()
        self._updateMatchCount()

    def findNext(self) -> bool:
        return self._find(backward=False)

    def findPrevious(self) -> bool:
        return self._find(backward=True)

    def replace(self) -> None:
        if not self._editor:
            return
        cursor = self._editor.textCursor()
        if cursor.hasSelection() and self._isMatch(cursor.selectedText()):
            cursor.insertText(self._replaceEdit.text())
        self.findNext()
        self._updateMatchCount()

    def replaceAll(self) -> int:
        if not self._editor or not self._findEdit.text():
            return 0

        document = self._editor.document()
        editBlockCursor = _qtg.QTextCursor(document)
        editBlockCursor.beginEditBlock()  # a single undo step
        cursor = _qtg.QTextCursor(document)
        count = 0
        while True:
            cursor = document.find(
                self._findEdit.text(), cursor, self._getFindFlags()
            )
            if cursor.isNull():
                break
            cursor.insertText(self._replaceEdit.text())
            count += 1
        editBlockCursor.endEditBlock()

        self._matchCountLabel.setText(f"Replaced {count}")
        return count

    def _find(self, backward: bool) -> bool:
        if not self._editor or not self._findEdit.text():
            return False

        flags = self._getFindFlags()
        if backward:
            flags |= _qtg.QTextDocument.FindBackward

        if self._editor.find(self._findEdit.text(), flags):
            return True

        # Wrap around.
        cursor = self._editor.textCursor()
        cursor.movePosition(
            _qtg.QTextCursor.End if backward else _qtg.QTextCursor.Start
        )
        self._editor.setTextCursor(cursor)
        return self._editor.find(self._findEdit.text(), flags)

    def _getFindFlags(self) -> _qtg.QTextDocument.FindFlags:
        flags = _qtg.QTextDocument.FindFlags()
        if self._matchCaseCheckBox.isChecked():
            flags |= _qtg.QTextDocument.FindCaseSensitively
        return flags

    def _isMatch(self, text: str) -> bool:
        searchText = self._findEdit.text()
        if self._matchCaseCheckBox.isChecked():
            return text == searchText
        return text.lower() == searchText.lower()

    def _updateMatchCount(self) -> None:
        searchText = self._findEdit.text()
        if not self._editor or not searchText:
            self._matchCountLabel.setText("")
            return

        text = self._editor.toPlainText()
        if not self._matchCaseCheckBox.isChecked():
            text, searchText = text.lower(), searchText.lower()
        self._matchCountLabel.setText(f"{text.count(searchText)} matches")

    def _hideAndFocusEditor(self) -> None:
        self.hide()
        if self._editor:
            self._editor.setFocus()

    @staticmethod
    def _createButton(
        text: str, slot: _cabc.Callable[[], object]
    ) -> _qtw.QPushButton:
        button = _qtw.QPushButton(text)
        button.setAutoDefault(False)
        # Don't pass `clicked`'s `checked` argument on to the slot.
        button.clicked.connect(lambda _checked: slot())
        return button


class _PlaceholderPanel(_qtw.QWidget):
    """Shows the placeholder values the diagram provides for the current
    file's component. Double-clicking one inserts it at the cursor."""

    insertRequested = _qtc.pyqtSignal(str)

    def __init__(self, parent: _qtw.QWidget) -> None:
        super().__init__(parent)

        self._titleLabel = _qtw.QLabel()
        self._titleLabel.setWordWrap(True)

        self._messageLabel = _qtw.QLabel()
        self._messageLabel.setWordWrap(True)
        self._messageLabel.setAlignment(_qtc.Qt.AlignTop | _qtc.Qt.AlignLeft)

        self._tree = _qtw.QTreeWidget()
        self._tree.setHeaderLabels(["Placeholder", "Variable"])
        self._tree.setRootIsDecorated(True)
        self._tree.itemDoubleClicked.connect(self._onItemDoubleClicked)
        self._tree.setToolTip("Double-click to insert at the cursor.")

        layout = _qtw.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._titleLabel)
        layout.addWidget(self._messageLabel)
        layout.addWidget(self._tree, 1)

    def showMessage(self, message: str) -> None:
        self._titleLabel.setText("<b>Placeholders</b>")
        self._messageLabel.setText(message)
        self._messageLabel.show()
        self._tree.clear()
        self._tree.hide()

    def showValues(
        self, componentName: str, valuesByPort: _ph.ValuesByPort
    ) -> None:
        self._titleLabel.setText(
            f"<b>Placeholders of <code>{componentName}</code></b>"
            " (from the diagram)"
        )
        self._tree.clear()

        if not valuesByPort:
            self._messageLabel.setText(
                f"The diagram provides no placeholder values for"
                f" `{componentName}`. Is the ddck file in the folder of"
                " a component with ports?"
            )
            self._messageLabel.show()
            self._tree.hide()
            return

        self._messageLabel.hide()
        self._tree.show()

        for portName in sorted(valuesByPort):
            portItem = _qtw.QTreeWidgetItem([portName, ""])
            for portProperty, variableName in sorted(
                valuesByPort[portName].items()
            ):
                placeholder = f"{portProperty}({portName})"
                child = _qtw.QTreeWidgetItem([placeholder, variableName])
                child.setData(0, _qtc.Qt.UserRole, placeholder)
                portItem.addChild(child)
            self._tree.addTopLevelItem(portItem)

        self._tree.expandAll()
        self._tree.resizeColumnToContents(0)

    def _onItemDoubleClicked(
        self, item: _qtw.QTreeWidgetItem, _column: int
    ) -> None:
        placeholder = item.data(0, _qtc.Qt.UserRole)
        if placeholder:
            self.insertRequested.emit(placeholder)


class _LockBanner(_qtw.QFrame):
    """Shown above originals of the ddck library, which open read-only."""

    unlockRequested = _qtc.pyqtSignal()
    copyRequested = _qtc.pyqtSignal()

    def __init__(self, parent: _qtw.QWidget) -> None:
        super().__init__(parent)
        self.setFrameShape(_qtw.QFrame.StyledPanel)
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(_qtg.QPalette.Window, _qtg.QColor("#fff8c5"))
        self.setPalette(palette)

        label = _qtw.QLabel(
            "\U0001f512 <b>Original of the ddck library</b> (read-only):"
            " changes would affect every project that uses it."
        )
        label.setWordWrap(True)
        self._copyButton = _qtw.QPushButton("Copy to project")
        self._copyButton.setToolTip(
            "Copy it (and the data files it ASSIGNs) into the project and"
            " include the copy instead (PROJECT$) in the active config."
        )
        self._copyButton.clicked.connect(self.copyRequested)
        unlockButton = _qtw.QPushButton("Unlock")
        unlockButton.setToolTip("Edit the library's original.")
        unlockButton.clicked.connect(self.unlockRequested)

        layout = _qtw.QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.addWidget(label, 1)
        layout.addWidget(self._copyButton)
        layout.addWidget(unlockButton)

    @property
    def canCopy(self) -> bool:
        return self._copyButton.isEnabled()

    def setCanCopy(self, canCopy: bool) -> None:
        self._copyButton.setEnabled(canCopy)
        if not canCopy:
            self._copyButton.setToolTip(
                "Only possible for ddcks included in the active config."
            )


def _copyLibraryDdckIntoProject(
    parent: _qtw.QWidget,
    context: _ctx.ConfigContext,
    inclusion: _ctx.Inclusion,
    libraryFilePath: _pl.Path,
    folderName: str,
) -> _pl.Path | None:
    """Copies the library ddck into `ddck/<folderName>/` and replaces its
    inclusion in the config by the copy, keeping its component name and
    visibility. None if cancelled."""
    assert context.libraryDirPath
    original = inclusion.include

    plan = _imp.planCopy(
        context.libraryDirPath,
        libraryFilePath,
        context.projectDirPath / "ddck",
        folderName,
        alias=None if original.isGlobal else original.componentName or None,
    )
    if original.isGlobal:
        plan = _dc.replace(
            plan, include=_dc.replace(plan.include, alias=None, isGlobal=True)
        )

    existing = plan.getExistingTargetFilePaths()
    if existing:
        answer = _qtw.QMessageBox.question(
            parent,
            "Overwrite files?",
            "Overwrite these files of the project?\n\n"
            + "\n".join(f"  \u2022 {p}" for p in existing),
            _qtw.QMessageBox.Yes | _qtw.QMessageBox.No,
            _qtw.QMessageBox.No,
        )
        if answer != _qtw.QMessageBox.Yes:
            return None

    _imp.executeCopy(plan, overwrite=True)

    # Re-read: the config might have changed since the context was loaded.
    config = context.config
    if config.filePath and config.filePath.is_file():
        config = _rc.RunConfig.read(config.filePath)
    config.replaceIncludeLine(inclusion.lineIndex, plan.include)
    config.write()

    return plan.targetDdckFilePath


def _showWarning(parent: _qtw.QWidget, message: str) -> None:
    _qtw.QMessageBox.warning(parent, "Editor", message)
