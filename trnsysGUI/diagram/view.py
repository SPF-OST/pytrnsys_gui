from __future__ import annotations

import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

from trnsysGUI.AirSourceHP import AirSourceHP  # type: ignore[attr-defined]
from trnsysGUI.BlockItem import BlockItem  # type: ignore[attr-defined]
from trnsysGUI.Boiler import Boiler  # type: ignore[attr-defined]
from trnsysGUI.CentralReceiver import CentralReceiver  # type: ignore[attr-defined]
from trnsysGUI.Collector import Collector  # type: ignore[attr-defined]
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
from trnsysGUI.PV import PV  # type: ignore[attr-defined]
from trnsysGUI.ParabolicTroughField import ParabolicTroughField  # type: ignore[attr-defined]
from trnsysGUI.PitStorage import PitStorage  # type: ignore[attr-defined]
from trnsysGUI.Radiator import Radiator  # type: ignore[attr-defined]
from trnsysGUI.SaltTankCold import SaltTankCold  # type: ignore[attr-defined]
from trnsysGUI.SaltTankHot import SaltTankHot  # type: ignore[attr-defined]
from trnsysGUI.SteamPowerBlock import SteamPowerBlock  # type: ignore[attr-defined]
from trnsysGUI.TVentil import TVentil  # type: ignore[attr-defined]
from trnsysGUI.TeePiece import TeePiece  # type: ignore[attr-defined]
from trnsysGUI.WTap import WTap  # type: ignore[attr-defined]
from trnsysGUI.WTap_main import WTap_main  # type: ignore[attr-defined]
from trnsysGUI.connectors.connector import Connector  # type: ignore[attr-defined]
from trnsysGUI.connectors.doubleDoublePipeConnector import DoubleDoublePipeConnector
from trnsysGUI.connectors.singleDoublePipeConnector import SingleDoublePipeConnector
from trnsysGUI.crystalizer import Crystalizer
from trnsysGUI.deleteBlockCommand import DeleteBlockCommand
from trnsysGUI.doublePipeTeePiece import DoublePipeTeePiece
from trnsysGUI.geotherm import Geotherm
from trnsysGUI.pump import Pump  # type: ignore[attr-defined]
from trnsysGUI.sink import Sink
from trnsysGUI.source import Source
from trnsysGUI.sourceSink import SourceSink
from trnsysGUI.storageTank.widget import StorageTank
from trnsysGUI.water import Water

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
            if componentType == "StorageTank":
                blockItem = StorageTank(componentType, self._editor, displayNamePrefix="Tes")
                blockItem.setHydraulicLoops(self._editor.hydraulicLoops)
                self._editor.showConfigStorageDlg(blockItem)
            elif componentType == "TeePiece":
                blockItem = TeePiece(componentType, self._editor, displayNamePrefix="Tee")
            elif componentType == "DPTee":
                blockItem = DoublePipeTeePiece(componentType, self._editor, displayNamePrefix="DTee")
            elif componentType == "SPCnr":
                blockItem = SingleDoublePipeConnector(componentType, self._editor, displayNamePrefix="SCnr")
            elif componentType == "DPCnr":
                blockItem = DoubleDoublePipeConnector(componentType, self._editor, displayNamePrefix="DCnr")
            elif componentType == "TVentil":
                blockItem = TVentil(componentType, self._editor, displayNamePrefix="Val")
            elif componentType == "Pump":
                blockItem = Pump(componentType, self._editor, displayNamePrefix="Pump")
            elif componentType == "Collector":
                blockItem = Collector(componentType, self._editor, displayNamePrefix="Coll")
            elif componentType == "HP":
                blockItem = HeatPump(componentType, self._editor, displayNamePrefix="HP")
            elif componentType == "IceStorage":
                blockItem = IceStorage(componentType, self._editor, displayNamePrefix="IceS")
            elif componentType == "PitStorage":
                blockItem = PitStorage(componentType, self._editor, displayNamePrefix="PitS")
            elif componentType == "Radiator":
                blockItem = Radiator(componentType, self._editor, displayNamePrefix="Rad")
            elif componentType == "WTap":
                blockItem = WTap(componentType, self._editor, displayNamePrefix="WtTp")
            elif componentType == "WTap_main":
                blockItem = WTap_main(componentType, self._editor, displayNamePrefix="WtSp")
            elif componentType == "Connector":
                blockItem = Connector(componentType, self._editor, displayNamePrefix="Conn")
            elif componentType == "GenericBlock":
                blockItem = GenericBlock(componentType, self._editor, displayNamePrefix="GBlk")
                self._editor.showGenericPortPairDlg(blockItem)
            elif componentType == "HPTwoHx":
                blockItem = HeatPumpTwoHx(componentType, self._editor, displayNamePrefix="HP")
            elif componentType == "HPDoubleDual":
                blockItem = HPDoubleDual(componentType, self._editor, displayNamePrefix="HPDD")
            elif componentType == "HPDual":
                blockItem = HPDual(componentType, self._editor, displayNamePrefix="HPDS")
            elif componentType == "Boiler":
                blockItem = Boiler(componentType, self._editor, displayNamePrefix="Bolr")
            elif componentType == "AirSourceHP":
                blockItem = AirSourceHP(componentType, self._editor, displayNamePrefix="Ashp")
            elif componentType == "PV":
                blockItem = PV(componentType, self._editor, displayNamePrefix="PV")
            elif componentType == "GroundSourceHx":
                blockItem = GroundSourceHx(componentType, self._editor, displayNamePrefix="Gshx")
            elif componentType == "ExternalHx":
                blockItem = ExternalHx(componentType, self._editor, displayNamePrefix="Hx")
            elif componentType == "IceStorageTwoHx":
                blockItem = IceStorageTwoHx(componentType, self._editor, displayNamePrefix="IceS")
            elif componentType == "GraphicalItem":
                blockItem = GraphicalItem(self._editor)
            elif componentType == "MasterControl":
                blockItem = MasterControl(componentType, self._editor)
            elif componentType == "Control":
                blockItem = Control(componentType, self._editor)
            elif componentType == "Sink":
                blockItem = Sink(componentType, self._editor, displayNamePrefix="QSnk")
            elif componentType == "Source":
                blockItem = Source(componentType, self._editor, displayNamePrefix="QSrc")
            elif componentType == "SourceSink":
                blockItem = SourceSink(componentType, self._editor, displayNamePrefix="QExc")
            elif componentType == "Geotherm":
                blockItem = Geotherm(componentType, self._editor, displayNamePrefix="GeoT")
            elif componentType == "Water":
                blockItem = Water(componentType, self._editor, displayNamePrefix="QWat")
            elif componentType == "Crystalizer":
                blockItem = Crystalizer(componentType, self._editor, displayNamePrefix="Cryt")
            elif componentType == "powerBlock":
                blockItem = SteamPowerBlock(componentType, self._editor, displayNamePrefix="StPB")
            elif componentType == "CSP_PT":
                blockItem = ParabolicTroughField(componentType, self._editor, displayNamePrefix="PT")
            elif componentType == "CSP_CR":
                blockItem = CentralReceiver(componentType, self._editor, displayNamePrefix="CR")
            elif componentType == "coldSaltTank":
                blockItem = SaltTankCold(componentType, self._editor, displayNamePrefix="ClSt")
            elif componentType == "hotSaltTank":
                blockItem = SaltTankHot(componentType, self._editor, displayNamePrefix="HtSt")
            else:
                blockItem = BlockItem(componentType, self._editor, displayNamePrefix="Blk")

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
        command = DeleteBlockCommand(blockItem, self._editor)
        self._editor.parent().undoStack.push(command)

    @staticmethod
    def _getBlockItem(componentType, editor):
        blockItems = {"StorageTank": {"blockItem": StorageTank, "displayNamePrefix": "Tes"},
                      "TeePiece": {"blockItem": TeePiece, "displayNamePrefix": "Tee"},
                      "DPTee": {"blockItem": DoublePipeTeePiece, "displayNamePrefix": "DTee"},
                      "SPCnr": {"blockItem": SingleDoublePipeConnector, "displayNamePrefix": "SCnr"},
                      "DPCnr": {"blockItem": DoubleDoublePipeConnector, "displayNamePrefix": "DCnr"},
                      "TVentil": {"blockItem": TVentil, "displayNamePrefix": "Val"},
                      "Pump": {"blockItem": Pump, "displayNamePrefix": "Pump"},
                      "Collector": {"blockItem": Collector, "displayNamePrefix": "Coll"},
                      "HP": {"blockItem": HeatPump, "displayNamePrefix": "HP"},
                      "IceStorage": {"blockItem": IceStorage, "displayNamePrefix": "IceS"},
                      "PitStorage": {"blockItem": PitStorage, "displayNamePrefix": "PitS"},
                      "Radiator": {"blockItem": Radiator, "displayNamePrefix": "Rad"},
                      "WTap": {"blockItem": WTap, "displayNamePrefix": "WtTp"},
                      "WTap_main": {"blockItem": WTap_main, "displayNamePrefix": "WtSp"},
                      "Connector": {"blockItem": Connector, "displayNamePrefix": "Conn"},
                      "GenericBlock": {"blockItem": GenericBlock, "displayNamePrefix": "GBlk"},
                      "HPTwoHx": {"blockItem": HeatPumpTwoHx, "displayNamePrefix": "HP"},
                      "HPDoubleDual": {"blockItem": HPDoubleDual, "displayNamePrefix": "HPDD"},
                      "HPDual": {"blockItem": HPDual, "displayNamePrefix": "HPDS"},
                      "Boiler": {"blockItem": Boiler, "displayNamePrefix": "Bolr"},
                      "AirSourceHP": {"blockItem": AirSourceHP, "displayNamePrefix": "Ashp"},
                      "PV": {"blockItem": PV, "displayNamePrefix": "PV"},
                      "GroundSourceHx": {"blockItem": GroundSourceHx, "displayNamePrefix": "Gshx"},
                      "ExternalHx": {"blockItem": ExternalHx, "displayNamePrefix": "Hx"},
                      "IceStorageTwoHx": {"blockItem": IceStorageTwoHx, "displayNamePrefix": "IceS"},
                      "GraphicalItem": {"blockItem": GraphicalItem, "displayNamePrefix": None},
                      # None entries will likely cause issues
                      "MasterControl": {"blockItem": MasterControl, "displayNamePrefix": None},
                      "Control": {"blockItem": Control, "displayNamePrefix": None},
                      "Sink": {"blockItem": Sink, "displayNamePrefix": "QSnk"},
                      "Source": {"blockItem": Source, "displayNamePrefix": "QSrc"},
                      "SourceSink": {"blockItem": SourceSink, "displayNamePrefix": "QExc"},
                      "Geotherm": {"blockItem": Geotherm, "displayNamePrefix": "GeoT"},
                      "Water": {"blockItem": Water, "displayNamePrefix": "QWat"},
                      "Crystalizer": {"blockItem": Crystalizer, "displayNamePrefix": "Cryt"},
                      "powerBlock": {"blockItem": SteamPowerBlock, "displayNamePrefix": "StPB"},
                      "CSP_PT": {"blockItem": ParabolicTroughField, "displayNamePrefix": "PT"},
                      "CSP_CR": {"blockItem": CentralReceiver, "displayNamePrefix": "CR"},
                      "coldSaltTank": {"blockItem": SaltTankCold, "displayNamePrefix": "ClSt"},
                      "hotSaltTank": {"blockItem": SaltTankHot, "displayNamePrefix": "HtSt"},
                      "Blk": {"blockItem": BlockItem, "displayNamePrefix": "Blk"},
                      }
        if componentType not in blockItems:
            parts = blockItems["Blk"]
        else:
            parts = blockItems[componentType]

        if parts["blockItem"] == GraphicalItem:  # may not be needed
            blockItem = parts["blockItem"](editor)
        elif (parts["blockItem"] == MasterControl) or (parts["blockItem"] == Control):
            blockItem = parts["blockItem"](componentType, editor)
        else:
            blockItem = parts["blockItem"](componentType, editor, displayNamePrefix=parts["displayNamePrefix"])

        return blockItem

    def _dropEventRedone(self, event):  # pylint: disable=too-many-branches,too-many-statements
        """Here, the dropped icons create BlockItems/GraphicalItems"""
        if event.mimeData().hasFormat("component/name"):
            componentType = str(event.mimeData().data("component/name"), encoding="utf-8")
            self.logger.debug("name is " + componentType)
            blockItem = self._getBlockItem(componentType)
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
