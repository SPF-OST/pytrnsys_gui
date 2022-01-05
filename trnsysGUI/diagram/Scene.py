# pylint: skip-file
# type: ignore

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QPen
import PyQt5.QtWidgets as _qtw

from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.connection.connectionBase import ConnectionBase
from trnsysGUI.Graphicaltem import GraphicalItem
from trnsysGUI.ResizerItem import ResizerItem
from trnsysGUI.storageTank.widget import StorageTank


class Scene(_qtw.QGraphicsScene):
    """
    This class serves as container for QGraphicsItems and is used in combination with the View to display the
    diagram.
    It contains a rectangle for copy-paste or selecting multiple items.

    Attributes
    ----------

    sRstart : :obj:`QPointF`
        Upper left corner position of selectionRect
    sRh : int
        selectionRectHeight
    sRw : int
        selectionRectWidth
    selectionRect : :obj:`QGraphicsRectItem`
        Rectangle that displays the selection
    viewRect1 : :obj:`QGraphicsRectItem`
        Used to set the initial Scene size to approximately View size
    viewRect2 : :obj:`QGraphicsRectItem`
            Used to set the initial Scene size to approximately View size
    released : bool
        Enables the display of the selectionRect
    pressed : bool
        Set to True when selectionMode is True and mousePressed
        Set to False when no element in selection

    """

    def __init__(self, editor):
        super().__init__(editor)

        self.logger = editor.logger
        self._editor = editor

        self.sRstart = QPointF(-500, -400)
        self.sRh = 700
        self.sRw = 400

        self.selectionRect = _qtw.QGraphicsRectItem(self.sRstart.x(), self.sRstart.y(), self.sRw, self.sRw)
        self.viewRect1 = _qtw.QGraphicsRectItem(0, 0, 10, 10)
        self.viewRect2 = _qtw.QGraphicsRectItem(-800, -400, 10, 10)
        rectColor = QColor(100, 160, 245)

        p1 = QPen(rectColor, 2)
        self.selectionRect.setPen(p1)
        self.viewRect1.setPen(p1)
        self.viewRect2.setPen(p1)

        self.selectionRect.setVisible(False)
        self.viewRect1.setVisible(False)
        self.viewRect2.setVisible(False)

        self.addItem(self.selectionRect)
        self.addItem(self.viewRect1)
        self.addItem(self.viewRect2)

        self._previouslyHitItems = []

        self.released = False
        self.pressed = False

    def mouseMoveEvent(self, mouseEvent):
        self.parent().sceneMouseMoveEvent(mouseEvent)
        super(Scene, self).mouseMoveEvent(mouseEvent)

        if self.parent().selectionMode and not self.released and self.pressed:
            self.selectionRect.setVisible(True)
            self.sRw = mouseEvent.scenePos().x() - self.sRstart.x()
            self.sRh = mouseEvent.scenePos().y() - self.sRstart.y()

            if self.sRw < 0 and self.sRh > 0:  # from top right to bottom left
                rectangleR1 = QRectF(self.sRstart.x(), self.sRstart.y(), -abs(self.sRw), self.sRh).normalized()
                self.selectionRect.setRect(rectangleR1)
            elif self.sRw < 0 and self.sRh < 0:  # from bottom right to top left
                rectangleR1 = QRectF(self.sRstart.x(), self.sRstart.y(), -abs(self.sRw), -abs(self.sRh)).normalized()
                self.selectionRect.setRect(rectangleR1)
            elif self.sRw > 0 and self.sRh < 0:  # from bottom left to top right
                rectangleR1 = QRectF(self.sRstart.x(), self.sRstart.y(), self.sRw, -abs(self.sRh)).normalized()
                self.selectionRect.setRect(rectangleR1)
            else:
                rectangleR1 = QRectF(self.sRstart.x(), self.sRstart.y(), self.sRw, self.sRh)
                self.selectionRect.setRect(rectangleR1)

    def mouseReleaseEvent(self, mouseEvent):
        self.parent().sceneMouseReleaseEvent(mouseEvent)
        super().mouseReleaseEvent(mouseEvent)
        self.parent().moveDirectPorts = False
        if self.parent().pasting:
            self.parent().clearCopyGroup()

        if self.parent().itemsSelected:
            self.parent().clearSelectionGroup()

        if self.parent().selectionMode:
            if self.hasElementsInRect():
                if self.parent().multipleSelectMode:
                    self.parent().createSelectionGroup(self.elementsInRect())
            else:
                self.parent().selectionMode = False

            self.released = False
            self.pressed = False
            self.selectionRect.setVisible(False)

    def drawBackground(self, painter, rect):
        # Overwrite drawBackground if snapGrid is True
        if self.parent().snapGrid:
            pen = QPen()
            pen.setWidth(2)
            pen.setCosmetic(True)
            painter.setPen(pen)

            gridSize = self.parent().snapSize

            left = int(rect.left()) - (int(rect.left()) % gridSize)
            top = int(rect.top()) - (int(rect.top()) % gridSize)
            points = []
            for x in range(left, int(rect.height()), gridSize):
                for y in range(top, int(rect.bottom()), gridSize):
                    points.append(QPointF(x, y))

            for x in points:
                painter.drawPoint(x)
        else:
            super(Scene, self).drawBackground(painter, rect)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_L:
            self.parent().moveDirectPorts = not self.parent().moveDirectPorts
            return

        if event.key() == Qt.Key_Delete:
            trnsysObjects = self.parent().trnsysObj
            selectedObjects = [o for o in trnsysObjects if o.isSelected]

            if not selectedObjects:
                return

            if len(selectedObjects) > 1:
                messageBox = _qtw.QMessageBox()
                messageBox.setWindowTitle("Deleting with multiple objects selected")
                messageBox.setText(
                    "You're trying to delete multiple selected objects at once. This is currently not supported. "
                    "Please select and delete one object after the other."
                )
                messageBox.setStandardButtons(messageBox.Ok)
                messageBox.exec()
                return

            selectedObject = selectedObjects[0]

            if isinstance(selectedObject, ConnectionBase):
                selectedObject.createDeleteUndoCommandAndAddToStack()
            if isinstance(selectedObject, BlockItem):
                selectedObject.deleteBlockCom()

    def mousePressEvent(self, event):
        if not self._editor.parent().massFlowEnabled:
            for connection in self._editor.connectionList:
                connection.deselectConnection()

        for trnsysObject in self._editor.trnsysObj:
            if isinstance(trnsysObject, BlockItem):
                trnsysObject.isSelected = False
            if isinstance(trnsysObject, StorageTank):
                for heatExchanger in trnsysObject.heatExchangers:
                    heatExchanger.unhighlightHx()

        self.parent().clearSelectionGroup()
        self.parent().selectionMode = True
        self.parent().multipleSelectMode = True

        self.parent().alignYLineItem.setVisible(False)

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

        if self.parent().selectionMode:
            self.pressed = True
            if not self.released:
                self.sRstart = event.scenePos()
                self.selectionRect.setRect(
                    self.sRstart.x(),
                    self.sRstart.y(),
                    abs(event.scenePos().x() - self.sRstart.x()),
                    abs(event.scenePos().y() - self.sRstart.y()),
                )
                self.selectionRect.setVisible(True)

    def elementsInRect(self):
        # Return elements in the selection rectangle

        res = []

        for o in self.parent().trnsysObj:
            if isinstance(o, BlockItem):
                self.logger.debug("Checking block to group")
                if self.isInRect(o.scenePos()):
                    res.append(o)

            if isinstance(o, ConnectionBase):
                self.logger.debug("Checking connection to group")
                if self.isInRect(o.fromPort.scenePos()) and self.isInRect(o.toPort.scenePos()):
                    res.append(o)

        for o in self.parent().graphicalObj:
            if isinstance(o, GraphicalItem):
                self.logger.debug("Checking graphic item to group")
                if self.isInRect(o.scenePos()):
                    res.append(o)

        return res

    def hasElementsInRect(self):
        # Check if there are elements in the selection rectangle
        for o in self.parent().trnsysObj:
            if isinstance(o, BlockItem):
                self.logger.debug("Checking block to group")
                if self.isInRect(o.scenePos()):
                    return True

            if isinstance(o, ConnectionBase):
                self.logger.debug("Checking connection to group")
                if self.isInRect(o.fromPort.scenePos()) and self.isInRect(o.toPort.scenePos()):
                    return True

        for o in self.parent().graphicalObj:
            if isinstance(o, GraphicalItem):
                self.logger.debug("Checking graphic item to group")
                if self.isInRect(o.scenePos()):
                    return True

        return False

    def isInRect(self, point):
        # Check if a point is in the selection rectangle
        # from top left to bottom right
        if (
            point.x() > self.sRstart.x()
            and point.x() < (self.sRstart.x() + self.sRw)
            and point.y() > self.sRstart.y()
            and point.y() < (self.sRstart.y() + self.sRh)
        ):
            self.logger.debug("In rect")
            return True

        # from top right to bottom left
        elif (
            point.x() < self.sRstart.x()
            and point.x() > (self.sRstart.x() + self.sRw)
            and point.y() > self.sRstart.y()
            and point.y() < (self.sRstart.y() + self.sRh)
        ):
            self.logger.debug("In rect")
            return True

        # from bottom right to top left
        elif (
            point.x() < self.sRstart.x()
            and point.x() > (self.sRstart.x() + self.sRw)
            and point.y() < self.sRstart.y()
            and point.y() > (self.sRstart.y() + self.sRh)
        ):
            self.logger.debug("In rect")
            return True

        # from bottom left to top right
        elif (
            point.x() > self.sRstart.x()
            and point.x() < (self.sRstart.x() + self.sRw)
            and point.y() < self.sRstart.y()
            and point.y() > (self.sRstart.y() + self.sRh)
        ):
            self.logger.debug("In rect")
            return True

        else:
            return False
