"""The ddcks of the active config, in config order, with a node per
component block. Clicking a ddck opens it in the editor."""

import pathlib as _pl

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

import trnsysGUI.runConfig as _rc
import trnsysGUI.runConfig.context as _ctx

_PATH_ROLE = _qtc.Qt.UserRole

_MISSING_COLOR = "#cf222e"


class ConfigTree(_qtw.QWidget):
    openRequested = _qtc.pyqtSignal(object)
    refreshRequested = _qtc.pyqtSignal()

    def __init__(self, parent: _qtw.QWidget | None = None) -> None:
        super().__init__(parent)

        self._titleLabel = _qtw.QLabel()
        self._titleLabel.setWordWrap(True)
        refreshButton = _qtw.QToolButton()
        refreshButton.setText("↻")
        refreshButton.setToolTip("Reload the active config")
        refreshButton.clicked.connect(self.refreshRequested)

        titleLayout = _qtw.QHBoxLayout()
        titleLayout.addWidget(self._titleLabel, 1)
        titleLayout.addWidget(refreshButton)

        self.tree = _qtw.QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemActivated.connect(self._onItemActivated)
        self.tree.itemClicked.connect(self._onItemActivated)

        layout = _qtw.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(titleLayout)
        layout.addWidget(self.tree, 1)

        self.setContext(None)

    def setContext(self, context: _ctx.ConfigContext | None) -> None:
        self.tree.clear()

        if context is None:
            self._titleLabel.setText(
                "<b>Active config</b><br>None yet (it's created when"
                " needed)."
            )
            return

        self._titleLabel.setText(
            f"<b>Active config</b><br><code>{context.configName}</code>"
        )
        self._titleLabel.setToolTip(str(context.config.filePath))

        style = self.style()
        fileIcon = style.standardIcon(_qtw.QStyle.SP_FileIcon)
        componentIcon = style.standardIcon(_qtw.QStyle.SP_DirIcon)

        for item in context.config.getSectionItems():
            if item.isComponentBlock:
                assert item.componentName
                blockItem = _qtw.QTreeWidgetItem([item.componentName])
                blockItem.setIcon(0, componentIcon)
                font = blockItem.font(0)
                font.setBold(True)
                blockItem.setFont(0, font)
                for include in context.config.getComponentIncludes(
                    item.componentName
                ):
                    blockItem.addChild(
                        _createFileItem(context, include, fileIcon)
                    )
                self.tree.addTopLevelItem(blockItem)
                blockItem.setExpanded(True)
            else:
                assert item.entry
                self.tree.addTopLevelItem(
                    _createFileItem(context, item.entry.include, fileIcon)
                )

    def _onItemActivated(self, item: _qtw.QTreeWidgetItem, _column=0) -> None:
        filePathString = item.data(0, _PATH_ROLE)
        if filePathString:
            self.openRequested.emit(_pl.Path(filePathString))


def _createFileItem(
    context: _ctx.ConfigContext,
    include: _rc.DdckInclude,
    icon: _qtg.QIcon,
) -> _qtw.QTreeWidgetItem:
    text = include.relativePath
    if include.alias:
        text += f"  as {include.alias}"
    elif include.isGlobal:
        text += "  (global)"

    item = _qtw.QTreeWidgetItem([text])
    item.setIcon(0, icon)

    filePath = context.resolve(include)
    if filePath and filePath.is_file():
        item.setData(0, _PATH_ROLE, str(filePath))
        source = "library" if context.isLibraryFile(filePath) else "project"
        item.setToolTip(0, f"{include.toLine()}\n{filePath} ({source})")
    else:
        item.setForeground(0, _qtg.QColor(_MISSING_COLOR))
        item.setToolTip(0, f"{include.toLine()}\nNot found: {filePath}")
    return item
