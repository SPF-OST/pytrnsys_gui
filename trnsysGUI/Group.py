# pylint: skip-file
# type: ignore

from PyQt5.QtCore import QPointF
from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsTextItem

from trnsysGUI.Connection import Connection
from trnsysGUI.PortItem import PortItem
from trnsysGUI.segmentItem import segmentItem
from trnsysGUI.BlockItem import BlockItem


class Group(QGraphicsRectItem):
    def __init__(self, x, y, w, h, parent):
        super(Group, self).__init__(x, y, w, h)
        self.parent = parent
        self.x = x
        self.y = y
        self.w = w
        self.h = h

        self.displayName = "Untitled"

        # List of items part of this group
        self.itemList = []

        self.exportDi = 0.05  # [m]
        self.exportL = 2  # [m]
        self.exportU = 10  # DC will calculate proper default value

        self.label = QGraphicsTextItem(self)
        self.label.setPlainText(self.displayName)

        self.setVisible(False)

        # Add rect to scene
        self.parent.addItem(self)

        # Add group to groupList
        self.parent.parent().groupList.append(self)

        # Update the label position
        self.updateLabelPos()

    def computeRect(self):
        factor = 1.2
        center = None

        blockitems = 0

        max_x = 0
        max_y = 0
        min_x = 0
        min_y = 0

        for i in self.itemList:
            if isinstance(i, BlockItem):
                center += i.scenePos()
                blockitems += 1
                if i.scenePos().x() > max_x:
                    max_x = i.scenePos().x()

                if i.scenePos().x() < min_x:
                    min_x = i.scenePos().x()

                if i.scenePos().y() > max_y:
                    max_y = i.scenePos().y()

                if i.scenePos().x() < min_x:
                    min_y = i.scenePos().y()

            if type(i) is Connection:
                # ignore for center calculation
                pass

        center = QPointF(1 / blockitems * center.x(), 1 / blockitems * center.y())

        return (
            center.x() - (max_x - min_x) / 2 * factor,
            center.y() - (max_y - min_y) / 2 * factor,
            (max_x - min_x) * factor,
            (max_y - min_y) * factor,
        )

    def setItemsGroup(self, itemList):
        """
        Sets the items to this group
        Parameters
        ----------
        itemList

        Returns
        -------

        """
        for o in itemList:
            if isinstance(o, BlockItem):
                o.setBlockToGroup(self.displayName)
            elif isinstance(o, Connection):
                o.setConnToGroup(self.displayName)
            else:
                print("Found an item which is wether Block nor Connection in setItemsGroup")

    def addBlock(self, bl):
        inGroup = False

        for i in self.itemList:
            if isinstance(i, BlockItem):
                if i.id == bl.id:
                    print("Found the block already to be in group")
                    inGroup = True

        if not inGroup:
            print("Block not yet in this group")
            bl.append(bl)
            self.setItemsGroup()

    def addConnection(self, c):
        inGroup = False

        for i in self.itemList:
            if isinstance(i, Connection):
                if i.id == c.id:
                    print("Found the connection already to be in group")
                    inGroup = True

        if not inGroup:
            print("Block not yet in this group")
            c.append(c)
            self.setItemsGroup()

    def setName(self, newName):
        self.displayName = newName
        self.label.setPlainText(newName)
        # self.setItemsGroup()

    def updateLabelPos(self):
        factor = 0.9
        self.label.setPos(self.x + factor * self.w, self.y + self.h + 5)

    def deleteGroup(self):
        self.parent.parent().groupList.remove(self)
        self.parent.removeItem(self)

    def printGroup(self):
        print("Printout of group " + str(self) + str(self.displayName))
        print(
            "There are "
            + len([t for t in self.parent.parent().trnsysObj if type(t) is BlockItem])
            + " blocks and "
            + len([t for t in self.parent.parent().trnsysObj if type(t) is Connection])
            + " connections"
        )

        print("The elements are " + [t.displayName for t in self.parent.parent().trnsysObj])
