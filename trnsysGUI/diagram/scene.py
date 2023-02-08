import PyQt5.QtWidgets as _qtw
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPen

from trnsysGUI.BlockItem import BlockItem  # type: ignore[attr-defined]
from trnsysGUI.Graphicaltem import GraphicalItem  # type: ignore[attr-defined]
from trnsysGUI.ResizerItem import ResizerItem  # type: ignore[attr-defined]
from trnsysGUI.connection.connectionBase import ConnectionBase  # type: ignore[attr-defined]
from trnsysGUI.storageTank.widget import StorageTank


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
        # Overwrite drawBackground if snapGrid is True
        if self._editor.snapGrid:
            pen = QPen()
            pen.setWidth(2)
            pen.setCosmetic(True)
            painter.setPen(pen)

            gridSize = self._editor.snapSize

            left = int(rect.left()) - (int(rect.left()) % gridSize)
            top = int(rect.top()) - (int(rect.top()) % gridSize)
            points = []
            for xIndex in range(left, int(rect.height()), gridSize):
                for yIndex in range(top, int(rect.bottom()), gridSize):
                    points.append(QPointF(xIndex, yIndex))

            for point in points:
                painter.drawPoint(point)
        else:
            super().drawBackground(painter, rect)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_L:
            self._editor.moveDirectPorts = not self._editor.moveDirectPorts
            return

        if event.key() == Qt.Key_Delete:
            trnsysObjects = self._editor.trnsysObj
            selectedObjects = [o for o in trnsysObjects if o.isSelected]

            if not selectedObjects:
                return

            assert len(selectedObjects) == 1, "It shouldn't be possible select more than one object"

            selectedObject = selectedObjects[0]

            if isinstance(selectedObject, ConnectionBase):
                selectedObject.createDeleteUndoCommandAndAddToStack()
            if isinstance(selectedObject, BlockItem):
                selectedObject.deleteBlockCom()

    def mousePressEvent(self, event):
        for connection in self._editor.connectionList:
            connection.deselectConnection()

        for trnsysObject in self._editor.trnsysObj:
            if isinstance(trnsysObject, BlockItem):
                trnsysObject.isSelected = False
            if isinstance(trnsysObject, StorageTank):
                for heatExchanger in trnsysObject.heatExchangers:
                    heatExchanger.unhighlightHx()

        self._editor.alignYLineItem.setVisible(False)

        if self._previouslyHitItems is not None:
            for item in self._previouslyHitItems:
                if isinstance(item, (GraphicalItem, BlockItem)) and hasattr(item, "resizer"):
                    self.removeItem(item.resizer)
                    item.deleteResizer()
                if isinstance(item, ResizerItem):
                    self.removeItem(item)
                    item.parent.deleteResizer()

            self._previouslyHitItems.clear()

        super().mousePressEvent(event)

        hitItems = self.items(event.scenePos())
        self._previouslyHitItems = hitItems
