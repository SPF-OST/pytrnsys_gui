# pylint: skip-file
# type: ignore

from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QGraphicsView
from trnsysGUI.AirSourceHP import AirSourceHP
from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.Boiler import Boiler
from trnsysGUI.Collector import Collector
from trnsysGUI.Connector import Connector
from trnsysGUI.Control import Control
from trnsysGUI.DeleteBlockCommand import DeleteBlockCommand
from trnsysGUI.ExternalHx import ExternalHx
from trnsysGUI.GenericBlock import GenericBlock
from trnsysGUI.Graphicaltem import GraphicalItem
from trnsysGUI.GroundSourceHx import GroundSourceHx
from trnsysGUI.HPDoubleDual import HPDoubleDual
from trnsysGUI.HeatPump import HeatPump
from trnsysGUI.HeatPumpTwoHx import HeatPumpTwoHx
from trnsysGUI.IceStorage import IceStorage
from trnsysGUI.IceStorageTwoHx import IceStorageTwoHx
from trnsysGUI.MasterControl import MasterControl
from trnsysGUI.PV import PV
from trnsysGUI.PitStorage import PitStorage
from trnsysGUI.Pump import Pump
from trnsysGUI.Radiator import Radiator
from trnsysGUI.StorageTank import StorageTank
from trnsysGUI.TVentil import TVentil
from trnsysGUI.TeePiece import TeePiece
from trnsysGUI.WTap import WTap
from trnsysGUI.WTap_main import WTap_main


class View(QGraphicsView):
    """
    Displays the items from the Scene. Here, the drag and drop from the library to the View is implemented.

    """

    def __init__(self, scene, parent=None):
        QGraphicsView.__init__(self, scene, parent)

        self.logger = parent.logger

        # self.setMinimumSize(self.parent().horizontalLayout.height, 700)
        self.adjustSize()
        # self.setMinimumSize(1300, 700)
        self.parent().diagramScene.viewRect2.setPos(-self.width() / 2, -self.height() / 2)
        # self.parent().diagramScene.viewRect2.setPos(1300, 700)
        # Use aliasing or not:
        self.setRenderHint(QPainter.Antialiasing)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("component/name"):
            event.accept()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("component/name"):
            event.accept()

    def dropEvent(self, event):
        """Here, the dropped icons create BlockItems/GraphicalItems"""
        if event.mimeData().hasFormat("component/name"):
            name = str(event.mimeData().data("component/name"), encoding="utf-8")
            self.logger.debug("name is " + name)
            if name == "StorageTank":
                bl = StorageTank(name, self)
                # c = ConfigStorage(bl, self)
                self.parent().showConfigStorageDlg(bl)
            elif name == "TeePiece":
                bl = TeePiece(name, self)
            elif name == "TVentil":
                bl = TVentil(name, self)
            elif name == "Pump":
                bl = Pump(name, self)
            elif name == "Collector":
                bl = Collector(name, self)
            elif name == "HP":
                bl = HeatPump(name, self)
            elif name == "IceStorage":
                bl = IceStorage(name, self)
            elif name == "PitStorage":
                bl = PitStorage(name, self)
            elif name == "Radiator":
                bl = Radiator(name, self)
            elif name == "WTap":
                bl = WTap(name, self)
            elif name == "WTap_main":
                bl = WTap_main(name, self)
            elif name == "Connector":
                bl = Connector(name, self)
            elif name == "GenericBlock":
                bl = GenericBlock(name, self)
                # c = GenericPortPairDlg(bl, self)
                self.parent().showGenericPortPairDlg(bl)
            elif name == "HPTwoHx":
                bl = HeatPumpTwoHx(name, self)
            elif name == "HPDoubleDual":
                bl = HPDoubleDual(name, self)
            elif name == "Boiler":
                bl = Boiler(name, self)
            elif name == "AirSourceHP":
                bl = AirSourceHP(name, self)
            elif name == "PV":
                bl = PV(name, self)
            elif name == "GroundSourceHx":
                bl = GroundSourceHx(name, self)
            elif name == "ExternalHx":
                bl = ExternalHx(name, self)
            elif name == "IceStorageTwoHx":
                bl = IceStorageTwoHx(name, self)
            elif name == "GraphicalItem":
                bl = GraphicalItem(self)
            elif name == "MasterControl":
                bl = MasterControl(name, self)
            elif name == "Control":
                bl = Control(name, self)
            else:
                bl = BlockItem(name, self)

            snapSize = self.parent().snapSize
            if self.parent().snapGrid:
                qp = QPoint(event.pos().x() - event.pos().x() % snapSize, event.pos().y() - event.pos().y() % snapSize)
                p1 = self.mapToScene(qp)
            else:
                p1 = self.mapToScene(event.pos())

            bl.setPos(p1)
            self.scene().addItem(bl)

            bl.oldPos = bl.scenePos()

            # Debug parent of blockitem
            # print("scene items" + str(self.scene().items()))
            # print("scene parent" + str(self.scene().parent()))
            # print("view children " + str(self.children()))
            # print("view items " + str(self.children()))
            # print("scene children" + str(self.scene().children()))
            # print("bl parentobjects are " + str(bl.parentObject()))
            # print("bl parent Widgets are " + str(bl.parentWidget()))
            # print("bl scene is " + str(bl.scene()))

    def mouseMoveEvent(self, event):
        QGraphicsView.mouseMoveEvent(self, event)
        self.parent().mouseMoveEvent(event)

    def mouseReleaseEvent(self, mouseEvent):
        pass
        # print(str(mouseEvent.pos()))
        #     for ot in self.trnsysObj:
        #     t.setPos(t.pos())
        # #     self.parent().alignYLineItem.setVisible(False)

        super(View, self).mouseReleaseEvent(mouseEvent)

    def wheelEvent(self, event):
        super(View, self).wheelEvent(event)
        # 67108864(dez) = 100000000000000000000000000(bin)
        if int(event.modifiers()) == 67108864:
            if event.angleDelta().y() > 0:
                self.scale(1.2, 1.2)
            else:
                self.scale(0.8, 0.8)

    def mousePressEvent(self, event):
        # for t in self.parent().trnsysObj:
        #     if isinstance(t, BlockItem):
        #         t.alignMode = True
        #         print("Changing alignmentmode")
        # for t in self.parent().trnsysObj:
        #     if isinstance(t, BlockItem):
        #         t.itemChange(t.ItemPositionChange, t.pos())

        super(View, self).mousePressEvent(event)

    def deleteBlockCom(self, bl):
        """
        Pushes the deleteBlockCommand onto the undoStack
        Parameters
        ----------
        bl

        Returns
        -------

        """
        command = DeleteBlockCommand(bl, "Delete block command")
        print("Deleted block")
        self.parent().parent().undoStack.push(command)
