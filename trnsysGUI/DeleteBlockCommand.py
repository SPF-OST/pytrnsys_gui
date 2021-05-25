# pylint: skip-file
# type: ignore

from PyQt5.QtWidgets import QUndoCommand

import trnsysGUI.Collector
import trnsysGUI.Connector
import trnsysGUI.GenericBlock
import trnsysGUI.HeatPump
import trnsysGUI.HeatPumpTwoHx
import trnsysGUI.IceStorage
import trnsysGUI.Pump
import trnsysGUI.Radiator
import trnsysGUI.StorageTank
import trnsysGUI.TVentil
import trnsysGUI.TeePiece
import trnsysGUI.WTap
import trnsysGUI.WTap_main
import trnsysGUI.Boiler
import trnsysGUI.BlockItem
import trnsysGUI.AirSourceHP
import trnsysGUI.PV


class DeleteBlockCommand(QUndoCommand):
    def __init__(self, bl, descr):
        super(DeleteBlockCommand, self).__init__(descr)
        self.bl = bl
        self.blW = bl.w
        self.blH = bl.h
        self.blParent = bl.parent
        self.blId = bl.id
        self.blTrnsysId = bl.trnsysId

        self.portsIdIn = []
        self.portsIdOut = []
        self.savePortsId()

        self.blFlippedH = bl.flippedH
        self.blFlippedV = bl.flippedV
        self.blRotation = bl.rotationN
        self.blGroupName = bl.groupName
        self.blName = bl.name
        self.bldName = bl.displayName
        self.blPos = bl.pos()

    def redo(self):
        self.bl.deleteBlock()
        self.bl = None

    def undo(self):
        name = self.blName
        if name == "StorageTank":
            bl = trnsysGUI.StorageTank.StorageTank(name, self.blParent)
        elif name == "TeePiece":
            bl = trnsysGUI.TeePiece.TeePiece(name, self.blParent)
        elif name == "TVentil":
            bl = trnsysGUI.TVentil.TVentil(name, self.blParent)
        elif name == "Pump":
            bl = trnsysGUI.Pump.Pump(name, self.blParent)
        elif name == "Collector":
            bl = trnsysGUI.Collector.Collector(name, self.blParent)
        elif name == "HP":
            bl = trnsysGUI.HeatPump.HeatPump(name, self.blParent)
        elif name == "IceStorage":
            bl = trnsysGUI.IceStorage.IceStorage(name, self.blParent)
        elif name == "Radiator":
            bl = trnsysGUI.Radiator.Radiator(name, self.blParent)
        elif name == "WTap":
            bl = trnsysGUI.WTap.WTap(name, self.blParent)
        elif name == "WTap_main":
            bl = trnsysGUI.WTap_mainW.Tap_main(name, self.blParent)
        elif name == "Connector":
            bl = trnsysGUI.Connector.Connector(name, self.blParent)
        elif name == "GenericBlock":
            bl = trnsysGUI.GenericBlock.GenericBlock(name, self.blParent)
        elif name == "HPTwoHx":
            bl = trnsysGUI.HeatPumpTwoHx.HeatPumpTwoHx(name, self.blParent)
        elif name == "Boiler":
            bl = trnsysGUI.Boiler.Boiler(name, self.blParent)
        elif name == "AirSourceHP":
            bl = trnsysGUI.AirSourceHP.AirSourceHP(name, self.blParent)
        elif name == "PV":
            bl = trnsysGUI.PV.PV
        elif name == "GroundSourceHx":
            bl = trnsysGUI.GroundSourceHx.GroundSourceHx(name, self.blParent)
        else:
            bl = trnsysGUI.BlockItem.BlockItem(name, self.blParent)

        bl.trnsysId = self.blTrnsysId
        bl.id = self.blId
        bl.updateFlipStateH(self.blFlippedH)
        bl.updateFlipStateV(self.blFlippedV)
        bl.rotateBlockToN(self.blRotation)
        bl.displayName = self.bldName
        bl.label.setPlainText(bl.displayName)

        bl.groupName = "defaultGroup"
        bl.setBlockToGroup(self.blGroupName)

        bl.setPos(self.blPos)
        self.blParent.scene().addItem(bl)

        bl.oldPos = bl.scenePos()

    def savePortsId(self):
        for p in self.bl.inputs:
            self.portsIdIn.append(p.id)
        for p in self.bl.outputs:
            self.portsIdOut.append(p.id)


# From stackoverflow, this should have helped:

# from trnsysGUI.Collector import Collector
# from trnsysGUI.Connector import Connector
# from trnsysGUI.GenericBlock import GenericBlock
# from trnsysGUI.HeatPump import HeatPump
# from trnsysGUI.HeatPumpTwoHx import HeatPumpTwoHx
# from trnsysGUI.IceStorage import IceStorage
# from trnsysGUI.Pump import Pump
# from trnsysGUI.Radiator import Radiator
# from trnsysGUI.StorageTank import StorageTank
# from trnsysGUI.TVentil import TVentil
# from trnsysGUI.TeePiece import TeePiece
# from trnsysGUI.WTap import WTap
# from trnsysGUI.WTap_main import WTap_main
#
# from trnsysGUI.BlockItem import BlockItem
