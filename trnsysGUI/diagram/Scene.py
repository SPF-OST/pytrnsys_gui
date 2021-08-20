# pylint: skip-file
# type: ignore

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QPen
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsRectItem
from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.Connection import Connection
from trnsysGUI.Graphicaltem import GraphicalItem
from trnsysGUI.Group import Group
from trnsysGUI.ResizerItem import ResizerItem
from trnsysGUI.StorageTank import StorageTank


class Scene(QGraphicsScene):
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

    def __init__(self, parent=None):
        # Static size
        # super(Scene, self).__init__(QRectF(0, 0, parent.height(), 1500), parent)
        # self.setSceneRect(0, 0, parent.height(), parent.width())

        # Dynamic size, but "zero" at beginning
        super(Scene, self).__init__(parent)

        self.logger = parent.logger

        self.sRstart = QPointF(-500, -400)
        self.sRh = 700
        self.sRw = 400

        self.selectionRect = QGraphicsRectItem(self.sRstart.x(), self.sRstart.y(), self.sRw, self.sRw)
        self.viewRect1 = QGraphicsRectItem(0, 0, 10, 10)
        self.viewRect2 = QGraphicsRectItem(-800, -400, 10, 10)
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

        self.selectedItem = None

        # self.viewRect1.setPos(-1300, -100)
        # self.viewRect2.setPos(-1300, -100)

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
        self.logger.debug("Releasing mouse in Scene...")
        self.parent().sceneMouseReleaseEvent(mouseEvent)
        super(Scene, self).mouseReleaseEvent(mouseEvent)
        self.parent().moveDirectPorts = False
        if self.parent().pasting:
            # Dismantle group
            self.parent().clearCopyGroup()

        if self.parent().itemsSelected:
            # Dismantle selection
            self.parent().clearSelectionGroup()

        if self.parent().selectionMode:
            # self.released = True
            self.logger.debug("There are elements inside the selection : " + str(self.hasElementsInRect()))
            if self.hasElementsInRect():
                if self.parent().groupMode:
                    g = self.createGroup()
                    # groupDlg(g, self.parent(), self.elementsInRect())
                    self.parent().showGroupDlg(g, self.elementsInRect())
                elif self.parent().multipleSelectMode:
                    self.parent().createSelectionGroup(self.elementsInRect())
                elif self.parent().copyMode:
                    self.parent().copyElements()
                else:
                    self.logger.info("No recognized mode for selection")
            else:
                self.parent().copyMode = False
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
        pass
        if event.key() == Qt.Key_L:
            self.parent().moveDirectPorts = not self.parent().moveDirectPorts
            self.logger.debug("Changing move bool to " + str(self.parent().moveDirectPorts))

    def mousePressEvent(self, event):
        # self.parent().mousePressEvent(event)
        # TODO : remove resizer when click on other block items
        super(Scene, self).mousePressEvent(event)

        if len(self.items(event.scenePos())) > 0:
            self.selectedItem = self.items(event.scenePos())
            # for items in self.items():
            #     if items != self.selectedItem[0]:
            #         if isinstance(items, ResizerItem):
            #             break
            #         else:
            #             if hasattr(items, 'resizer'):
            #                 self.removeItem(items.resizer)
            #                 items.deleteResizer()
            #     else:
            #         print(items)
            #         print(self.selectedItem[0])

        """For selection when clicking on empty space"""
        if len(self.items(event.scenePos())) == 0:
            self.logger.debug("No items here!")
            self.parent().clearSelectionGroup()
            self.parent().selectionMode = True
            self.parent().copyMode = False
            self.parent().groupMode = False
            self.parent().multipleSelectMode = True
            for c in self.parent().connectionList:
                if not self.parent().parent().massFlowEnabled:
                    c.unhighlightConn()

            self.parent().alignYLineItem.setVisible(False)

            for st in self.parent().trnsysObj:
                if isinstance(st, StorageTank):
                    for hx in st.heatExchangers:
                        hx.unhighlightHx()

            if self.selectedItem is not None:
                for items in self.selectedItem:
                    if isinstance(items, GraphicalItem) and hasattr(items, "resizer"):
                        self.removeItem(items.resizer)
                        items.deleteResizer()
                    if isinstance(items, BlockItem) and hasattr(items, "resizer"):
                        self.removeItem(items.resizer)
                        items.deleteResizer()
                    if isinstance(items, ResizerItem):
                        self.removeItem(items)
                        items.parent.deleteResizer()

            if self.selectedItem is not None:
                self.selectedItem.clear()

        # global selectionMode
        if self.parent().selectionMode:
            self.pressed = True
            # self.selectionRect.setParentItem(self)
            if not self.released:
                self.sRstart = event.scenePos()
                self.selectionRect.setRect(
                    self.sRstart.x(),
                    self.sRstart.y(),
                    abs(event.scenePos().x() - self.sRstart.x()),
                    abs(event.scenePos().y() - self.sRstart.y()),
                )
                self.selectionRect.setVisible(True)

        # if len(self.items(event.scenePos())) == 0:
        #     print("No items here!")
        #     for c in self.parent().connectionList:
        #         c.unhighlightConn()
        #
        #     self.parent().alignYLineItem.setVisible(False)
        #
        #     for st in self.parent().trnsysObj:
        #         if isinstance(st, StorageTank):
        #             for hx in st.heatExchangers:
        #                 hx.unhighlightHx()

    def createGroup(self):
        newGroup = Group(self.sRstart.x(), self.sRstart.y(), self.sRw, self.sRh, self)

        return newGroup

    def elementsInRect(self):
        # Return elements in the selection rectangle

        res = []

        for o in self.parent().trnsysObj:
            if isinstance(o, BlockItem):
                self.logger.debug("Checking block to group")
                if self.isInRect(o.scenePos()):
                    res.append(o)

            if type(o) is Connection:
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

            if type(o) is Connection:
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
