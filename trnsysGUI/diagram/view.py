from __future__ import annotations

import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

import trnsysGUI.blockItems.getBlockItem as _gbi
import trnsysGUI.deleteBlockCommand as _dbc
import trnsysGUI.names.undo as _nu

if _tp.TYPE_CHECKING:
    import trnsysGUI.diagram.Editor as _ed


class View(_qtw.QGraphicsView):
    """
    Displays the items from the Scene. Here, the drag and drop from the library to the View is implemented.

    """

    def __init__(self, scene, editor: _ed.Editor) -> None:  # type: ignore[name-defined]
        super().__init__(scene, editor)

        self.logger = editor.logger
        self._editor = editor

        self.adjustSize()
        self.setRenderHint(_qtg.QPainter.Antialiasing)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("component/name"):
            event.accept()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("component/name"):
            event.accept()

    def dropEvent(self, event):  # pylint: disable=too-many-branches,too-many-statements
        """Here, the dropped icons create BlockItems/GraphicalItems"""
        if event.mimeData().hasFormat("component/name"):
            componentType = str(event.mimeData().data("component/name"), encoding="utf-8")
            self.logger.debug("name is " + componentType)
            blockItem = _gbi.getBlockItem(componentType, self._editor)
            if componentType == "StorageTank":
                blockItem.setHydraulicLoops(self._editor.hydraulicLoops)
                self._editor.showConfigStorageDlg(blockItem)
            elif componentType == "GenericBlock":
                self._editor.showGenericPortPairDlg(blockItem)

            snapSize = self._editor.snapSize
            if self._editor.snapGrid:
                position = _qtc.QPoint(
                    event.pos().x() - event.pos().x() % snapSize, event.pos().y() - event.pos().y() % snapSize
                )
                scenePosition = self.mapToScene(position)
            else:
                scenePosition = self.mapToScene(event.pos())

            blockItem.setPos(scenePosition)
            self.scene().addItem(blockItem)

            blockItem.oldPos = blockItem.scenePos()

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self._editor.mouseMoveEvent(event)

    def wheelEvent(self, event):
        super().wheelEvent(event)
        if int(event.modifiers()) == 0b100000000000000000000000000:
            if event.angleDelta().y() > 0:
                self.scale(1.2, 1.2)
            else:
                self.scale(0.8, 0.8)

    def deleteBlockCom(self, blockItem):
        undoNamesHelper = _nu.UndoNamingHelper(self._editor.namesManager, self._editor.idGen)
        command = _dbc.DeleteBlockCommand(blockItem, self._editor, undoNamesHelper)
        self._editor.parent().undoStack.push(command)
