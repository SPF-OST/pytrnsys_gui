"""The ddck library tree (`COMMON$`) with search, "Import as copy" and "Use
original", shared by the component's and the project's ddck windows."""

import pathlib as _pl
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

import trnsysGUI.runConfig as _rc

FILE_PATH_ROLE = _qtc.Qt.UserRole + 1


class LibraryBrowser(_qtw.QWidget):
    """Emits the selected library ddck's path when the user wants to import
    it as a copy or use the original."""

    importAsCopyRequested = _qtc.pyqtSignal(object)
    useOriginalRequested = _qtc.pyqtSignal(object)
    libraryChanged = _qtc.pyqtSignal(object)
    nothingSelected = _qtc.pyqtSignal()

    def __init__(
        self,
        libraryDirPath: _pl.Path | None,
        startDirPath: _pl.Path,
        copyToolTip: str,
        parent: _qtw.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.libraryDirPath = libraryDirPath
        self._startDirPath = startDirPath
        self._copyToolTip = copyToolTip

        self.tree = _qtw.QTreeView()
        self.filter = _qtw.QLineEdit()

        self._layout = _qtw.QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._content: _qtw.QWidget | None = None
        self._rebuild()

    def getSelectedFile(self) -> _pl.Path | None:
        index = self.tree.currentIndex()
        if not index.isValid():
            return None
        filePathString = index.data(FILE_PATH_ROLE)
        return _pl.Path(filePathString) if filePathString else None

    def chooseLibrary(self) -> None:
        startDirPath = str(self.libraryDirPath or self._startDirPath)
        dirPathString = _qtw.QFileDialog.getExistingDirectory(
            self, "Choose the ddck library folder", startDirPath
        )
        if not dirPathString:
            return

        _rc.saveConfiguredLibraryPath(dirPathString)
        self.libraryDirPath = _pl.Path(dirPathString)
        self._rebuild()
        self.libraryChanged.emit(self.libraryDirPath)

    def _rebuild(self) -> None:
        if self._content:
            self._layout.removeWidget(self._content)
            self._content.deleteLater()
        self._content = self._createContent()
        self._layout.addWidget(self._content)

    def _createContent(self) -> _qtw.QWidget:
        content = _qtw.QWidget()
        layout = _qtw.QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)

        # Recreated when the library changes.
        self.tree = _qtw.QTreeView()
        self.filter = _qtw.QLineEdit()

        title = _qtw.QLabel("<b>Library</b> (COMMON$)")
        changeButton = _qtw.QPushButton("Choose folder...")
        changeButton.setToolTip(
            "The folder with the ddck library (pytrnsys_gui's data/ddck)."
            " Also in File → Settings..."
        )
        changeButton.clicked.connect(self.chooseLibrary)
        titleLayout = _qtw.QHBoxLayout()
        titleLayout.addWidget(title, 1)
        titleLayout.addWidget(changeButton)
        layout.addLayout(titleLayout)

        if not self.libraryDirPath:
            message = _qtw.QLabel(
                "No ddck library found. Choose its folder (pytrnsys_gui's"
                " data/ddck) with the button above."
            )
            message.setWordWrap(True)
            layout.addWidget(message)
            layout.addStretch()
            return content

        title.setToolTip(str(self.libraryDirPath))

        self.filter.setPlaceholderText("Search...")
        self.filter.setClearButtonEnabled(True)
        layout.addWidget(self.filter)

        model = _createLibraryModel(self.libraryDirPath)
        proxyModel = _qtc.QSortFilterProxyModel(self)
        proxyModel.setSourceModel(model)
        proxyModel.setRecursiveFilteringEnabled(True)
        proxyModel.setFilterCaseSensitivity(_qtc.Qt.CaseInsensitive)
        self.filter.textChanged.connect(
            lambda text: self._filterLibrary(proxyModel, text)
        )

        self.tree.setModel(proxyModel)
        self.tree.setHeaderHidden(True)
        self.tree.doubleClicked.connect(
            lambda _: self._emitForSelection(self.useOriginalRequested)
        )
        layout.addWidget(self.tree, 1)

        buttons = _qtw.QHBoxLayout()
        copyButton = _qtw.QPushButton("Import as copy →")
        copyButton.setToolTip(self._copyToolTip)
        copyButton.clicked.connect(
            lambda: self._emitForSelection(self.importAsCopyRequested)
        )
        referenceButton = _qtw.QPushButton("Use original →")
        referenceButton.setToolTip(
            "Reference the ddck in the library (COMMON$), without copying it."
            " Double-clicking a ddck does the same."
        )
        referenceButton.clicked.connect(
            lambda: self._emitForSelection(self.useOriginalRequested)
        )
        buttons.addWidget(copyButton)
        buttons.addWidget(referenceButton)
        layout.addLayout(buttons)

        return content

    def _emitForSelection(self, signal: _tp.Any) -> None:
        filePath = self.getSelectedFile()
        if filePath:
            signal.emit(filePath)
        else:
            self.nothingSelected.emit()

    def _filterLibrary(
        self, proxyModel: _qtc.QSortFilterProxyModel, text: str
    ) -> None:
        proxyModel.setFilterFixedString(text)
        if text:
            self.tree.expandAll()


def _createLibraryModel(libraryDirPath: _pl.Path) -> _qtg.QStandardItemModel:
    """Folders and ddck files of the library (data files are hidden)."""
    model = _qtg.QStandardItemModel()
    style = _qtw.QApplication.style()
    folderIcon = style.standardIcon(_qtw.QStyle.SP_DirIcon)
    fileIcon = style.standardIcon(_qtw.QStyle.SP_FileIcon)

    def addChildren(parentItem: _qtg.QStandardItem, dirPath: _pl.Path) -> bool:
        hasDdcks = False
        for path in sorted(dirPath.iterdir(), key=_sortKey):
            if path.is_dir():
                folderItem = _qtg.QStandardItem(folderIcon, path.name)
                folderItem.setEditable(False)
                if addChildren(folderItem, path):
                    parentItem.appendRow(folderItem)
                    hasDdcks = True
            elif path.suffix.lower() == ".ddck":
                fileItem = _qtg.QStandardItem(fileIcon, path.stem)
                fileItem.setEditable(False)
                fileItem.setData(str(path), FILE_PATH_ROLE)
                fileItem.setToolTip(str(path.relative_to(libraryDirPath)))
                parentItem.appendRow(fileItem)
                hasDdcks = True
        return hasDdcks

    addChildren(model.invisibleRootItem(), libraryDirPath)
    return model


def _sortKey(path: _pl.Path) -> _tp.Tuple[bool, str]:
    return (not path.is_dir(), path.name.lower())
