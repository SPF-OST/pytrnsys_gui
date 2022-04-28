from __future__ import annotations

import typing as _tp

from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QGraphicsView

from trnsysGUI.AirSourceHP import AirSourceHP  # type: ignore[attr-defined]
from trnsysGUI.BlockItem import BlockItem  # type: ignore[attr-defined]
from trnsysGUI.Boiler import Boiler  # type: ignore[attr-defined]
from trnsysGUI.CentralReceiver import CentralReceiver  # type: ignore[attr-defined]
from trnsysGUI.Collector import Collector  # type: ignore[attr-defined]
from trnsysGUI.connectors.connector import Connector  # type: ignore[attr-defined]
from trnsysGUI.Control import Control  # type: ignore[attr-defined]
from trnsysGUI.ExternalHx import ExternalHx  # type: ignore[attr-defined]
from trnsysGUI.GenericBlock import GenericBlock  # type: ignore[attr-defined]
from trnsysGUI.Graphicaltem import GraphicalItem  # type: ignore[attr-defined]
from trnsysGUI.GroundSourceHx import GroundSourceHx  # type: ignore[attr-defined]
from trnsysGUI.HPDoubleDual import HPDoubleDual  # type: ignore[attr-defined]
from trnsysGUI.HPDual import HPDual  # type: ignore[attr-defined]
from trnsysGUI.HeatPump import HeatPump  # type: ignore[attr-defined]
from trnsysGUI.HeatPumpTwoHx import HeatPumpTwoHx  # type: ignore[attr-defined]
from trnsysGUI.IceStorage import IceStorage  # type: ignore[attr-defined]
from trnsysGUI.IceStorageTwoHx import IceStorageTwoHx  # type: ignore[attr-defined]
from trnsysGUI.MasterControl import MasterControl  # type: ignore[attr-defined]
from trnsysGUI.ParabolicTroughField import ParabolicTroughField  # type: ignore[attr-defined]
from trnsysGUI.PV import PV  # type: ignore[attr-defined]
from trnsysGUI.PitStorage import PitStorage  # type: ignore[attr-defined]
from trnsysGUI.pump import Pump  # type: ignore[attr-defined]
from trnsysGUI.Radiator import Radiator  # type: ignore[attr-defined]
from trnsysGUI.SaltTankCold import SaltTankCold  # type: ignore[attr-defined]
from trnsysGUI.SaltTankHot import SaltTankHot  # type: ignore[attr-defined]
from trnsysGUI.SteamPowerBlock import SteamPowerBlock  # type: ignore[attr-defined]
from trnsysGUI.TVentil import TVentil  # type: ignore[attr-defined]
from trnsysGUI.TeePiece import TeePiece  # type: ignore[attr-defined]
from trnsysGUI.WTap import WTap  # type: ignore[attr-defined]
from trnsysGUI.WTap_main import WTap_main  # type: ignore[attr-defined]
from trnsysGUI.crystalizer import Crystalizer
from trnsysGUI.deleteBlockCommand import DeleteBlockCommand
from trnsysGUI.connectors.doubleDoublePipeConnector import DoubleDoublePipeConnector
from trnsysGUI.doublePipeTeePiece import DoublePipeTeePiece
from trnsysGUI.geotherm import Geotherm
from trnsysGUI.connectors.singleDoublePipeConnector import SingleDoublePipeConnector
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
            componentType = str(event.mimeData().data("component/name"), encoding="utf-8")
            self.logger.debug("name is " + componentType)
            if componentType == "StorageTank":
                blockItem = StorageTank(componentType, self, displayNamePrefix="Tes")
                self.parent().showConfigStorageDlg(blockItem)
            elif componentType == "TeePiece":
                blockItem = TeePiece(componentType, self, displayNamePrefix="Tee")
            elif componentType == "DPTee":
                blockItem = DoublePipeTeePiece(componentType, self, displayNamePrefix="DTee")
            elif componentType == "SPCnr":
                blockItem = SingleDoublePipeConnector(componentType, self, displayNamePrefix="SCnr")
            elif componentType == "DPCnr":
                blockItem = DoubleDoublePipeConnector(componentType, self, displayNamePrefix="DCnr")
            elif componentType == "TVentil":
                blockItem = TVentil(componentType, self, displayNamePrefix="Val")
            elif componentType == "Pump":
                blockItem = Pump(componentType, self, displayNamePrefix="Pump")
            elif componentType == "Collector":
                blockItem = Collector(componentType, self, displayNamePrefix="Coll")
            elif componentType == "HP":
                blockItem = HeatPump(componentType, self, displayNamePrefix="HP")
            elif componentType == "IceStorage":
                blockItem = IceStorage(componentType, self, displayNamePrefix="IceS")
            elif componentType == "PitStorage":
                blockItem = PitStorage(componentType, self, displayNamePrefix="PitS")
            elif componentType == "Radiator":
                blockItem = Radiator(componentType, self, displayNamePrefix="Rad")
            elif componentType == "WTap":
                blockItem = WTap(componentType, self, displayNamePrefix="WtTp")
            elif componentType == "WTap_main":
                blockItem = WTap_main(componentType, self, displayNamePrefix="WtSp")
            elif componentType == "Connector":
                blockItem = Connector(componentType, self, displayNamePrefix="Conn")
            elif componentType == "GenericBlock":
                blockItem = GenericBlock(componentType, self, displayNamePrefix="GBlk")
                self.parent().showGenericPortPairDlg(blockItem)
            elif componentType == "HPTwoHx":
                blockItem = HeatPumpTwoHx(componentType, self, displayNamePrefix="HP")
            elif componentType == "HPDoubleDual":
                blockItem = HPDoubleDual(componentType, self, displayNamePrefix="HPDD")
            elif componentType == "HPDual":
                blockItem = HPDual(componentType, self, displayNamePrefix="HPDS")
            elif componentType == "Boiler":
                blockItem = Boiler(componentType, self, displayNamePrefix="Bolr")
            elif componentType == "AirSourceHP":
                blockItem = AirSourceHP(componentType, self, displayNamePrefix="Ashp")
            elif componentType == "PV":
                blockItem = PV(componentType, self, displayNamePrefix="PV")
            elif componentType == "GroundSourceHx":
                blockItem = GroundSourceHx(componentType, self, displayNamePrefix="Gshx")
            elif componentType == "ExternalHx":
                blockItem = ExternalHx(componentType, self, displayNamePrefix="Hx")
            elif componentType == "IceStorageTwoHx":
                blockItem = IceStorageTwoHx(componentType, self, displayNamePrefix="IceS")
            elif componentType == "GraphicalItem":
                blockItem = GraphicalItem(self)
            elif componentType == "MasterControl":
                blockItem = MasterControl(componentType, self)
            elif componentType == "Control":
                blockItem = Control(componentType, self)
            elif componentType == "Sink":
                blockItem = Sink(componentType, self, displayNamePrefix="QSnk")
            elif componentType == "Source":
                blockItem = Source(componentType, self, displayNamePrefix="QSrc")
            elif componentType == "SourceSink":
                blockItem = SourceSink(componentType, self, displayNamePrefix="QExc")
            elif componentType == "Geotherm":
                blockItem = Geotherm(componentType, self, displayNamePrefix="GeoT")
            elif componentType == "Water":
                blockItem = Water(componentType, self, displayNamePrefix="QWat")
            elif componentType == "Crystalizer":
                blockItem = Crystalizer(componentType, self, displayNamePrefix="Cryt")
            elif componentType == "powerBlock":
                blockItem = SteamPowerBlock(componentType, self, displayNamePrefix="StPB")
            elif componentType == "ParabolicTroughField":
                blockItem = ParabolicTroughField(componentType, self, displayNamePrefix="PT")
            elif componentType == "CR":
                blockItem = CentralReceiver(componentType, self, displayNamePrefix="CR")
            elif componentType == "coldStore":
                blockItem = SaltTankCold(componentType, self, displayNamePrefix="ClSt")
            elif componentType == "hotStore":
                blockItem = SaltTankHot(componentType, self, displayNamePrefix="HtSt")
            else:
                blockItem = BlockItem(componentType, self, displayNamePrefix="Blk")

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
