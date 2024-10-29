import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw
import numpy as _np

import trnsysGUI.BlockItem as _bi
import trnsysGUI.GraphicalItem as _gi
import trnsysGUI.connection.connectionBase as _cb
import trnsysGUI.storageTank.widget as _widget


class Scene(_qtw.QGraphicsScene):
    """
    This class serves as container for QGraphicsItems and is used in combination with the View to display the
    diagram.
    """

    def __init__(self, editor):
        super().__init__(editor)

        self.logger = editor.logger
        self._editor = editor

        self._previouslyHitItems = []

    def mouseMoveEvent(self, mouseEvent):
        self._editor.sceneMouseMoveEvent(mouseEvent)
        super().mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        self._editor.sceneMouseReleaseEvent(mouseEvent)
        super().mouseReleaseEvent(mouseEvent)
        self._editor.moveDirectPorts = False

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)

        if not self._editor.snapGrid:
            return

        pen = _qtg.QPen()
        pen.setWidth(2)
        pen.setCosmetic(True)
        painter.setPen(pen)

        gridSize = self._editor.snapSize

        left = rect.left() - rect.left() % gridSize
        top = rect.top() - rect.top() % gridSize

        for x in _np.arange(left, rect.right(), gridSize):
            for y in _np.arange(top, rect.bottom(), gridSize):
                xIndex = int(x)
                yIndex = int(y)
                painter.drawPoint(xIndex, yIndex)

    def keyPressEvent(self, event):
        if event.key() == _qtc.Qt.Key_L:
            self._editor.moveDirectPorts = not self._editor.moveDirectPorts
            return

        if event.key() == _qtc.Qt.Key_Delete:
            trnsysObjects = self._editor.trnsysObj
            selectedObjects = [o for o in trnsysObjects if self._isSelected(o)]

            if not selectedObjects:
                return

            assert (
                len(selectedObjects) == 1
            ), "It shouldn't be possible select more than one object"

            selectedObject = selectedObjects[0]

            if isinstance(selectedObject, _cb.ConnectionBase):
                selectedObject.createDeleteUndoCommandAndAddToStack()
            if isinstance(selectedObject, _bi.BlockItem):
                selectedObject.deleteBlockCom()

    @staticmethod
    def _isSelected(o):
        return (
            o.isConnectionSelected
            if isinstance(o, _cb.ConnectionBase)
            else o.isSelected
        )

    def mousePressEvent(self, event):
        for connection in self._editor.connectionList:
            connection.deselectConnection()

        for trnsysObject in self._editor.trnsysObj:
            if isinstance(trnsysObject, _bi.BlockItem):
                trnsysObject.isSelected = False
            if isinstance(trnsysObject, _widget.StorageTank):
                for heatExchanger in trnsysObject.heatExchangers:
                    heatExchanger.unhighlightHx()

        self._editor.alignYLineItem.setVisible(False)

        if self._previouslyHitItems is not None:
            for item in self._previouslyHitItems:
                if isinstance(
                    item, (_gi.GraphicalItem, _bi.BlockItem)
                ) and hasattr(item, "resizer"):
                    self.removeItem(item.resizer)

            self._previouslyHitItems.clear()

        super().mousePressEvent(event)

        hitItems = self.items(event.scenePos())
        self._previouslyHitItems = hitItems
