# pylint: skip-file

import os as _os
import shutil as _sh
import typing as _tp

import PyQt5.QtWidgets as _qtw

import trnsysGUI.BlockItem as _bi
import trnsysGUI.MyQFileSystemModel as _fsm
import trnsysGUI.MyQTreeView as _tv
import trnsysGUI.blockItemGraphicItemMixins as _bimx
import trnsysGUI.images as _img


class PV(_bi.BlockItem, _bimx.PngBlockItemMixin):
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        _bi.BlockItem.__init__(self, trnsysType, editor, displayName)
        _bimx.PngBlockItemMixin.__init__(self)

        self.w = 100
        self.h = 100
        self.loadedFiles: list[str] = []

        self.changeSize()
        self.addTree()

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.PV_SVG

    def changeSize(self):
        w = self.w
        h = self.h

        # Limit the block size:
        if h < 20:
            h = 20
        if w < 40:
            w = 40
        # center label:
        rect = self.label.boundingRect()
        lw, lh = rect.width(), rect.height()
        lx = (w - lw) / 2
        self.label.setPos(lx, h)
        return w, h

    def addTree(self):
        """
        When a blockitem is added to the main window.
        A file explorer for that item is added to the right of the main window by calling this method
        """
        self.logger.debug(self.editor)
        pathName = self.displayName
        self.path = self.editor.projectFolder
        self.path = _os.path.join(self.path, "ddck")
        self.path = _os.path.join(self.path, pathName)
        if not _os.path.exists(self.path):
            _os.makedirs(self.path)

        self.model = _fsm.MyQFileSystemModel()
        self.model.setRootPath(self.path)
        self.model.setName(self.displayName)
        self.tree = _tv.MyQTreeView(self.model, self)
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(self.path))
        self.tree.setObjectName("%sTree" % self.displayName)
        for i in range(1, self.model.columnCount() - 1):
            self.tree.hideColumn(i)
        self.tree.setMinimumHeight(200)
        self.tree.setSortingEnabled(True)
        self.editor.splitter.addWidget(self.tree)

    def deleteBlock(self):
        """
        Overridden method to also delete folder
        """
        self.logger.debug("Block " + str(self) + " is deleting itself (" + self.displayName + ")")
        self.editor.trnsysObj.remove(self)
        self.logger.debug("deleting block " + str(self) + self.displayName)
        self.editor.diagramScene.removeItem(self)
        widgetToRemove = self.editor.findChild(_qtw.QTreeView, self.displayName + "Tree")
        _sh.rmtree(self.path)
        self.deleteLoadedFile()
        try:
            widgetToRemove.hide()
        except AttributeError:
            self.logger.debug("Widget doesnt exist!")
        else:
            self.logger.debug("Deleted widget")
        del self

    def setDisplayName(self, newName):
        """
        Overridden method to also change folder name
        """
        self.displayName = newName
        self.label.setPlainText(newName)
        self.model.setName(self.displayName)
        self.tree.setObjectName("%sTree" % self.displayName)
        self.logger.debug(_os.path.dirname(self.path))
        destPath = _os.path.join(_os.path.split(self.path)[0], self.displayName)
        if _os.path.exists(self.path):
            _os.rename(self.path, destPath)
            self.path = destPath
            self.logger.debug(self.path)
