from __future__ import annotations

import typing as _tp

from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QGraphicsView

from trnsysGUI.AirSourceHP import AirSourceHP  # type: ignore[attr-defined]
from trnsysGUI.BlockItem import BlockItem  # type: ignore[attr-defined]
from trnsysGUI.Boiler import Boiler  # type: ignore[attr-defined]
from trnsysGUI.Collector import Collector  # type: ignore[attr-defined]
from trnsysGUI.Connector import Connector  # type: ignore[attr-defined]
from trnsysGUI.Control import Control  # type: ignore[attr-defined]
from trnsysGUI.ExternalHx import ExternalHx  # type: ignore[attr-defined]
from trnsysGUI.GenericBlock import GenericBlock  # type: ignore[attr-defined]
from trnsysGUI.Graphicaltem import GraphicalItem  # type: ignore[attr-defined]
from trnsysGUI.GroundSourceHx import GroundSourceHx  # type: ignore[attr-defined]
from trnsysGUI.HPDoubleDual import HPDoubleDual  # type: ignore[attr-defined]
from trnsysGUI.HeatPump import HeatPump  # type: ignore[attr-defined]
from trnsysGUI.HeatPumpTwoHx import HeatPumpTwoHx  # type: ignore[attr-defined]
from trnsysGUI.IceStorage import IceStorage  # type: ignore[attr-defined]
from trnsysGUI.IceStorageTwoHx import IceStorageTwoHx  # type: ignore[attr-defined]
from trnsysGUI.MasterControl import MasterControl  # type: ignore[attr-defined]
from trnsysGUI.PV import PV  # type: ignore[attr-defined]
from trnsysGUI.PitStorage import PitStorage  # type: ignore[attr-defined]
from trnsysGUI.Pump import Pump  # type: ignore[attr-defined]
from trnsysGUI.Radiator import Radiator  # type: ignore[attr-defined]
from trnsysGUI.TVentil import TVentil  # type: ignore[attr-defined]
from trnsysGUI.TeePiece import TeePiece  # type: ignore[attr-defined]
from trnsysGUI.WTap import WTap  # type: ignore[attr-defined]
from trnsysGUI.WTap_main import WTap_main  # type: ignore[attr-defined]
from trnsysGUI.crystalizer import Crystalizer
from trnsysGUI.deleteBlockCommand import DeleteBlockCommand
from trnsysGUI.doubleDoublePipeConnector import DoubleDoublePipeConnector
from trnsysGUI.doublePipeTeePiece import DoublePipeTeePiece
from trnsysGUI.geotherm import Geotherm
from trnsysGUI.singleDoublePipeConnector import SingleDoublePipeConnector
from trnsysGUI.sink import Sink
from trnsysGUI.source import Source
from trnsysGUI.sourceSink import SourceSink
from trnsysGUI.storageTank.widget import StorageTank
from trnsysGUI.water import Water

if _tp.TYPE_CHECKING:
    import trnsysGUI.diagram.Editor as _ed


class View(QGraphicsView):
    """
    Displays the items from the Scene. Here, the drag and drop from the library to the View is implemented.

    """

    def __init__(self, scene, editor: _ed.Editor) -> None:  # type: ignore[name-defined]
        super().__init__(scene, editor)

        self.logger = editor.logger
        self._editor = editor

        self.adjustSize()
        self.parent().diagramScene.viewRect2.setPos(-self.width() / 2, -self.height() / 2)
        self.setRenderHint(QPainter.Antialiasing)

    def dragEnterEvent(self, event):  # pylint: disable=no-self-use
        if event.mimeData().hasFormat("component/name"):
            event.accept()

    def dragMoveEvent(self, event):  # pylint: disable=no-self-use
        if event.mimeData().hasFormat("component/name"):
            event.accept()

    def dropEvent(self, event):  # pylint: disable=too-many-branches,too-many-statements
        """Here, the dropped icons create BlockItems/GraphicalItems"""
        if event.mimeData().hasFormat("component/name"):
            name = str(event.mimeData().data("component/name"), encoding="utf-8")
            self.logger.debug("name is " + name)
            if name == "StorageTank":
                blockItem = StorageTank(name, self)
                self.parent().showConfigStorageDlg(blockItem)
            elif name == "TeePiece":
                blockItem = TeePiece(name, self)
            elif name == "DPTee":
                blockItem = DoublePipeTeePiece(name, self)
            elif name == "SPCnr":
                blockItem = SingleDoublePipeConnector(name, self)
            elif name == "DPCnr":
                blockItem = DoubleDoublePipeConnector(name, self)
            elif name == "TVentil":
                blockItem = TVentil(name, self)
            elif name == "Pump":
                blockItem = Pump(name, self)
            elif name == "Collector":
                blockItem = Collector(name, self)
            elif name == "HP":
                blockItem = HeatPump(name, self)
            elif name == "IceStorage":
                blockItem = IceStorage(name, self)
            elif name == "PitStorage":
                blockItem = PitStorage(name, self)
            elif name == "Radiator":
                blockItem = Radiator(name, self)
            elif name == "WTap":
                blockItem = WTap(name, self)
            elif name == "WTap_main":
                blockItem = WTap_main(name, self)
            elif name == "Connector":
                blockItem = Connector(name, self)
            elif name == "GenericBlock":
                blockItem = GenericBlock(name, self)
                # c = GenericPortPairDlg(bl, self)
                self.parent().showGenericPortPairDlg(blockItem)
            elif name == "HPTwoHx":
                blockItem = HeatPumpTwoHx(name, self)
            elif name == "HPDoubleDual":
                blockItem = HPDoubleDual(name, self)
            elif name == "Boiler":
                blockItem = Boiler(name, self)
            elif name == "AirSourceHP":
                blockItem = AirSourceHP(name, self)
            elif name == "PV":
                blockItem = PV(name, self)
            elif name == "GroundSourceHx":
                blockItem = GroundSourceHx(name, self)
            elif name == "ExternalHx":
                blockItem = ExternalHx(name, self)
            elif name == "IceStorageTwoHx":
                blockItem = IceStorageTwoHx(name, self)
            elif name == "GraphicalItem":
                blockItem = GraphicalItem(self)
            elif name == "MasterControl":
                blockItem = MasterControl(name, self)
            elif name == "Control":
                blockItem = Control(name, self)
            elif name == "Sink":
                blockItem = Sink(name, self)
            elif name == "Source":
                blockItem = Source(name, self)
            elif name == "SourceSink":
                blockItem = SourceSink(name, self)
            elif name == "Geotherm":
                blockItem = Geotherm(name, self)
            elif name == "Water":
                blockItem = Water(name, self)
            elif name == "Crystalizer":
                blockItem = Crystalizer(name, self)
            else:
                blockItem = BlockItem(name, self)

            snapSize = self.parent().snapSize
            if self.parent().snapGrid:
                position = QPoint(
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
        self.parent().mouseMoveEvent(event)

    def wheelEvent(self, event):
        super().wheelEvent(event)
        if int(event.modifiers()) == 0b100000000000000000000000000:
            if event.angleDelta().y() > 0:
                self.scale(1.2, 1.2)
            else:
                self.scale(0.8, 0.8)

    def deleteBlockCom(self, blockItem):
        command = DeleteBlockCommand(blockItem, self._editor)
        self.parent().parent().undoStack.push(command)
