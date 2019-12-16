#!/usr/bin/python
# import random
import string
from math import sqrt, acos, pi, degrees, atan

import sys
# import os
import json
from pathlib import Path

# import qrc_resources
# import platform
# import inspect

# from trnsysGUI.CircularDep import *
# from trnsysGUI.Connection import Connection
# from trnsysGUI.GenericBlock import GenericBlock
from trnsysGUI.PortItem import PortItem
from trnsysGUI.diagramDlg import diagramDlg
from trnsysGUI.groupDlg import groupDlg
from trnsysGUI.groupsEditor import groupsEditor
from trnsysGUI.newDiagramDlg import newDiagramDlg

from trnsysGUI.BlockItem import BlockItem

from trnsysGUI.Collector import Collector
from trnsysGUI.ConfigStorage import ConfigStorage
from trnsysGUI.Connector import Connector
from trnsysGUI.Group import Group
from trnsysGUI.HeatPump import HeatPump
from trnsysGUI.IceStorage import IceStorage
from trnsysGUI.LibraryModel import LibraryModel
from trnsysGUI.Pump import Pump
from trnsysGUI.Radiator import Radiator
from trnsysGUI.StorageTank import StorageTank
from trnsysGUI.HeatExchanger import HeatExchanger
from trnsysGUI.TVentil import TVentil
from trnsysGUI.TeePiece import TeePiece
from trnsysGUI.WTap import WTap
from trnsysGUI.WTap_main import WTap_main
from trnsysGUI.copyGroup import copyGroup
from trnsysGUI.IdGenerator import IdGenerator
from trnsysGUI.Connection import Connection

from PyQt5 import QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

__version__ = "1.0.0"
__author__ = "Stefano Marti"
__email__ = "stefano.marti@spf.ch"
__status__ = "Prototype"

cssSs = open("res/style.txt", "r")

# global globalID
# globalID = 0
#
# global globalConnID
# globalConnID = 0
#
# global trnsysID
# trnsysID = 0
#
# global globalSegID
# globalSegID = 0

def encode_Block(bl):
    print("bl is " + str(type(bl)))
    if isinstance(bl, BlockItem):
        return {"__Block__": True,
                "Name": bl.name,
                "dispName": bl.displayName,
                "Position": bl.pos(),
                "GroupName": bl.groupName,
                "ID": bl.id}
    else:
        type_name = bl.__class__.__name__
        raise TypeError("Object of type '{}' is not JSON serializable".format(type_name))


def calcDist(p1, p2):
    vec = p1 - p2
    norm = sqrt(vec.x() ** 2 + vec.y() ** 2)
    return norm


class DiagramDecoderPaste(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        self.editor = kwargs["editor"]
        kwargs.pop("editor")
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, arr):
        # Object hook seem to get executed for every sub object in the json file.
        # print(arr)
        # # print("type is " + str(type(arr)))

        resBlockList = []
        offset_x = 300
        offset_y = 100
        if ".__BlockDct__" in arr:
            # print("Found the block holding dict")
            # print(arr)  # all objects up to level of .__BlockDct__
            # print(type(arr))    # dict

            resConnList = []
            print("keys are " + str(sorted((arr.keys()))))
            for k in sorted((arr.keys())):
                if type(arr[k]) is dict:
                    # print("Found a block or Connection")
                    if ".__BlockDict__" in arr[k]:
                        # print("Found a block ")
                        i = arr[k]

                        # print("Bl name " +  arr[k]["BlockName"] + str(type(arr[k]["BlockName"])))
                        # print("Bl disp name " +  arr[k]["BlockDisplayName"])

                        if i["BlockName"] == 'StorageTank':
                            print("No storage tank should be found here")
                            bl = StorageTank(i["BlockName"], i["BlockDisplayName"] + "COPY", self.editor.diagramView)
                            # c = ConfigStorage(bl, self.editor.diagramView)
                        elif i["BlockName"] == 'TeePiece':
                            bl = TeePiece(i["BlockName"], i["BlockDisplayName"] + "COPY", self.editor.diagramView)
                        elif i["BlockName"] == 'TVentil':
                            bl = TVentil(i["BlockName"], i["BlockDisplayName"] + "COPY", self.editor.diagramView)
                        elif i["BlockName"] == 'Pump':
                            bl = Pump(i["BlockName"], i["BlockDisplayName"] + "COPY", self.editor.diagramView)
                        elif i["BlockName"] == 'Kollektor':
                            bl = Collector(i["BlockName"], i["BlockDisplayName"] + "COPY", self.editor.diagramView)
                        elif i["BlockName"] == 'HP':
                            bl = HeatPump(i["BlockName"], i["BlockDisplayName"] + "COPY", self.editor.diagramView)
                        elif i["BlockName"] == 'IceStorage':
                            bl = IceStorage(i["BlockName"], i["BlockDisplayName"] + "COPY", self.editor.diagramView)
                        elif i["BlockName"] == 'Radiator':
                            bl = Radiator(i["BlockName"], i["BlockDisplayName"] + "COPY", self.editor.diagramView)
                        elif i["BlockName"] == 'WTap':
                            bl = WTap(i["BlockName"], i["BlockDisplayName"] + "COPY", self.editor.diagramView)
                        elif i["BlockName"] == 'WTap_main':
                            bl = WTap_main(i["BlockName"], i["BlockDisplayName"] + "COPY", self.editor.diagramView)
                        elif i["BlockName"] == 'Connector':
                            bl = Connector(i["BlockName"], i["BlockDisplayName"] + "COPY", self.editor.diagramView)
                        else:
                            bl = BlockItem(i["BlockName"], i["BlockName"] + "COPY", self.editor.diagramView)
                        # print("Bl name is" + bl.name)

                        bl.setPos(float(i["BlockPosition"][0] + offset_x),
                                  float(i["BlockPosition"][1] + offset_y))

                        # bl.trnsysId = i["trnsysID"]
                        bl.updateFlipStateH(i["FlippedH"])
                        bl.updateFlipStateV(i["FlippedV"])
                        bl.rotateBlockToN(i["RotationN"])

                        for x in range(len(bl.inputs)):
                            bl.inputs[x].id = i["PortsIDIn"][x]

                        for x in range(len(bl.outputs)):
                            bl.outputs[x].id = i["PortsIDOut"][x]

                        resBlockList.append(bl)

                    elif ".__HeatPumpDict__" in arr[k]:
                        print("Loading a HeatPump in Decoder")
                        i = arr[k]
                        bl = HeatPump(i["HeatPumpName"], i["HeatPumpDisplayName"] + "COPY", self.editor.diagramView)
                        # bl.flippedH = i["FlippedH"]
                        # bl.flippedV = i["FlippedV"]
                        # bl.childIds = i["childIds"]

                        bl.changeSize()

                        for x in range(len(bl.inputs)):
                            bl.inputs[x].id = i["PortsIDIn"][x]
                            print("Input at heatExchanger")

                        for x in range(len(bl.outputs)):
                            bl.outputs[x].id = i["PortsIDOut"][x]
                            print("Output at heatExchanger")

                        bl.setPos(float(i["HeatPumpPosition"][0]) + offset_x, float(i["HeatPumpPosition"][1] + offset_y))
                        # bl.trnsysId = i["trnsysID"]
                        # bl.id = i["ID"]

                        resBlockList.append(bl)

                    elif ".__StorageDict__" in arr[k]:
                        print("Loading a Storage in Decoder")
                        i = arr[k]
                        bl = StorageTank(i["StorageName"], i["StorageDisplayName"] + "COPY", self.editor.diagramView)
                        bl.flippedH = i["FlippedH"]
                        # bl.flippedV = i["FlippedV"] # No support for vertical flip
                        bl.changeSize()

                        bl.setPos(float(i["StoragePosition"][0]) + offset_x, float(i["StoragePosition"][1]) + offset_y)
                        # bl.trnsysId = i["trnsysID"]
                        # bl.id = i["ID"]
                        # Add heat exchanger
                        for h in i["HxList"]:
                            hEx = HeatExchanger(h["SideNr"], h["Width"], h["Height"],
                                                QPointF(h["Offset"][0], h["Offset"][1]),
                                                bl, h["DisplayName"] + "New",
                                                port1ID=h['Port1ID'], port2ID=h['Port2ID'], connTrnsysID=self.editor.idGen.getTrnsysID())

                            # hEx.setId(["ID"])
                            hEx.port1.id = h['Port1ID']
                            hEx.port2.id = h['Port2ID']

                            # hxDct['ParentID'] = hx.parent.id
                            # hxDct['Port2ID'] = hx.port2.id

                        # Add manual inputs
                        for x in i["PortPairList"]:
                            print("Printing port pair")
                            print(x)

                            conn = bl.setSideManualPair(x["Side"], x["Port1offset"], x["Port2offset"],
                                                        fromPortId=x["Port1ID"], toPortId=x["Port2ID"],
                                                        connId=self.editor.idGen.getID(), connCid=self.editor.idGen.getConnID(),
                                                        connDispName=x["ConnDisName"] + "New",
                                                        trnsysConnId=self.editor.idGen.getTrnsysID())

                            # conn.id = x["ConnID"]
                            # conn.connId = x["ConnCID"]
                            # conn.trnsysId = x["trnsysID"]
                            # conn.displayName = x["ConnDisName"]

                            # resStorageConnList.append(conn)
                            resConnList.append(conn)
                        resBlockList.append(bl)

                    elif ".__ConnectionDict__" in arr[k]:
                        i = arr[k]

                        fport = None
                        tPort = None
                        print("Loading a connection in paste")
                        print("blocks are " + str(resBlockList))

                        for connBl in resBlockList:
                            # if "COPY" in connBl.displayName and connBl.displayName[-4:None] == 'COPY':
                            if True:
                                for p in connBl.inputs + connBl.outputs:
                                    if p.id == i["PortFromID"]:
                                        fport = p
                                    if p.id == i["PortToID"]:
                                        tPort = p

                        if fport is None:
                            print("Did not found a fromPort")

                        if tPort is None:
                            print("Did not found a tPort")

                        # if not i["isBlockConn"]:  # Now internal connections don't get encoded in the first place
                        if True:
                            for cornerL in i["CornerPositions"]:
                                cornerL[0] += offset_x
                                cornerL[1] += offset_y

                            c = Connection(fport, tPort, i["isBlockConn"], self.editor,
                                           fromPortId=i["PortFromID"], toPortId=i["PortToID"],
                                           segmentsLoad=i["SegmentPositions"], cornersLoad=i["CornerPositions"])
                            # c.id = i["ConnID"]
                            # c.connId = i["ConnCID"]
                            # c.trnsysId = i["trnsysID"]
                            c.displayName = i["ConnDisplayName"] + "COPY"

                            # Note: This wouldn't allow two connections to the same port (which is not really used, but ok)
                            # fport.id = getID()
                            # tPort.id = getID()
                            resConnList.append(c)
                        else:
                            print("This is an internal connection (e.g. in the storage) and thus is not created now")

                    elif "__idDct__" in arr[k]:
                        resBlockList.append(arr[k])
                    else:
                        print("Error: Not recognized object in decoder")

            # return resBlockList, resConnList, resStorageConnList
            return resBlockList, resConnList

        return arr


class DiagramDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        self.editor = kwargs["editor"]
        kwargs.pop("editor")
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, arr):
        # Object hook seem to get executed for every sub object in the json file.

        # print(arr)
        # # print("type is " + str(type(arr)))

        resBlockList = []

        if ".__BlockDct__" in arr:
            # print("Found the block holding dict")
            # print(arr)  # all objects up to level of .__BlockDct__
            # print(type(arr))    # dict

            resConnList = []
            print("keys are " + str(sorted((arr.keys()))))
            for k in sorted((arr.keys())):
                if type(arr[k]) is dict:
                    # print("Found a block or Connection")

                    if ".__GroupDict__" in arr[k]:
                        print("Found the group dict")
                        i = arr[k]
                        print("Decoding group " + str(i["GroupName"]))

                        groupListNames = [g.displayName for g in self.editor.groupList]

                        if i["GroupName"] not in groupListNames:
                            g = Group(i["Position"][0], i["Position"][1], i["Size"][0], i["Size"][1], self.editor.diagramScene)
                            g.setName(i["GroupName"])

                    elif ".__BlockDict__" in arr[k]:
                        print("Found a block ")
                        i = arr[k]

                        # print("Bl name " +  arr[k]["BlockName"] + str(type(arr[k]["BlockName"])))
                        # print("Bl disp name " +  arr[k]["BlockDisplayName"])

                        if i["BlockName"] == 'StorageTank':
                            print("Decoder should not find a Storage here")
                            bl = StorageTank(i["BlockName"], i["BlockDisplayName"], self.editor.diagramView)
                            # c = ConfigStorage(bl, self.editor.diagramView)
                        elif i["BlockName"] == 'TeePiece':
                            bl = TeePiece(i["BlockName"], i["BlockDisplayName"], self.editor.diagramView)
                        elif i["BlockName"] == 'TVentil':
                            bl = TVentil(i["BlockName"], i["BlockDisplayName"], self.editor.diagramView)
                        elif i["BlockName"] == 'Pump':
                            bl = Pump(i["BlockName"], i["BlockDisplayName"], self.editor.diagramView)
                        elif i["BlockName"] == 'Kollektor':
                            bl = Collector(i["BlockName"], i["BlockDisplayName"], self.editor.diagramView)
                        elif i["BlockName"] == 'HP':
                            bl = HeatPump(i["BlockName"], i["BlockDisplayName"], self.editor.diagramView)
                            print("Encoder should not find a HeatPump here")
                        elif i["BlockName"] == 'IceStorage':
                            bl = IceStorage(i["BlockName"], i["BlockDisplayName"], self.editor.diagramView)
                        elif i["BlockName"] == 'Radiator':
                            bl = Radiator(i["BlockName"], i["BlockDisplayName"], self.editor.diagramView)
                        elif i["BlockName"] == 'WTap':
                            bl = WTap(i["BlockName"], i["BlockDisplayName"], self.editor.diagramView)
                        elif i["BlockName"] == 'WTap_main':
                            bl = WTap_main(i["BlockName"], i["BlockDisplayName"], self.editor.diagramView)
                        elif i["BlockName"] == 'Connector':
                            bl = Connector(i["BlockName"], i["BlockDisplayName"], self.editor.diagramView)
                        else:
                            bl = BlockItem(i["BlockName"], i["BlockName"
                                                             ""], self.editor.diagramView)
                        # print("Bl name is" + bl.name)

                        bl.setPos(float(i["BlockPosition"][0]), float(i["BlockPosition"][1]))
                        bl.trnsysId = i["trnsysID"]
                        bl.id = i["ID"]
                        bl.updateFlipStateH(i["FlippedH"])
                        bl.updateFlipStateV(i["FlippedV"])
                        bl.rotateBlockToN(i["RotationN"])
                        bl.displayName = i["BlockDisplayName"]
                        bl.label.setPlainText(bl.displayName)

                        bl.groupName = "defaultGroup"
                        bl.setBlockToGroup(i["GroupName"])

                        print(len(bl.inputs))
                        for x in range(len(bl.inputs)):
                            bl.inputs[x].id = i["PortsIDIn"][x]

                        for x in range(len(bl.outputs)):
                            bl.outputs[x].id = i["PortsIDOut"][x]

                        resBlockList.append(bl)

                    elif ".__StorageDict__" in arr[k]:
                        print("Loading a Storage in Decoder")
                        i = arr[k]
                        bl = StorageTank(i["StorageName"], i["StorageDisplayName"], self.editor.diagramView)
                        bl.flippedH = i["FlippedH"]
                        # bl.flippedV = i["FlippedV"] # No support for vertical flip
                        bl.displayName = i["StorageDisplayName"]

                        bl.changeSize()

                        bl.setPos(float(i["StoragePosition"][0]), float(i["StoragePosition"][1]))
                        bl.trnsysId = i["trnsysID"]
                        bl.id = i["ID"]

                        bl.groupName = "defaultGroup"
                        bl.setBlockToGroup(i["GroupName"])

                        # Add heat exchangers
                        for h in i["HxList"]:
                            hEx = HeatExchanger(h["SideNr"], h["Width"], h["Height"],
                                                QPointF(h["Offset"][0], h["Offset"][1]), bl, h["DisplayName"],
                                                port1ID=h['Port1ID'], port2ID=h['Port2ID'],
                                                connTrnsysID=h['connTrnsysID'])

                            hEx.setId(h["ID"])
                            hEx.port1.id = h['Port1ID']
                            hEx.port2.id = h['Port2ID']

                            # hxDct['ParentID'] = hx.parent.id
                            # hxDct['Port2ID'] = hx.port2.id

                        # Add manual inputs
                        for x in i["PortPairList"]:
                            print("Printing port pair")
                            print(x)

                            conn = bl.setSideManualPair(x["Side"], x["Port1offset"], x["Port2offset"],
                                                        fromPortId=x["Port1ID"], toPortId=x["Port2ID"],
                                                        connId=x["ConnID"], connCid=x["ConnCID"],
                                                        connDispName=x["ConnDisName"], trnsysConnId=x["trnsysID"])
                            conn.id = x["ConnID"]
                            conn.connId = x["ConnCID"]
                            conn.trnsysId = x["trnsysID"]
                            conn.displayName = x["ConnDisName"]

                            resConnList.append(conn)
                        resBlockList.append(bl)

                    elif ".__HeatPumpDict__" in arr[k]:
                        print("Loading a HeatPump in Decoder")
                        i = arr[k]
                        bl = HeatPump(i["HeatPumpName"], i["HeatPumpDisplayName"], self.editor.diagramView)
                        bl.flippedH = i["FlippedH"]
                        bl.flippedV = i["FlippedV"]
                        bl.childIds = i["childIds"]
                        bl.displayName = i["HeatPumpName"]
                        bl.changeSize()

                        for x in range(len(bl.inputs)):
                            bl.inputs[x].id = i["PortsIDIn"][x]
                            print("Input at heatExchanger")

                        for x in range(len(bl.outputs)):
                            bl.outputs[x].id = i["PortsIDOut"][x]
                            print("Output at heatExchanger")

                        bl.setPos(float(i["HeatPumpPosition"][0]), float(i["HeatPumpPosition"][1]))
                        bl.trnsysId = i["trnsysID"]
                        bl.id = i["ID"]

                        bl.groupName = "defaultGroup"
                        bl.setBlockToGroup(i["GroupName"])

                        resBlockList.append(bl)

                    elif ".__ConnectionDict__" in arr[k]:
                        print("Loading a connection in Decoder")
                        i = arr[k]

                        fport = None
                        tPort = None

                        for connBl in resBlockList:
                            for p in connBl.inputs + connBl.outputs:
                                if p.id == i["PortFromID"]:
                                    fport = p
                                if p.id == i["PortToID"]:
                                    tPort = p

                        if fport is None:
                            print("Did not found a fromPort")

                        if tPort is None:
                            print("Did not found a tPort")

                        # if not i["isBlockConn"]:  # Now internal connections don't get encoded in the first place
                        if True:
                            c = Connection(fport, tPort, i["isBlockConn"], self.editor,
                                           fromPortId=i["PortFromID"], toPortId=i["PortToID"],
                                           segmentsLoad=i["SegmentPositions"], cornersLoad=i["CornerPositions"])
                            c.id = i["ConnID"]
                            c.connId = i["ConnCID"]
                            c.trnsysId = i["trnsysID"]
                            c.displayName = i["ConnDisplayName"]

                            c.groupName = "defaultGroup"
                            c.setConnToGroup(i["GroupName"])

                            resConnList.append(c)

                        else:
                            print("This is an internal connection (e.g. in the storage) and thus is not created now")

                    elif "__idDct__" in arr[k]:
                        resBlockList.append(arr[k])
                    elif "__nameDct__" in arr[k]:
                        resBlockList.append(arr[k])
                    else:
                        print("Error: Not recognized object in decoder, " + str(arr[k]))

            # return resBlockList, resConnList, resStorageConnList
            return resBlockList, resConnList

        return arr


# TrnsysObj are stored in a list of dictionaries
class DiagramEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, DiagramEditor) or isinstance(obj, copyGroup):
            print("Is diagram or copygroup")

            res = {}
            blockDct = {".__BlockDct__": True}

            for t in obj.trnsysObj:
                dct = {}
                if isinstance(t, BlockItem) and type(t) is not StorageTank and type(t) is not HeatPump:
                    if t.isVisible() is False:
                        print("Invisible block [probably a insideBlock?]" + str(t) + str(t.displayName))
                        continue
                    portListInputs = []
                    portListOutputs = []

                    for p in t.inputs:
                        portListInputs.append(p.id)
                    for p in t.outputs:
                        portListOutputs.append(p.id)

                    dct['.__BlockDict__'] = True
                    dct['BlockName'] = t.name
                    dct['BlockDisplayName'] = t.displayName
                    dct['BlockPosition'] = (float(t.pos().x()), float(t.pos().y()))
                    dct['ID'] = t.id
                    dct['trnsysID'] = t.trnsysId
                    dct['PortsIDIn'] = portListInputs
                    dct['PortsIDOut'] = portListOutputs
                    dct['FlippedH'] = t.flippedH
                    dct['FlippedV'] = t.flippedV
                    dct['RotationN'] = t.rotationN
                    dct['GroupName'] = t.groupName

                    blockDct["Block-" + str(t.id)] = dct

                if type(t) is StorageTank:
                    print("Encoding a storage tank")

                    hxList = []
                    for hx in t.heatExchangers:
                        hxDct = {"DisplayName": hx.displayName}
                        hxDct['ID'] = hx.id
                        hxDct['ParentID'] = hx.parent.id
                        hxDct['connTrnsysID'] = hx.conn.trnsysId
                        # hxDct['connDispName'] = hx.conn.diplayName    # Both are set in initNew
                        hxDct['Offset'] = (hx.offset.x(), hx.offset.y())
                        hxDct['Width'] = hx.w
                        hxDct['Height'] = hx.h
                        hxDct['SideNr'] = hx.sSide
                        hxDct['Port1ID'] = hx.port1.id
                        hxDct['Port2ID'] = hx.port2.id

                        hxList.append(hxDct)

                    portPairList = []

                    for manP in t.leftSide + t.rightSide:
                        manP.portPairVisited = True
                        print("This port is part of a manual port pair ")
                        for innerC in manP.connectionList:
                            print("There is a connection")
                            if innerC.fromPort is manP and type(innerC.toPort.parent) is StorageTank \
                                    and not innerC.toPort.portPairVisited:
                                print("Found the corresponding port")

                                portPairDct = {"Port1ID": manP.id}

                                b = t.hasManPortById(manP.id)

                                print("side encoded is" + str(b))

                                portPairDct["Side"] = b
                                portPairDct["Port1offset"] = float(manP.scenePos().y() - t.scenePos().y())
                                portPairDct["Port2ID"] = innerC.toPort.id
                                portPairDct["Port2offset"] = float(innerC.toPort.scenePos().y() - t.scenePos().y())
                                portPairDct["ConnDisName"] = innerC.displayName
                                portPairDct["ConnID"] = innerC.id
                                portPairDct["ConnCID"] = innerC.connId
                                portPairDct["trnsysID"] = innerC.trnsysId

                                portPairList.append(portPairDct)

                                # innerC.deleteConn()

                            elif innerC.toPort is manP and type(innerC.fromPort.parent) is StorageTank \
                                    and not innerC.fromPort.portPairVisited:

                                print("Found the corresponding port")

                                portPairDct = {"Port2ID": manP.id}

                                b = t.hasManPortById(manP.id)

                                print("side encoded is" + str(b))

                                portPairDct["Side"] = b
                                portPairDct["Port2offset"] = float(manP.scenePos().y() - t.scenePos().y())
                                portPairDct["Port1ID"] = innerC.fromPort.id
                                portPairDct["Port1offset"] = float(innerC.fromPort.scenePos().y() - t.scenePos().y())
                                portPairDct["ConnDisName"] = innerC.displayName
                                portPairDct["ConnID"] = innerC.id
                                portPairDct["ConnCID"] = innerC.connId
                                portPairDct["trnsysID"] = innerC.trnsysId

                                # print("Portpairlist is " + str(portPairDct))
                                portPairList.append(portPairDct)

                                # innerC.deleteConn()

                            else:
                                print("Did not found the corresponding (inner) port")

                    for manP in t.leftSide + t.rightSide:
                        manP.portPairVisited = False

                    dct['.__StorageDict__'] = True
                    dct['StorageName'] = t.name
                    dct['StorageDisplayName'] = t.displayName
                    dct['StoragePosition'] = (float(t.pos().x()), float(t.pos().y()))
                    dct['ID'] = t.id
                    dct['trnsysID'] = t.trnsysId
                    dct['HxList'] = hxList
                    dct['PortPairList'] = portPairList
                    dct['FlippedH'] = t.flippedH
                    dct['FlippedV'] = t.flippedH
                    dct['GroupName'] = t.groupName

                    # dct['RotationN'] = t.rotationN

                    blockDct["BlockStorage-" + str(t.id)] = dct

                if type(t) is HeatPump:
                    print("Encoding a HeatPump")

                    # childIdList = []

                    portListInputs = []
                    portListOutputs = []

                    for p in t.inputs:
                        portListInputs.append(p.id)
                    for p in t.outputs:
                        portListOutputs.append(p.id)

                    dct['.__HeatPumpDict__'] = True
                    dct['HeatPumpName'] = t.name
                    dct['HeatPumpDisplayName'] = t.displayName
                    dct['PortsIDIn'] = portListInputs
                    dct['PortsIDOut'] = portListOutputs
                    dct['HeatPumpPosition'] = (float(t.pos().x()), float(t.pos().y()))
                    dct['ID'] = t.id
                    dct['trnsysID'] = t.trnsysId
                    dct['childIds'] = t.childIds
                    dct['FlippedH'] = t.flippedH
                    dct['FlippedV'] = t.flippedH
                    dct['RotationN'] = t.rotationN
                    dct['GroupName'] = t.groupName


                    # Why does it not appear with this key??
                    blockDct["BlockHeatPump-" + str(t.id)] = dct

                # Theoretically the interpreter should only evaluate the right boolean if the left is true.
                if isinstance(t, Connection) and not t.isBlockConn:
                    print("Encoding a connection")

                    dct['.__ConnectionDict__'] = True
                    dct['PortFromID'] = t.fromPort.id
                    dct['PortToID'] = t.toPort.id
                    dct['isBlockConn'] = t.isBlockConn
                    dct['ConnDisplayName'] = t.displayName
                    dct['ConnID'] = t.id
                    dct['ConnCID'] = t.connId
                    dct['trnsysID'] = t.trnsysId
                    dct['GroupName'] = t.groupName

                    segments = []  # Not used, but instead corners[]

                    for s in t.segments:
                        segmentTupel = (s.line().p1().x(), s.line().p1().y(), s.line().p2().x(), s.line().p2().y())
                        segments.append(segmentTupel)
                    # print("Segments in encoder is " + str(segments))
                    dct['SegmentPositions'] = segments

                    corners = []

                    for s in t.getCorners():
                        cornerTupel = (s.pos().x(), s.pos().y())
                        corners.append(cornerTupel)
                    dct['CornerPositions'] = corners

                    # res.append(dct)
                    blockDct["Connection-" + str(t.id)] = dct

            idDict = {"__idDct__": True, "GlobalId": 0, "trnsysID": 0, "globalConnID": 0}
            blockDct["IDs"] = idDict

            nameDict = {"__nameDct__": True, "DiagramName": obj.diagramName}
            blockDct["Strings"] = nameDict

            # groupDict = {"..__GroupDict__": True}
            for g in obj.groupList:
                dct = {}
                dct[".__GroupDict__"] = True
                dct["GroupName"] = g.displayName
                dct["Position"] = g.x, g.y
                dct["Size"] = g.w, g.h
                # dct["..Group-" + g.displayName] = dct

                blockDct["..__GroupDct-" + g.displayName] = dct

            res["Blocks"] = blockDct

            return res
        else:
            print("This is a strange object in DiagramEncoder" + type(obj))
            # return super().default(obj)


class DiagramScene(QGraphicsScene):
    def __init__(self, parent=None):
        # Static size
        # super(DiagramScene, self).__init__(QRectF(0, 0, parent.height(), 1500), parent)
        # self.setSceneRect(0, 0, parent.height(), parent.width())

        # Dynamic size, but "zero" at beginning
        super(DiagramScene, self).__init__(parent)

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

        # self.viewRect1.setPos(-1300, -100)
        # self.viewRect2.setPos(-1300, -100)

        self.released = False
        self.pressed = False

    def mouseMoveEvent(self, mouseEvent):
        self.parent().sceneMouseMoveEvent(mouseEvent)
        super(DiagramScene, self).mouseMoveEvent(mouseEvent)

        # global selectionMode
        if self.parent().selectionMode and not self.released and self.pressed:
            self.selectionRect.setVisible(True)
            self.sRw = mouseEvent.scenePos().x() - self.sRstart.x()
            self.sRh = mouseEvent.scenePos().y() - self.sRstart.y()
            self.selectionRect.setRect(self.sRstart.x(), self.sRstart.y(), self.sRw, self.sRh)

    def mouseReleaseEvent(self, mouseEvent):
        # print("Releasing mouse in DiagramScene...")
        self.parent().sceneMouseReleaseEvent(mouseEvent)
        super(DiagramScene, self).mouseReleaseEvent(mouseEvent)

        # global selectionMode
        # global copyMode
        # global pasting


        if self.parent().pasting:
            # Dismantle group
            self.parent().clearCopyGroup()

        if self.parent().itemsSelected:
            # Dismantle selection
            self.parent().clearSelectionGroup()

        if self.parent().selectionMode:
            # self.released = True
            print("There are elements inside the selection " + str(self.hasElementsInRect()))
            if self.hasElementsInRect():
                if self.parent().groupMode:
                    g = self.createGroup()
                    groupDlg(g, self.parent(), self.elementsInRect())
                elif self.parent().multipleSelectMode:
                    self.parent().createSelectionGroup(self.elementsInRect())
                elif self.parent().copyMode:
                    self.parent().copyElements()
                else:
                    print("No recognized mode")
            else:
                self.parent().copyMode = False
                self.parent().selectionMode = False

            self.released = False
            self.pressed = False
            self.selectionRect.setVisible(False)

    def drawBackground(self, painter, rect):
        if self.parent().snapGrid:
            pen = QPen()
            pen.setWidth(2)
            pen.setCosmetic(True)
            painter.setPen(pen)

            gridSize = 50

            left = int(rect.left()) - (int(rect.left()) % gridSize)
            top = int(rect.top()) - (int(rect.top()) % gridSize)
            points = []
            for x in range(left, int(rect.height()), gridSize):
                for y in range(top, int(rect.bottom()), gridSize):
                    points.append(QPointF(x, y))

            for x in points:
                painter.drawPoint(x)
        else:
            super(DiagramScene, self).drawBackground(painter, rect)

    # def mouseMoveEvent(self, e):
    #     self.setMouseTracking(True)
    #     print("In scene")
    #     self.window().mouseMoveEvent(e)

    def keyPressEvent(self, event):
        pass
        # if event.key() == Qt.Key_A:
        #     print("Toggling mode")
        #     # global editorMode
        #     self.parent().editorMode = (self.parent().editorMode + 1) % 2
        #     self.parent().parent().sb.showMessage("Mode is " + str(self.parent().editorMode))
        #
        # if event.key() == Qt.Key_S:
        #     print("Toggling selectionMode")
        #     # global selectionMode
        #     self.parent().selectionMode = not self.parent().selectionMode



        # global copyMode
        #
        # if pasting:

    def mousePressEvent(self, event):
        # self.parent().mousePressEvent(event)
        super(DiagramScene, self).mousePressEvent(event)

        # global selectionMode
        if self.parent().selectionMode:
            self.pressed = True
            # self.selectionRect.setParentItem(self)
            if not self.released:
                self.sRstart = event.scenePos()
                self.selectionRect.setRect(self.sRstart.x(), self.sRstart.y(), event.scenePos().x() - self.sRstart.x(),
                                           event.scenePos().y() - self.sRstart.y())
                self.selectionRect.setVisible(True)

        if len(self.items(event.scenePos())) == 0:
            print("No items here!")
            for c in self.parent().connectionList:
                c.unhighlightConn()

            self.parent().alignYLineItem.setVisible(False)

            for st in self.parent().trnsysObj:
                if isinstance(st, StorageTank):
                    for hx in st.heatExchangers:
                        hx.unhighlightHx()

    def createGroup(self):
        newGroup = Group(self.sRstart.x(), self.sRstart.y(), self.sRw, self.sRh, self)

        # for o in self.parent().trnsysObj:
        #     if isinstance(o, BlockItem):
        #         print("Checking block to group")
        #         if self.isInRect(o.scenePos()):
        #             newGroup.itemList.append(o)
        #             o.setGroupName()
        #
        #     if type(o) is Connection:
        #         print("Checking connection to group")
        #         if self.isInRect(o.fromPort.scenePos()) and self.isInRect(o.toPort.scenePos()):
        #             newGroup.itemList.append(o)

        return newGroup

    def elementsInRect(self):
        res = []

        for o in self.parent().trnsysObj:
            if isinstance(o, BlockItem):
                print("Checking block to group")
                if self.isInRect(o.scenePos()):
                    res.append(o)

            if type(o) is Connection:
                print("Checking connection to group")
                if self.isInRect(o.fromPort.scenePos()) and self.isInRect(o.toPort.scenePos()):
                    res.append(o)

        return res

    def hasElementsInRect(self):
        for o in self.parent().trnsysObj:
            if isinstance(o, BlockItem):
                print("Checking block to group")
                if self.isInRect(o.scenePos()):
                    return True

            if type(o) is Connection:
                print("Checking connection to group")
                if self.isInRect(o.fromPort.scenePos()) and self.isInRect(o.toPort.scenePos()):
                    return True

        return False

    def isInRect(self, point):
        if point.x() > self.sRstart.x() and point.x() < (
                self.sRstart.x() + self.sRw) and point.y() > self.sRstart.y() and point.y() < (
                self.sRstart.y() + self.sRh):
            print("In rect")
            return True
        else:
            return False


class EditorGraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        QGraphicsView.__init__(self, scene, parent)
        # self.setMinimumSize(self.parent().horizontalLayout.height, 700)
        self.adjustSize()
        # self.setMinimumSize(1300, 700)
        self.parent().diagramScene.viewRect2.setPos(-self.width() / 2, -self.height() / 2)
        # self.parent().diagramScene.viewRect2.setPos(1300, 700)
        self.setRenderHint(QPainter.Antialiasing)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('component/name'):
            event.accept()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat('component/name'):
            event.accept()

    def dropEvent(self, event):
        if event.mimeData().hasFormat('component/name'):
            name = str(event.mimeData().data('component/name'), encoding='utf-8')
            print("name is " + name)
            if name == 'StorageTank':
                bl = StorageTank(name, name, self)
                c = ConfigStorage(bl, self)
            elif name == 'TeePiece':
                bl = TeePiece(name, name, self)
            elif name == 'TVentil':
                bl = TVentil(name, name, self)
            elif name == 'Pump':
                bl = Pump(name, name, self)
            elif name == 'Kollektor':
                bl = Collector(name, name, self)
            elif name == 'HP':
                bl = HeatPump(name, name, self)
            elif name == 'IceStorage':
                bl = IceStorage(name, name, self)
            elif name == 'Radiator':
                bl = Radiator(name, name, self)
            elif name == 'WTap':
                bl = WTap(name, name, self)
            elif name == 'WTap_main':
                bl = WTap_main(name, name, self)
            elif name == 'Connector':
                bl = Connector(name, name, self)
            # elif name == 'GenericBlock':
            #     bl = GenericBlock(name, name, self)
            else:
                bl = BlockItem(name, name, self)

            if self.parent().snapGrid:
                qp = QPoint(event.pos().x() - event.pos().x() % 150, event.pos().y() - event.pos().y() % 150)
                p1 = self.mapToScene(qp)
            else:
                p1 = self.mapToScene(event.pos())

            bl.setPos(p1)
            self.scene().addItem(bl)

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

        super(EditorGraphicsView, self).mouseReleaseEvent(mouseEvent)

    def wheelEvent(self, event):
        super(EditorGraphicsView, self).wheelEvent(event)

        if int(event.modifiers()) == 67108864:
            if event.angleDelta().y() > 0:
                self.scale(1.25, 1.25)
            else:
                self.scale(0.8, 0.8)

    def mousePressEvent(self, event):
    #     pass
        # for t in self.parent().trnsysObj:
        #     if isinstance(t, BlockItem):
        #         t.alignMode = True
        #         print("Changing alignmentmode")
        # for t in self.parent().trnsysObj:
        #     if isinstance(t, BlockItem):
        #         t.itemChange(t.ItemPositionChange, t.pos())

        super(EditorGraphicsView, self).mousePressEvent(event)

    # def drawBackground(self, painter_, rect):
    #
    #     mCellSize_w = 15
    #     mCellSize_h = 15
    #
    #     left_ = int(rect.left()) - ( int(rect.left()) % mCellSize_w)
    #     top_ = int(rect.top()) - ( int(rect.top()) % mCellSize_h)
    #
    #     # QVarLengthArray < QLineF, 100 > lines;
    #     lines = []
    #
    #     for x in range(30):
    #         for y in range(30):
    #             self.scene().addItem(QGraphicsEllipseItem(x* mCellSize_h, y * mCellSize_w, 1, 1))
    #
    #     # for x in range(left_, int(rect.right()), mCellSize_w):
    #     #     # lines.append(QGraphicsEllipseItem(x, left_, 5, 5 ))
    #     #     self.scene().addItem(QGraphicsEllipseItem(x, left_, 2, 2 ))
    #     #     # lines.append(QLineF(x, rect.top(), x, rect.bottom()))
    #     #     QGraphicsEllipseItem()
    #     # for y in range(top_, int(rect.bottom()), mCellSize_h):
    #     #     # lines.append(QGraphicsEllipseItem(top_, y, 5, 5 ))
    #     #     self.scene().addItem(QGraphicsEllipseItem(top_, y,  2, 2))
    #     #     # lines.append(QLineF(rect.left(), y, rect.right(), y))
    #
    #
    #     # pen = QtGui.QPen(QtCore.Qt.black, 1)
    #     #
    #     # pen.setStyle(Qt.DotLine)
    #     # painter_.setPen(pen)
    #     #
    #     # for i in lines:
    #     #     painter_.drawLine(i)


class DiagramEditor(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.diagramName = 'Untitled'
        self.saveAsPath = Path()
        self.idGen = IdGenerator()

        self.selectionMode = False
        self.groupMode = False
        self.copyMode = False
        self.multipleSelectedMode = False

        self.alignMode = False

        self.pasting = False
        self.itemsSelected = False

        self.editorMode = 0
        self.snapGrid = False

        self.horizontalLayout = QHBoxLayout(self)
        self.libraryBrowserView = QListView(self)
        self.libraryModel = LibraryModel(self)

        # Investigate why choosing 100 sets 2 columns
        self.libraryBrowserView.setGridSize(QSize(65, 65))
        self.libraryBrowserView.setResizeMode(QListView.Adjust)
        self.libraryModel.setColumnCount(0)

        # OLD: Library icon creation
        # pixmap = QPixmap(60, 60)
        # self.create_icon(pixmap)

        self.libItems = []
        # r_folder = "res\\"
        r_folder = "images/"

        # Investigate why file ending is not needed
        # Uncomment these to use the copied icons of polysun
        # self.libItems.append(QtGui.QStandardItem(QIcon(pixmap), r_folder + 'TWV'))
        # self.libItems.append(QtGui.QStandardItem(QIcon(pixmap), r_folder + 'Pump2'))
        # self.libItems.append(QtGui.QStandardItem(QIcon(pixmap), r_folder + 'Kollektor2'))
        # self.libItems.append(QtGui.QStandardItem(QIcon(pixmap), r_folder + 'StorageTank2'))

        self.libItems.append(QtGui.QStandardItem(QIcon(QPixmap(r_folder + 'Pump')),  'Pump'))
        self.libItems.append(QtGui.QStandardItem(QIcon(QPixmap(r_folder + 'Kollektor')),  'Kollektor'))
        self.libItems.append(QtGui.QStandardItem(QIcon(QPixmap(r_folder + 'TVentil')), 'TVentil'))
        self.libItems.append(QtGui.QStandardItem(QIcon(QPixmap(r_folder + 'StorageTank')), 'StorageTank'))

        self.libItems.append(QtGui.QStandardItem(QIcon(QPixmap(r_folder + 'Bvi')), 'Bvi'))
        self.libItems.append(QtGui.QStandardItem(QIcon(QPixmap(r_folder + 'TeePiece')), 'TeePiece'))
        self.libItems.append(QtGui.QStandardItem(QIcon(QPixmap(r_folder + 'HP')), 'HP'))
        self.libItems.append(QtGui.QStandardItem(QIcon(QPixmap(r_folder + 'IceStorage')), 'IceStorage'))
        self.libItems.append(QtGui.QStandardItem(QIcon(QPixmap(r_folder + 'WTap')), 'WTap'))
        self.libItems.append(QtGui.QStandardItem(QIcon(QPixmap(r_folder + 'WTap_main')), 'WTap_main'))
        self.libItems.append(QtGui.QStandardItem(QIcon(QPixmap(r_folder + 'Radiator')), 'Radiator'))
        self.libItems.append(QtGui.QStandardItem(QIcon(QPixmap(r_folder + 'Connector')), 'Connector'))
        # self.libItems.append(QtGui.QStandardItem(QIcon(QPixmap(r_folder + 'GenericBlock')), 'GenericBlock'))

        for i in self.libItems:
            self.libraryModel.appendRow(i)

        self.libraryBrowserView.setModel(self.libraryModel)
        self.libraryBrowserView.setViewMode(self.libraryBrowserView.IconMode)
        self.libraryBrowserView.setDragDropMode(self.libraryBrowserView.DragOnly)

        self.diagramScene = DiagramScene(self)
        self.diagramView = EditorGraphicsView(self.diagramScene, self)

        # For list view
        self.vertL = QVBoxLayout()
        self.vertL.addWidget(self.libraryBrowserView)
        self.listV = QListWidget()
        self.vertL.addWidget(self.listV)
        # self.horizontalLayout.addWidget(self.libraryBrowserView)

        self.horizontalLayout.addLayout(self.vertL)

        self.horizontalLayout.addWidget(self.diagramView)
        self.horizontalLayout.setStretchFactor(self.diagramView, 5)
        self.horizontalLayout.setStretchFactor(self.libraryBrowserView, 1)

        self.startedConnection = False
        self.tempStartPort = None
        self.tempEndPort = None
        self.connectionList = []
        self.trnsysObj = []
        self.groupList = []
        self.blockList = []

        self.defaultGroup = Group(0, 0, 100, 100, self.diagramScene)
        self.defaultGroup.setName("defaultGroup")

        self.copyGroupList = QGraphicsItemGroup()
        self.selectionGroupList = QGraphicsItemGroup()

        a = 400  # Start of upmost button y-value
        b = 50  # distance between starts of button y-values
        b_start = 75

        self.button = QPushButton(self)
        self.button.setText("Print info")
        self.button.move(b_start, a)
        self.button.setMinimumSize(120, 40)
        self.button.clicked.connect(self.button1_clicked)
        #
        # self.button2 = QPushButton(self)
        # self.button2.setText("Build Bridges")
        # self.button2.setMinimumSize(120, 40)
        # self.button2.move(b_start, a + b)
        # self.button2.clicked.connect(self.button2_clicked)
        #
        # self.button3 = QPushButton(self)
        # self.button3.setText("Export data")
        # self.button3.move(b_start, a + 2 * b)
        # self.button3.setMinimumSize(120, 40)
        # self.button3.clicked.connect(self.button3_clicked)
        #
        # self.button4 = QPushButton(self)
        # self.button4.setText("Clean up")
        # self.button4.move(b_start, a + 3 * b)
        # self.button4.setMinimumSize(120, 40)
        # self.button4.clicked.connect(self.button4_clicked)
        #
        # self.button5 = QPushButton(self)
        # self.button5.setText("BFS/dfs group")
        # self.button5.move(b_start, a + 4 * b)
        # self.button5.setMinimumSize(120, 40)
        # self.button5.clicked.connect(self.button5_clicked)
        #
        # self.button6 = QPushButton(self)
        # self.button6.setText("Delete group")
        # self.button6.move(b_start, a + 5 * b)
        # self.button6.setMinimumSize(120, 40)
        # self.button6.clicked.connect(self.button6_clicked)

        # Hardcode color scheme:
        colorsc = "red"
        linePx = 4

        if colorsc == "red":
            connLinecolor = QColor(Qt.red)
            # connLinecolor = QColor(252, 60, 60)
        elif colorsc == "blueish":
            connLinecolor = QColor(3, 124, 193)  # Blue
        elif colorsc == "darkgray":
            connLinecolor = QColor(140, 140, 140)  # Gray
        else:
            connLinecolor = QColor(196, 196, 196)  # Gray

        self.connLine = QLineF()
        self.connLineItem = QGraphicsLineItem(self.connLine)
        self.connLineItem.setPen(QtGui.QPen(connLinecolor, linePx))
        self.connLineItem.setVisible(False)
        self.diagramScene.addItem(self.connLineItem)

        self.alignYLine = QLineF()
        self.alignYLineItem = QGraphicsLineItem(self.alignYLine)
        self.alignYLineItem.setPen(QtGui.QPen(QColor(196, 249, 252), 2))
        self.alignYLineItem.setVisible(False)
        self.diagramScene.addItem(self.alignYLineItem)

        self.alignXLine = QLineF()

        # #Search related lists
        self.bfs_visitedNodes = []
        self.bfs_neighborNodes = []

    def test_func(self):
        print("In test func")

    def create_icon(self, map_icon):
        map_icon.fill()
        painter = QPainter(map_icon)
        painter.fillRect(10, 10, 40, 40, QColor(88, 233, 252))
        # painter.setBrush(Qt.red)
        painter.setBrush(QColor(252, 136, 98))
        painter.drawEllipse(36, 2, 15, 15)
        painter.setBrush(Qt.yellow)
        painter.drawEllipse(20, 20, 20, 20)
        painter.end()


    # Debug buttons
    def button1_clicked(self):
        self.dumpInformation()

    def button2_clicked(self):
        for c in self.connectionList:
            c.buildBridges()

    def button3_clicked(self):
        self.exportData()

    def button4_clicked(self):
        self.cleanUpConnections()

    def button5_clicked(self):
        self.bfs_b()

    def button6_clicked(self):
        # Remember that first bfs has to be run!
        self.delGroup()

    def bfs_b(self):
        self.bfs(self.connectionList[0].fromPort)
        # self.dfs1(self.connectionList[0].fromPort, 8, 0)
        # print(self.dfs2(self.connectionList[0].fromPort, 8, 0))


    # Connections related methods
    def startConnection(self, port):
        print("port is " + str(port))
        self.tempStartPort = port
        self.startedConnection = True
        # print("Started Connection")
        # print("tempPort is " + str(self.tempStartPort))

    def createConnection(self, startPort, endPort):
        # print("Creating connection...")
        if startPort is not endPort:
            # if len(endPort.connectionList) == 0:
            Connection(startPort, endPort, False, self)

    def sceneMouseMoveEvent(self, event):
        if self.startedConnection:
            # print("Started conn, should draw")
            tempx = self.tempStartPort.scenePos().x()
            tempy = self.tempStartPort.scenePos().y()
            posx = event.scenePos().x()
            posy = event.scenePos().y()
            # print(str(posx))
            # print(str(tempx))

            self.connLineItem.setVisible(True)
            self.connLine.setLine(tempx, tempy, posx, posy)
            self.connLineItem.setLine(self.connLine)
            self.connLineItem.setVisible(True)

    def sceneMouseReleaseEvent(self, event):
        # print("Called sceneMouseReleaseEvent with startedConnection=" + str(self.startedConnection))
        if self.startedConnection:
            releasePos = event.scenePos()
            itemsAtReleasePos = self.diagramScene.items(releasePos)
            print("items are " + str(itemsAtReleasePos))
            for it in itemsAtReleasePos:
                if type(it) is PortItem:
                    self.createConnection(self.tempStartPort, it)
                else:
                    self.startedConnection = False
                    self.connLineItem.setVisible(False)

                    # Not necessary
                    # self.tempStartPort = None

    def cleanUpConnections(self):
        for c in self.connectionList:
            c.niceConn()
        # if self.connectionList.__len__() > 0:
        #     self.connectionList[0].clearConn()

    def cleanUpLineCrosses(self):
        pass


    # Export related methods
    def setUpStorageInnerConns(self):
        for t in self.trnsysObj:
            if type(t) is StorageTank:

                for hx in t.heatExchangers:
                    if hx.sSide == 0:
                        t.connectHxs(self.findStorageCorrespPortsHx([hx.port1, hx.port2]), [hx.port1, hx.port2], t.hxInsideConnsLeft, "L")
                    elif hx.sSide == 2:
                        print("storage of hx R is " + str(t.displayName))
                        print("hx ports are" + str(hx.port1) + str(hx.port2))
                        t.connectHxs(self.findStorageCorrespPortsHx([hx.port1, hx.port2]), [hx.port1, hx.port2], t.hxInsideConnsRight, "R")
                    else:
                        print("heatExchanger has not valid sSide")

                # print("t.leftside has len " + str(len(t.leftSide)))
                # print("t.leftside is " + str(t.rightSide))
                t.connectInside(self.findStorageCorrespPorts(t.leftSide), t.insideConnLeft, "L")
                t.connectInside(self.findStorageCorrespPorts(t.rightSide), t.insideConnRight, "R")

                print("------Checking insideConns")
                print(t.hxInsideConnsLeft)
                print(t.hxInsideConnsRight)
                print(t.insideConnLeft)
                print(t.insideConnRight)

    def findStorageCorrespPorts(self, portList):
        # This function gets the ports on the other side of pipes connected to a port of the StorageTank

        res = []
        # print("Finding c ports")
        for p in portList:
            if len(p.connectionList) > 0:           # check if not >1 needed
                # connectionList[0] is the hidden connection created when the portPair is
                if p.connectionList[1].fromPort is p:
                    res.append(p.connectionList[1].toPort)
                elif p.connectionList[1].toPort is p:
                    res.append(p.connectionList[1].fromPort)
                else:
                    print("Port is not fromPort nor toPort")

        # [print(p.parent.displayName) for p in res]
        return res

    def findStorageCorrespPortsHx(self, portList):
        res = []

        for p in portList:
            # print("Port has")
            # [print(c.displayName) for c in p.connectionList]

            if len(p.connectionList) > 1:
                if p.connectionList[1].fromPort is p:
                    res.append(p.connectionList[1].toPort)
                elif p.connectionList[1].toPort is p:
                    res.append(p.connectionList[1].fromPort)
                else:
                    print("Port is not fromPort nor toPort")
            if len(p.connectionList) == 1:
                if p.connectionList[0].fromPort is p:
                    res.append(p.connectionList[0].toPort)
                elif p.connectionList[0].toPort is p:
                    res.append(p.connectionList[0].fromPort)
                else:
                    print("Port is not fromPort nor toPort")
        # print("res is " + str(res))
        return res

    def tearDownStorageInnerConns(self):
        for t in self.trnsysObj:
            if type(t) is StorageTank:

                # print("in conn left list is ")
                # [print(e.displayName) for e in t.insideConnLeft]
                # print("in conn right list is ")
                # [print(e.displayName) for e in t.insideConnRight]

                # Remove old insideConnection:
                # if len(t.insideConnLeft) > 0:
                    # print("t.insideConnection has " + str(len(t.insideConnLeft)) + "TPieces/connection")

                while len(t.insideConnLeft) > 0:
                    tp = t.insideConnLeft[0]
                    if isinstance(tp, TeePiece) or isinstance(tp, Connector):
                        if tp in self.trnsysObj:
                            t.insideConnLeft.remove(tp)
                            tp.deleteBlock()
                        else:
                            print("The virtual element not in trnsysobj is " + str(tp) + " " + tp.displayName)
                    else:
                        print("Element other than TPiece/connector found in insideConnection " + str(tp))
                t.insideConnLeft = []

                while len(t.insideConnRight) > 0:
                    tp = t.insideConnRight[0]
                    if isinstance(tp, TeePiece) or isinstance(tp, Connector):
                        if tp in self.trnsysObj:
                            t.insideConnRight.remove(tp)
                            tp.deleteBlock()
                        else:
                            print("The virtual element not in trnsysobj is " + str(tp) + " " + tp.displayName)
                    else:
                        print("Element other than TPiece/connector found in insideConnection " + str(tp))
                t.insideConnRight = []

                while len(t.hxInsideConnsLeft) > 0:
                    tp = t.hxInsideConnsLeft[0]
                    if isinstance(tp, TeePiece) or isinstance(tp, Connector):
                        if tp in self.trnsysObj:
                            t.hxInsideConnsLeft.remove(tp)
                            tp.deleteBlock()
                        else:
                            print("The virtual element not in trnsysobj is " + str(tp) + " " + tp.displayName)
                    else:
                        print("Element other than TPiece/connector found in insideConnection " + str(tp))
                t.hxInsideConnsLeft = []

                while len(t.hxInsideConnsRight) > 0:
                    tp = t.hxInsideConnsRight[0]
                    if isinstance(tp, TeePiece) or isinstance(tp, Connector):
                        if tp in self.trnsysObj:
                            t.hxInsideConnsRight.remove(tp)
                            tp.deleteBlock()
                        else:
                            print("The virtual element not in trnsysobj is " + str(tp) + " " + tp.displayName)
                    else:
                        print("Element other than TPiece/connector found in insideConnection " + str(tp))
                t.hxInsideConnsRight = []

        # self.setTrnsysIdBack()

    # def setTrnsysIdBack(self):
    #
    #     self.idGen.trnsysID = max(t.trnsysId for t in self.trnsysObj)

    def exportBlackBox(self):
        f = "*** Black box component temperatures" + "\n"
        equationNr = 0

        for t in self.trnsysObj:
            if isinstance(t, Connection):
                continue

            if not t.isVisible():
                # Virtual element
                continue

            if isinstance(t, HeatPump):
                f += "T" + t.displayName + "HeatPump" + "=1 \n"
                f += "T" + t.displayName + "Evap" + "=1 \n"
                equationNr += 2
                continue
            if isinstance(t, Pump):
                continue

            if isinstance(t, StorageTank):
                for p in t.inputs + t.outputs:
                    if p.side == 0:
                        lr = "Left"
                    else:
                        lr = "Right"
                    f += "T" + t.displayName + "Port" + lr + str(int(100*(1-(p.scenePos().y() - p.parent.scenePos().y())/p.parent.h))) + "=1\n"
                    equationNr += 1
                    continue

            if len(t.inputs + t.outputs) == 2 and not isinstance(t, Connector):
                f += "T" + t.displayName + "=1 \n"

                equationNr += 1

        f = "\nEQUATIONS " + str(equationNr) + "\n" + f + "\n"

        return f

    def exportPumpOutlets(self):
        f = "*** Pump outlet temperatures" + "\n"
        equationNr = 0
        for t in self.trnsysObj:
            if isinstance(t, Pump):
                f += "T" + t.displayName + " = " + "T" + t.outputs[0].connectionList[0].displayName + "\n"
                equationNr += 1
            elif isinstance(t, WTap) or isinstance(t, WTap_main):
                io = t.inputs + t.outputs
                f += "T" + t.displayName + " = " + "T" + io[0].connectionList[0].displayName + "\n"
                equationNr += 1

        f = "EQUATIONS " + str(equationNr) + "\n" + f + "\n"
        return f

    def exportMassFlows(self):
        f = "*** Massflowrates" + "\n"
        equationNr = 0

        for t in self.trnsysObj:
            if isinstance(t, Pump):
                f += "Mfr" + t.displayName + " = 1000" + "\n"
                equationNr += 1
            elif isinstance(t, TVentil):
                f += "xFrac" + t.displayName + " = 1" + "\n"
                equationNr += 1

        f = "EQUATIONS " + str(equationNr) + "\n" + f + "\n"

        return f

    def exportPrintConnections(self, simulationUnit, simulationType, descConnLength, parameters, lineNr):
        # If not all ports of an object are connected, less than 5 numbers will show up
        f = ""
        # print("UNIT " + str(simulationUnit) + " TYPE " + str(simulationType))
        f += "UNIT " + str(simulationUnit) + " TYPE " + str(simulationType) + "\n"
        # print("PARAMETERS " + str(parameters))
        f += "PARAMETERS " + str(parameters) + "\n"
        # print(str(lineNr))
        f += str(lineNr) + "\n"

        #exportConnsString: i/o i/o 0 0
        offset = 1
        # Dont forget to check if trnsysObj.index() is fully equivalent to global id
        for t in self.trnsysObj:
            if type(t) is StorageTank:
                # create insideConn
                # t.connectInside() # this needs to happen before going trough trnsysObj, just after clicking export
                # Then after export, clean up (delete blocks, set trnsysId to max(trnsysId in trnsysObj)
                pass

            elif type(t) is HeatPump:
                # Only print a connection for each input, not for output (A HeatPump is defined by one input on each side)
                # At creation, allocates a second trnsysId to have one for each side
                for i in range(len(t.inputs)):
                    # ConnectionList lenght should be max offset
                    temp = ""
                    for c in t.inputs[i].connectionList:
                        if type(c.fromPort.parent) is StorageTank and t.inputs[i].connectionList.index(c) == 0:
                            continue
                        elif type(c.toPort.parent) is StorageTank and t.inputs[i].connectionList.index(c) == 0:
                            continue
                        else:
                            if len(t.outputs[i].connectionList) > 0:

                                if i == 0:
                                    temp = str(c.trnsysId) + " " + str(
                                        t.outputs[i].connectionList[0].trnsysId) + " 0 0 " #+ str(t.childIds[0])
                                    temp += " " * (descConnLength - len(temp))

                                    # HeatPump will have a two liner exportConnString
                                    t.exportConnsString += temp + "\n"
                                    # print(temp + "!" + str(t.childIds[0]) + " : " + t.displayName + "HeatPump")
                                    f += temp + "!" + str(t.childIds[0]) + " : " + t.displayName + "HeatPump" + "\n"

                                elif i == 1:
                                    temp = str(c.trnsysId) + " " + str(
                                        t.outputs[i].connectionList[0].trnsysId) + " 0 0 " #+ str(t.childIds[1])
                                    temp += " " * (descConnLength - len(temp))

                                    # HeatPump will have a two liner exportConnString
                                    t.exportConnsString += temp + "\n"
                                    # print(temp + "!" + str(t.childIds[1]) + " : " + t.displayName + "Evap")
                                    f += temp + "!" + str(t.childIds[1]) + " : " + t.displayName + "Evap" + "\n"
                                else:
                                    # print("There are more inputs than trnsysIds ")
                                    f += "Error: There are more inputs than trnsysIds" + "\n"

                                # Presumably used only for storing the order of connections
                                t.trnsysConn.append(c)
                                t.trnsysConn.append(t.outputs[i].connectionList[0])

                            else:
                                # print("Output of HeatPump for input[{0}] is not connected ".format(i))
                                f += "Output of HFeatPump for input[{0}] is not connected ".format(i) + "\n"

            else:
                # No StorageTank and no HeatPump
                if isinstance(t, BlockItem):
                    temp = ""
                    for i in t.inputs:
                        # ConnectionList lenght should be max offset
                        for c in i.connectionList:
                            if type(c.fromPort.parent) is StorageTank and i.connectionList.index(c) == 0:
                                continue
                            elif type(c.toPort.parent) is StorageTank and i.connectionList.index(c) == 0:
                                continue
                            else:
                                temp = temp + str(c.trnsysId) + " "
                                t.trnsysConn.append(c)

                    for o in t.outputs:
                        # ConnectionList lenght should be max offset
                        for c in o.connectionList:
                            if type(c.fromPort.parent) is StorageTank and o.connectionList.index(c) == 0:
                                continue
                            elif type(c.toPort.parent) is StorageTank and o.connectionList.index(c) == 0:
                                continue
                            else:
                                temp = temp + str(c.trnsysId) + " "
                                t.trnsysConn.append(c)

                    # print(temp + "     " + "!" + str(t.id) + " : " + str(t.displayName))

                    if t.typeNumber != 2 and t.typeNumber != 3:
                        temp += "0 "

                    if isinstance(t, WTap_main) or isinstance(t, WTap):
                        temp += "0 "

                    temp += str(t.typeNumber)
                    # temp += " " + str(t.trnsysId)
                    temp += " " * (descConnLength - len(temp))
                    t.exportConnsString = temp
                    # print(temp + "!" + str(self.trnsysObj.index(t) + offset) + " : " + str(t.displayName))
                    # print(temp + "!" + str(t.trnsysId) + " : " + str(t.displayName))
                    f += temp + "!" + str(t.trnsysId) + " : " + str(t.displayName) + "\n"

                if type(t) is Connection:
                    # If neither port is at a StorageTank
                    # print("t is " + str(t) + " has " + str(t.fromPort.parent) + "->" + str(t.toPort.parent))
                    if type(t.fromPort.parent) is StorageTank or type(t.toPort.parent) is StorageTank:
                        continue

                    temp = str(t.fromPort.parent.trnsysId) + " " + str(t.toPort.parent.trnsysId) + " 0" * 2 + " " #+ str(t.trnsysId)
                    t.exportConnsString = temp

                    # Assert that parent is of type BlockItem
                    # print("toPort parent is " + str(t.toPort.parent) + "fromPort parent is " + str(t.fromPort.parent))
                    if isinstance(t.toPort.parent, BlockItem) and isinstance(t.fromPort.parent, BlockItem):
                        # print("----> Both parents of" + str(t) + " are blocks")
                        t.trnsysConn.append(t.fromPort.parent)
                        t.trnsysConn.append(t.toPort.parent)
                    else:
                        # print("Error: Parent of this port is not a BlockItem")
                        f += "Error: Parent of this port is not a BlockItem" + "\n"
                        return

                    # print(temp + " " * (descConnLength - len(temp)) + "!" + str(t.trnsysId) + " : " + str(t.displayName))
                    f += temp + " " * (descConnLength - len(temp)) + "!" + str(t.trnsysId) + " : " + str(t.displayName) + "\n"

                #TODO: Check if no problem with other storagetanks (very probable)

                # Very careful examination needed!
                # If at least one port is at a StorageTank
                else:
                    pass
                    # All connections are already correctly set in setUpStorageInnerConns

                    # Difficult, unclear alternative using ports on StorageTank:

                    # # If connection is inside StorageTank
                    # print("->1")
                    # if type(t.fromPort.parent) is StorageTank and type(t.toPort.parent) is StorageTank:
                    #     print("->2")
                    #
                    #     # If connection is not the first (portPair) connection:
                    #     # print(t.fromPort.connectionList)
                    #     # print(t.toPort.connectionList)
                    #     if len(t.fromPort.connectionList) > 0 and len(t.toPort.connectionList) > 0:
                    #         print("->3")
                    #
                    #         # Search for the corresponding ports outside of the StorageTank
                    #         firstPort = None
                    #         secondPort = None
                    #
                    #         # Here we assume that the outside connection of the StorageTank
                    #         # is created after the portPair connection and before the insideConn
                    #         # For two ports only, there is no connection generated in insideConn
                    #
                    #         a = 1
                    #         # if len(t.fromPort.connectionList) < 3:
                    #         #                                 #     a = 0
                    #
                    #         if t.fromPort.connectionList[a].fromPort is t.fromPort:
                    #             firstPort = t.fromPort.connectionList[a].toPort
                    #         elif t.fromPort.connectionList[a].toPort is t.fromPort:
                    #             firstPort = t.fromPort.connectionList[a].fromPort
                    #         else:
                    #             print("No firstPort set")
                    #
                    #         if t.toPort.connectionList[1].fromPort is t.toPort:
                    #             secondPort = t.fromPort.connectionList[1].toPort
                    #         elif t.toPort.connectionList[1].toPort is t.toPort:
                    #             secondPort = t.fromPort.connectionList[1].fromPort
                    #         else:
                    #             print("No secondPort set")
                    #
                    #         # print("--------> FirstPort is " + str(firstPort))
                    #         # print("--------> SecondPort is " + str(secondPort))

                        # Idea: the generated Connections should directly be made with corresp ports

        tempS = f

        t = self.convertToStringList(tempS)

        f = "\n".join(t[0:3]) + "\n" + self.correctIds(t[3:]) + "\n"

        return f

    def exportPrintInputs(self, inputNr):
        #  add a string to block and connection for exportPrintInput
        f = ''
        # print("INPUTS " + str(inputNr))
        f += "INPUTS " + str(inputNr) + "\n"

        pump_prefix = "Mfr"
        mix_prefix = "xFrac"

        temp = ""
        counter = 0

        for t in self.trnsysObj:
            if type(t) is StorageTank:
                continue
            if type(t) is Connection and (type(t.fromPort.parent) is StorageTank or type(t.toPort.parent) is StorageTank):
                continue

            # if type(t) is Connection and t.isBlockConn and not t.isStorageIO:
            #     continue
            # if isinstance(t, BlockItem) and not t.isVisible():
            #     continue

            if t.typeNumber == 1:
                temp1 = pump_prefix + t.displayName
                t.exportInputName = " " + temp1 + " " #+ "[" + t.displayName + " "
                temp += t.exportInputName
                t.exportInitialInput = 0.0

            elif t.typeNumber == 3:
                temp1 = mix_prefix + t.displayName
                t.exportInputName = " " + temp1 + " " #+ "[" + t.displayName + " "
                temp += t.exportInputName
                t.exportInitialInput = 0.0

            else:
                temp += " 0,0 " #+ "[" + t.displayName
                if type(t) is HeatPump:
                    temp += " 0,0 " #+ "[" + t.displayName
                    counter += 1

            # Used before storage and heatpump introduced changes
            # breakline = ((self.trnsysObj.index(t) + 1) % 8 == 0)
            # # breakline = ((t.trnsysId + 1) % 8 == 0)
            # if (self.trnsysObj.index(t) != (len(self.trnsysObj) - 1)) and not breakline:
            #     # if (t.trnsysId != (len(self.trnsysObj) - 1)) and not breakline:
            #     temp = temp + ", "
            #
            # if not breakline:
            #     print(temp, end='')
            # else:
            #     print(temp)

            if counter > 8 or t == self.trnsysObj[-1]:
                print(temp)
                f += temp + "\n"
                temp = ""
                counter = 0

            counter += 1

        # print("\n*** Initial Inputs *")
        f += "\n*** Initial Inputs *" + "\n"

        counter2 = 0
        for t in self.trnsysObj:
            if type(t) is StorageTank:
                continue
            if type(t) is Connection and (type(t.fromPort.parent) is StorageTank or type(t.toPort.parent) is StorageTank):
                continue
            if type(t) is HeatPump:
                # print(" " + str(t.exportInitialInput) + " " + str(t.exportInitialInput) + " ", end='')
                f += " " + str(t.exportInitialInput) + " " + str(t.exportInitialInput) + " "
                counter2 += 1
                continue
            # if type(t) is Connection and t.isBlockConn and not t.isStorageIO:
            #     continue
            # print(str(t.exportInitialInput) + " ", end='')
            f += str(t.exportInitialInput) + " "

            if counter2 == 8:
                # print("")
                f += "\n"
                counter2 = 0

            counter2 += 1

            # if (self.trnsysObj.index(t) + 1) % 8 != 0:
            #     print(str(t.exportInitialInput) + " ", end='')
            # else:
            #     print(str(t.exportInitialInput))

        # print("\n")
        f += "\n"

        return f

    def exportPrintEquations(self, simulationUnit):
        # Maybe add tuple (displayname, counting number)
        f = ''

        abc = list(string.ascii_uppercase)[0:3]

        prefix = "Mfr"
        equationNumber = 1
        tot = ""

        # counter = 1
        for t in self.trnsysObj:
            # for i in range(0, (1 + int((t.typeNumber == 2) or (t.typeNumber == 3))))
            if type(t) is StorageTank:
                continue
            if type(t) is Connection and (type(t.fromPort.parent) is StorageTank or type(t.toPort.parent) is StorageTank):
                continue
            # if type(t) is Connector:
            #     continue
            # if type(t) is Connection and t.isBlockConn and not t.isStorageIO:
            #     continue

            if type(t) is HeatPump:
                # print("----->" + str(t.exportConnsString))

                for i in range(0, 3):

                    if i < 2:
                        temp = prefix + t.displayName + "-HeatPump" + "_" + abc[i] + "=[" + str(simulationUnit) + "," +\
                               str(equationNumber) + "]\n"
                        tot += temp
                        t.exportEquations.append(temp)
                        equationNumber += 1

                for i in range(0, 3):

                    if i < 2:
                        temp = prefix + t.displayName + "_Evap" + "_" + abc[i] + "=[" + \
                               str(simulationUnit) + "," + str(equationNumber) + "]\n"
                        tot += temp
                        t.exportEquations.append(temp)
                        equationNumber += 1
                continue

            for i in range(0, 3):
                if t.typeNumber == 2 or t.typeNumber == 3:
                    temp = prefix + t.displayName + "_" + abc[i] + "=[" + str(simulationUnit) + "," + \
                           str(equationNumber) + "]\n"
                    tot += temp
                    t.exportEquations.append(temp)
                    equationNumber += 1
                else:
                    if i < 2:
                        temp = prefix + t.displayName + "_" + abc[i] + "=[" + str(simulationUnit) + "," + \
                               str(equationNumber) + "]\n"
                        tot += temp
                        t.exportEquations.append(temp)
                        equationNumber += 1

        head = "EQUATIONS {0}	!! Output up to three (A,B,C) mass flow rates of each component, positive = " \
               "input/inlet, negative = output/outlet ".format(equationNumber-1)

        # print(head)
        f += head + "\n"
        # print(tot)
        f += tot + "\n"

        # print("")
        f += "\n"

        return f

    def exportUnits(self, startingUnit):
        f = ''
        unitNumber = startingUnit
        typeNr1 = 929
        typeNr2 = 931

        for t in self.trnsysObj:

            unitText = ""
            ambientT = 20

            densityVar = "RhoWat"
            specHeatVar = "CPWat"

            equationConstant1 = 1
            equationConstant2 = 3

            # T-Pieces and Mixers
            if t.typeNumber == 2 or t.typeNumber == 3:
                unitText += "UNIT " + str(unitNumber) + " TYPE " + str(typeNr1) + "\n"
                unitText += "!" + t.displayName + "\n"
                unitText += "PARAMETERS 0\n"
                # unitText += "INPUTS " + str(2 * len(t.getConnections()))
                unitText += "INPUTS 6\n"

                for s in t.exportEquations:
                    unitText += s[0:s.find('=')] + "\n"

                for it in t.trnsysConn:
                    unitText += "T" + it.displayName + "\n"

                unitText += "***Initial values\n"
                unitText += 3 * "0 " + 3 * (str(ambientT) + " ") + "\n"

                unitText += "EQUATIONS 1\n"
                unitText += "T" + t.displayName + "= [" + str(unitNumber) + "," + str(equationConstant1) + "]\n"

                unitNumber += 1
                # print(unitText)
                f += unitText + "\n"

            # Pipes
            if type(t) is Connection and not (type(t.fromPort.parent) is StorageTank or type(t.toPort.parent) is StorageTank):
                # if t.isBlockConn and t.isStorageIO:
                if True:
                    parameterNumber = 6
                    inputNumbers = 4

                    # Fixed strings
                    diameterPrefix = "di"
                    lengthPrefix = "L"
                    lossPrefix = "U"
                    tempRoomVar = "TRoomStore"
                    initialValueS = "20 0.0 20 20"
                    powerPrefix = "P"

                    # Momentarily hardcoded
                    equationNr = 3

                    unitText += "UNIT " + str(unitNumber) + " TYPE " + str(typeNr2) + "\n"
                    unitText += "!" + t.displayName + "\n"
                    unitText += "PARAMETERS " + str(parameterNumber) + "\n"

                    unitText += diameterPrefix + t.displayName + "\n"
                    unitText += lengthPrefix + t.displayName + "\n"
                    unitText += lossPrefix + t.displayName + "\n"
                    unitText += densityVar + "\n"
                    unitText += specHeatVar + "\n"
                    unitText += str(ambientT) + "\n"

                    unitText += "INPUTS " + str(inputNumbers) + "\n"

                    if len(t.trnsysConn) == 2:
                        unitText += "T" + t.trnsysConn[0].displayName + "\n"
                        unitText += t.exportEquations[0][0:t.exportEquations[0].find("=")] + "\n"
                        unitText += tempRoomVar + "\n"
                        unitText += "T" + t.trnsysConn[1].displayName + "\n"
                    else:
                        # print("----> NO VALUE\n" * 3 + "at connection with parents " + str(t.fromPort.parent) + str(t.toPort.parent))
                        f += "Error: NO VALUE\n" * 3 + "at connection with parents " + str(t.fromPort.parent) + str(t.toPort.parent) + "\n"

                    unitText += "***Initial values\n"
                    unitText += initialValueS + "\n\n"

                    unitText += "EQUATIONS " + str(equationNr) + "\n"
                    unitText += "T" + t.displayName + "= [" + str(unitNumber) + "," + str(equationConstant1) + "]\n"
                    unitText += powerPrefix + t.displayName + "_kW" + "= [" + str(unitNumber) + "," + str(
                        equationConstant2) + "]/3600 !kW\n"
                    unitText += "Mfr" + t.displayName + "= " + "Mfr" + t.displayName + "_A" "\n"

                    unitNumber += 1
                    # print(unitText)
                    unitText += "\n"
                    f += unitText

        return f

    def exportPrintLoops(self):
        f = ''
        loopText = ''
        constsNr = 0
        constString = "CONSTANTS "
        suffix1 = "_save"
        string1 = "dtSim/rhoWat/"
        Pi = "3.14"
        for g in self.groupList:

            loopText += "** Fluid Loop : " + g.displayName + "\n"

            loopNr = self.groupList.index(g)

            diLp = "di_loop_" + str(loopNr)
            LLp = "L_loop_" + str(loopNr)
            ULp = "U_loop_" + str(loopNr)

            loopText += diLp + "=" + str(g.exportDi) + "\n"
            loopText += LLp + "=" + str(g.exportL) + "\n"
            loopText += ULp + "=" + str(g.exportU) + "\n"
            loopText += LLp + suffix1 + " = " "Mfr_" + "loop_" + str(loopNr) + "_nom*" + string1 + "((" + \
                        diLp + "/2)^2*" + Pi + ")\n"

            loopText += ULp + suffix1 + " = " + str(g.exportU) + "*" + LLp + suffix1

            constsNr += 5

            loopText += "\n"

        # print(constString + str(constsNr))
        f += constString + str(constsNr) + "\n"
        # print(loopText)
        f += loopText + "\n"

        return f

    def exportPrintPipeLoops(self):
        f = ''
        loopText = ""
        equationString = "EQUATIONS "
        equationNr = 0

        for g in self.groupList:
            loopText += "** Fluid Loop : " + g.displayName + "\n"

            loopNr = self.groupList.index(g)

            diLp = "di_loop_" + str(loopNr)
            LLp = "L_loop_" + str(loopNr)
            ULp = "U_loop_" + str(loopNr)

            loopText += "**" + diLp + "=" + str(g.exportDi) + "\n"
            loopText += "**" + LLp + "=" + str(g.exportL) + "\n"
            loopText += "**" + ULp + "=" + str(g.exportU) + "\n"

            for c in g.itemList:
                if isinstance(c, Connection) and not c.isBlockConn:
                    loopText += "*** " + c.displayName +"\n"
                    loopText += "di" + c.displayName + "=" + diLp + "\n"
                    loopText += "L" + c.displayName + "=" + LLp + "\n"
                    loopText += "U" + c.displayName + "=" + ULp + "\n"
                    equationNr += 3

            loopText += "\n"

        # print(equationString + str(equationNr))
        f += equationString + str(equationNr) + "\n"
        # print(loopText)
        f += loopText + "\n"
        return f

    def exportPrintPipeLosses(self):
        f = ''
        lossText = ''
        strVar = 'PipeLoss'

        for g in self.groupList:
            lossText += strVar + str(self.groupList.index(g)) + "="

            for i in g.itemList:
                if isinstance(i, Connection)  and not i.isBlockConn:
                    lossText += "P" + i.displayName + "_kW" + "+"

            lossText = lossText[:-1]
            lossText += "\n"

        lossText += strVar + "Total="

        for g in self.groupList:
            lossText += strVar + str(self.groupList.index(g)) + "+"

        lossText = lossText[:-1]

        # print(lossText)
        f += lossText + "\n"
        return f

    def exportEnd1(self, unitNr, typeNr):
        f = ''
        text = ''
        text += "UNIT {0} TYPE {1} \n".format(unitNr, typeNr)
        text += "PARAMETERS 10"
        text += "dtSim             ! 1 Printing interval\n"
        text += "START             ! 2 Start time\n"
        text += "STOP              ! 3 Stop time\n"
        text += "90     ! 4 Logical unit\n"
        text += "0     ! 5 Units printing mode\n"
        text += "0     ! 6 Relative or absolute start time\n"
        text += "-1     ! 7 Overwrite or Append\n"
        text += "-1     ! 8 Print header\n"
        text += "0     ! 9 Delimiter\n"
        text += "1     ! 10 Print labels\n"

        # print(text)
        f += text + "\n"
        return f

    def exportData(self):
        self.setUpStorageInnerConns()

        self.sortTrnsysObj()

        # print("Self trnsysObj" + str(self.trnsysObj))

        fullExportText = ''

        exportPath = Path(Path(__file__).resolve().parent.joinpath("exports")).joinpath(self.diagramName + '.dck')

        if Path(exportPath).exists():
            qmb = QMessageBox(self)
            qmb.setText("Warning: " +
                        "An export file exists already. Do you want to overwrite or cancel?")
            qmb.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
            qmb.setDefaultButton(QMessageBox.Cancel)
            ret = qmb.exec()
            if ret == QMessageBox.Save:
                print("Overwriting")
                # continue
            else:
                print("Canceling")
                return
        else:
            # Export file does not exist yet
            pass

        print("Printing the TRNSYS file... \n")

        header = open("res/Constants.txt", "r")
        fullExportText += header.read()
        header.close()

        print("\n")

        simulationUnit = 450
        simulationType = 935
        descConnLength = 20

        parameters = 0

        for t in self.trnsysObj:
            if type(t) is StorageTank:
                continue
            if type(t) is Connection and (type(t.fromPort.parent) is StorageTank or type(t.toPort.parent) is StorageTank):
                continue
            if type(t) is HeatPump:
                parameters += 1
            parameters += 1

        lineNrParameters = parameters
        parameters = parameters * 4 + 1

        # print("NEW export -----------------------------")
        # print(self.exportBlackBox())
        # print(self.exportPumpOutlets())
        # print(self.exportMassFlows())
        # print("New export -----------------------------")

        fullExportText += self.exportBlackBox()
        fullExportText += self.exportPumpOutlets()
        fullExportText += self.exportMassFlows()

        fullExportText += self.exportPrintConnections(simulationUnit, simulationType, descConnLength, parameters, lineNrParameters)
        fullExportText += self.exportPrintInputs(lineNrParameters)
        fullExportText += self.exportPrintEquations(simulationUnit)
        fullExportText += self.exportUnits(451)

        fullExportText += self.exportPrintLoops()
        fullExportText += self.exportPrintPipeLoops()
        fullExportText += self.exportPrintPipeLosses()

        print("------------------------> END OF EXPORT <------------------------")

        f = open(str(exportPath), 'w')
        f.truncate(0)
        f.write(fullExportText)
        f.close()

        # self.exportEnd1(139, 25)
        # self.cleanUpExportedElements()

        self.tearDownStorageInnerConns()

    def findId(self, s):
        return s[s.find("!") + 1:s.find(" ", s.find("!"))]

    def convertToStringList(self, l):
        res = []
        temp = ""
        for i in l:
            if i == "\n":
                res.append(temp)
                temp = ""
            else:
                temp += i

        return res

    def correctIds(self, lineList):
        fileCopy = lineList[:]
        print("fds" + str(fileCopy))
        fileCopy = [" " + l for l in fileCopy]

        counter = 0
        for line in lineList:
            counter += 1
            k = self.findId(line)
            if k != str(counter):
                fileCopy = [l.replace(" " + str(k) + " ", " " + str(counter) + " ") for l in fileCopy]
                fileCopy = [l.replace("!" + str(k) + " ", "!" + str(counter) + " ") for l in fileCopy]

        fileCopy = [l[1:None] for l in fileCopy]
        return '\n'.join(fileCopy)


    def cleanUpExportedElements(self):
        for t in self.trnsysObj:
            if isinstance(t, BlockItem):
                t.exportConnsString = ""
                t.exportInputName = "0"
                t.exportInitialInput = -1
                t.exportEquations = []
                t.trnsysConn = []

            if type(t) is Connection:
                t.exportConnsString = ""
                t.exportInputName = "0"
                t.exportInitialInput = -1
                t.exportEquations = []
                t.trnsysConn = []

    def setName(self, newName):
        self.diagramName = newName

    def propertiesDlg(self):
        diagramDlg(self)

    def delGroup(self):
        # This is used for deleting the first connected componts group found by BFS
        for bl in self.blockList:
            bl.deleteBlock()

    def delBlocks(self):
        # Delete the whole diagram
        while len(self.trnsysObj) > 0:
            # print(self.trnsysObj)
            # if isinstance(bl, BlockItem):
            print("In deleting...")
            self.trnsysObj[0].deleteBlock()

        while len(self.groupList) > 1:
            self.groupList[-1].deleteGroup()


        print("Groups are " + str(self.groupList))

    def dumpInformation(self):
        print("\n\nHello, this is a dump of the diagram information.\n")
        print("Mode is " + str(self.editorMode) + "\n")

        print("TrnsysObjects are:")
        for t in self.trnsysObj:
            print(str(t))
        print("")

        print("DiagramScene items are:")
        sItems = self.diagramScene.items()
        for it in sItems:
            print(str(it))
        print("")

        for c in self.connectionList:
            c.printConn()
        print("")

    # Graph searach related methods
    def bfs(self, startPort):
        self.bfs_neighborNodes.append(startPort)
        self.bfs_visitedNodes.append(startPort)
        self.blockList.append(startPort.parent)

        node = None

        # for j in range(3):
        while len(self.bfs_neighborNodes) > 0:
            node = self.bfs_neighborNodes.pop(0)

            # conns = node.parent.getConnections()
            for i in node.parent.getConnections():

                print("Parent has connections " + str(node.
                                                      parent.getConnections()))

                # Looking at nodes of current block
                if i.toPort.parent is node.parent and i.toPort is not node:
                    if i.toPort not in self.bfs_visitedNodes:
                        self.bfs_neighborNodes.append(i.toPort)
                        self.bfs_visitedNodes.append(i.toPort)
                        print("Adding toPort " + str(i.toPort))
                        if i.toPort.parent not in self.blockList:
                            self.blockList.append(i.toPort.parent)

                # Looking at nodes of current block
                if i.fromPort.parent is node.parent and i.fromPort is not node:
                    if i.fromPort not in self.bfs_visitedNodes:
                        self.bfs_neighborNodes.append(i.fromPort)
                        self.bfs_visitedNodes.append(i.fromPort)
                        print("Adding fromPort " + str(i.toPort))
                        if i.fromPort.parent not in self.blockList:
                            self.blockList.append(i.fromPort.parent)

                # Looking at connection of node itself
                if i.toPort == node and i.fromPort not in self.bfs_visitedNodes:
                    self.bfs_neighborNodes.append(i.fromPort)
                    self.bfs_visitedNodes.append(i.fromPort)
                    print("Adding fromPort " + str(i.fromPort))
                    if i.fromPort.parent not in self.blockList:
                        self.blockList.append(i.fromPort.parent)

                # Looking at connection of node itself
                if i.fromPort == node and i.toPort not in self.bfs_visitedNodes:
                    self.bfs_neighborNodes.append(i.toPort)
                    self.bfs_visitedNodes.append(i.toPort)
                    print("Adding toPort " + str(i.toPort))
                    if i.toPort.parent not in self.blockList:
                        self.blockList.append(i.toPort.parent)

        print("Blocklist " + str(self.blockList) + "\n")

    def dfs(self, port, maxdepth, d):
        print("At port " + str(port))

        # if port.visited:
        #     print("Found a cycle")
        #
        # if port == self.connectionList[0].fromPort:
        #     print("Found a cycle")

        # Return condition
        if d == maxdepth or port.visited:
            print("Returning at port " + str(port) + ", " + str(port.parent))
            return

        port.visited = True

        # Recursion
        # Algorithm:
        # Go through all connections port has, then through all connections the other ports of own block has

        conns = port.parent.getConnections()
        connsP = []
        connsOthers = []

        for c1 in conns:
            if c1 in port.connectionList:
                connsP.append(c1)
            else:
                connsOthers.append(c1)

        # Assertion
        # print("Sum of elements is " + str(len(connsP) + len(connsOthers)))

        for c in connsP:
            if c.fromPort is port and not c.toPort.visited:
                self.dfs(c.toPort, maxdepth, d + 1)
            if c.toPort is port and not c.fromPort.visited:
                self.dfs(c.fromPort, maxdepth, d + 1)

        for c in connsOthers:
            if c.fromPort.parent is port.parent:
                if not c.fromPort.visited:
                    self.dfs(c.fromPort, maxdepth, d)

            if c.toPort.parent is port.parent:
                if not c.toPort.visited:
                    self.dfs(c.toPort, maxdepth, d)

            # for c in connsOthers:
            #
            #     if c.fromPort.parent is port.parent:
            #
            #         if c.fromPort is port:
            #             for c2 in port.connectionList:
            #                 if c2.fromPort is port and not c2.toPort.visited:
            #                     self.dfs(c2.toPort, maxdepth, d + 1)
            #                 if c2.toPort is port and not c2.fromPort.visited:
            #                     self.dfs(c2.fromPort, maxdepth, d + 1)
            #         else:
            #             if not c.toPort.visited:
            #                 self.dfs(c.toPort, maxdepth, d + 1)
            #
            #     if c.toPort.parent is port.parent:
            #         if c.toPort is port:
            #             for c2 in port.connectionList:
            #                 if c2.fromPort is port and not c2.toPort.visited:
            #                     self.dfs(c2.toPort, maxdepth, d + 1)
            #                 if c2.toPort is port and not c2.fromPort.visited:
            #                     self.dfs(c2.fromPort, maxdepth, d + 1)
            #         else:
            #             if not c.fromPort.visited:
            #                 self.dfs(c.fromPort, maxdepth, d + 1)

    def dfs1(self, port, maxdepth, d):
        print("At port " + str(port))

        # Return condition
        if d == maxdepth:
            print("Returning at port " + str(port) + ", " + str(port.parent))
            return

        port.color = 'gray'

        # Recursion
        # Algorithm:
        # Go through all connections port has, then through all connections the other ports of own block has

        conns = port.parent.getConnections()
        connsP = []
        connsOthers = []

        for c1 in conns:
            if not c1.traversed:
                if c1 in port.connectionList:
                    connsP.append(c1)
                else:
                    connsOthers.append(c1)

        # print("conns are now " + str(connsP))
        # print("conns are now " + str(connsOthers))

        # Assertion
        # print("Sum of elements is " + str(len(connsP) + len(connsOthers)))

        for c in connsP:

            if c.fromPort is port:
                if c.toPort.color == 'white':
                    c.traversed = True
                    self.dfs1(c.toPort, maxdepth, d + 1)
                if c.toPort.color == 'gray':
                    print("Found a loop, says port " + str(port))

            if c.toPort is port:
                if c.fromPort.color == 'white':
                    c.traversed = True
                    self.dfs1(c.fromPort, maxdepth, d + 1)
                if c.fromPort.color == 'gray':
                    print("Found a loop, says port " + str(port))

        port.color = 'black'

        # for c in connsOthers:
        #     if c.fromPort.parent is port.parent:
        #         if c.fromPort.color == 'white':
        #             self.dfs1(c.fromPort, maxdepth, d)
        #         if c.fromPort.color == 'gray':
        #             print("Found a loop returning to ")
        #
        #     if c.toPort.parent is port.parent:
        #         if c.toPort.color == 'white':
        #             self.dfs1(c.toPort, maxdepth, d)
        #         if c.toPort.color == 'gray':
        #             print("Found a loop returning to ")

        for op in (port.parent.inputs + port.parent.outputs):
            if op.color == 'white' and len(op.connectionList) > 0:
                self.dfs1(op, maxdepth, d)
            if op.color == 'gray':
                print("Found a loop in other")

    def dfs2(self, port, maxdepth, d):
        print("At port " + str(port))

        # Return condition
        if d == maxdepth:
            print("Returning at port " + str(port) + ", " + str(port.parent))
            return

        port.color = 'gray'

        conns = port.parent.getConnections()
        connsP = []
        connsOthers = []

        for c1 in conns:
            if not c1.traversed:
                if c1 in port.connectionList:
                    connsP.append(c1)
                else:
                    connsOthers.append(c1)

        # print("conns are now " + str(connsP))
        # print("conns are now " + str(connsOthers))

        # Assertion
        # print("Sum of elements is " + str(len(connsP) + len(connsOthers)))

        for c in connsP:

            if c.fromPort is port:
                if c.toPort.color == 'white':
                    c.traversed = True
                    rlist = self.dfs2(c.toPort, maxdepth, d + 1)
                    if rlist is not None:
                        return rlist.append(port)
                    else:
                        rlist = []
                        return rlist.append(port)
                if c.toPort.color == 'gray':
                    print("Found a loop, says port " + str(port))
                    rlist = []
                    return rlist.append(port)

            if c.toPort is port:
                if c.fromPort.color == 'white':
                    c.traversed = True
                    rlist = self.dfs2(c.fromPort, maxdepth, d + 1)
                    if rlist is not None:
                        return rlist.append(port)
                    else:
                        rlist = []
                        return rlist.append(port)
                if c.fromPort.color == 'gray':
                    print("Found a loop, says port " + str(port))
                    rlist = []
                    return rlist.append(port)
        port.color = 'black'

        for op in (port.parent.inputs + port.parent.outputs):
            if op.color == 'white' and len(op.connectionList) > 0:
                rlist = self.dfs2(op, maxdepth, d)
                if rlist is not None:
                    return rlist.append(port)
                else:
                    rlist = []
                    return rlist.append(port)
                return rlist.append(self)
            if op.color == 'gray':
                print("Found a loop in other")
                rlist = []
                return rlist.append(self)

    # Save and load related methods
    # def encode_complex(z):
    #     if isinstance(z, complex):
    #         return (z.real, z.imag)
    #     else:
    #         type_name = z.__class__.__name__
    #         raise TypeError("Object of type '{type_name}' is not JSON serializable")
    #
    # def decode_complex(dct):
    #     if "__complex__" in dct:
    #         return complex(dct["real"], dct["imag"])
    #     return dct
    #
    # # def encode_Block(self, bl):
    # #     if isinstance(bl, BlockItem):
    # #         return {"__Block__": True,
    # #                 "Name": bl.name,
    # #                 "dispName": bl.displayName,
    # #                 "Position": bl.pos(),
    # #                 "GroupName": bl.groupName,
    # #                 "ID": bl.id}
    # #     else:
    # #         print("bl is " + str(type(bl)))
    # #         type_name = bl.__class__.__name__
    # #         raise TypeError("Object of type '{}' is not JSON serializable".format(type_name))
    #
    # # def decode_Connection(self, dct, blockList):
    # #     if "__Connection__" in dct:
    # #         fP = None
    # #         tP = None
    # #         blocks = blockList
    # #         for b in blocks:
    # #             for p in b.inputs + b.outputs:
    # #                 if p.id == dct["ID1"]:
    # #                     print("Found a port ")
    # #                     fP = p
    # #                 if p.id == dct["ID2"]:
    # #                     print("Found a port ")
    # #                     tP = p
    # #
    # #         return Connection(fP, tP, dct["isBl"], self)
    # #     return dct
    #
    # def decode_Block(self, dct):
    #     if "__Block__" in dct:
    #         bl = BlockItem(dct["Name"], dct["displayName"], self)
    #         bl.setPos(dct["Position"])
    #         bl.setId(dct["ID"])
    #         # bl.setId(dct["GroupName"])
    #         return bl
    #     return dct

    def encode(self, filename, encodeList):
        with open(filename, 'w') as jsonfile:
            json.dump(encodeList, jsonfile, indent=4, sort_keys=True, cls=DiagramEncoder)

    def encodeDiagram(self, filename):
        print("filename is at encoder" + str(filename))
        # if filename != "":
        with open(filename, 'w') as jsonfile:
            json.dump(self, jsonfile, indent=4, sort_keys=True, cls=DiagramEncoder)

    def decodeDiagram(self, filename):
        # filename = 'jsonOut.json'

        with open(filename, 'r') as jsonfile:
            blocklist = json.load(jsonfile, cls=DiagramDecoder, editor=self)  # Working
            # blocklist = json.load(jsonfile, object_hook=as_diagram)   # not Working

        print(" I got to the printer" + str(blocklist))

        if len(self.groupList) == 0:
            print("self.group is empty, adding default group")
            self.defaultGroup = Group(0, 0, 100, 100, self.diagramScene)
            self.defaultGroup.setName("defaultGroup")

        for j in blocklist["Blocks"]:
            # print("J is " + str(j))

            for k in j:
                if isinstance(k, BlockItem):
                    k.setParent(self.diagramView)
                    k.changeSize()
                    self.diagramScene.addItem(k)
                    print("self grouplist is " + str(self.groupList))
                    # k.setBlockToGroup("defaultGroup")

                if isinstance(k, StorageTank):
                    print("Loading a Storage")
                    k.setParent(self.diagramView)
                    k.updateImage()
                    # k.setBlockToGroup("defaultGroup")

                    print("dddd is " + k.displayName)
                    for hx in k.heatExchangers:
                        hx.initLoad()

                    # print("Printing storage tank" + str(k))

                if isinstance(k, Connection):
                    print("Almost done with loading a connection")
                    # print("Connection displ name " + str(k.displayName))
                    # print("Connection fromPort" + str(k.fromPort))
                    # print("Connection toPort" + str(k.toPort))
                    k.initLoad()
                    # k.setConnToGroup("defaultGroup")

                if isinstance(k, dict):
                    if "__idDct__" in k:
                        # here we don't set the ids because the copyGroup would need access to idGen
                        print("Found the id dict while loading, not setting the ids")
                        # global globalID
                        # global trnsysID
                        # global globalConnID

                        # self.idGen.setID(k["GlobalId"])
                        # self.idGen.setTrnsysID(k["trnsysID"])
                        # self.idGen.setConnID(k["globalConnID"])

                        # self.idGen.getID()
                        # self.idGen.getTrnsysID()
                        # self.idGen.getConnID()
                        # self.idGen.getBlockID()

                        # print("Global id is " + str(globalID))
                        # print("trnsys id is " + str(trnsysID))
                    if "__nameDct__" in k:
                        print("Found the name dict while loading")
                        self.diagramName = k["DiagramName"]

        for t in self.trnsysObj:
            print("Tr obj is" + str(t) + " " + str(t.trnsysId))

        # tempList = []
        # for t in self.trnsysObj:

    # Own, primitiv insertion sort, unused
    def insertionSort(self):
        print("Len of trnsyObj before sort is " + str(len(self.trnsysObj)))
        print("List is " + str(self.trnsysObj))

        # for s in self.trnsysObj:
        #     print("before, s has tr id " + str(s.trnsysId))

        newTrnsysList = []
        newTrnsysList.append(self.trnsysObj.pop(0))

        for t in self.trnsysObj:
            for n in newTrnsysList:
                if n.trnsysId > t.trnsysId:
                    # print("Found a larger id, inserting")
                    newTrnsysList.insert(newTrnsysList.index(n), t)
                    break
            if t.trnsysId > newTrnsysList[-1].trnsysId:
                newTrnsysList.append(t)

        self.trnsysObj = newTrnsysList

        print("Len of trnsyObj after sort is " + str(len(self.trnsysObj)))
        # print("List is now " + str(self.trnsysObj))
        # for s in self.trnsysObj:
        #     print("s has tr id " + str(s.trnsysId))

        # self.sortTrnsysObj()


    def sortTrnsysObj(self):
        res = self.trnsysObj.sort(key=self.sortId)
        for s in self.trnsysObj:
            print("s has tr id " + str(s.trnsysId) + " has dname " + s.displayName)

    def sortId(self, l1):
        return l1.trnsysId

    def copyElements(self):
        clipboardGroup = copyGroup()
        print(self.diagramScene.elementsInRect())

        for t in self.diagramScene.elementsInRect():
            print("element in rect is" + str(t))
            clipboardGroup.trnsysObj.append(t)

        self.saveToClipBoard(clipboardGroup)

    def saveToClipBoard(self, copyList):
        filename = 'clipboard.json'

        with open(filename, 'w') as jsonfile:
            json.dump(copyList, jsonfile, indent=4, sort_keys=True, cls=DiagramEncoder)

    def pasteFromClipBoard(self):
        filename = 'clipboard.json'

        with open(filename, 'r') as jsonfile:
            blocklist = json.load(jsonfile, cls=DiagramDecoderPaste, editor=self)

        for j in blocklist["Blocks"]:
            # print("J is " + str(j))

            for k in j:
                if isinstance(k, BlockItem):
                    # k.setParent(self.diagramView)
                    k.changeSize()
                    self.copyGroupList.addToGroup(k)

                    for inp in k.inputs:
                        inp.id = self.idGen.getID()
                    for out in k.outputs:
                        out.id = self.idGen.getID()

                    # copyGroupList.trnsysObj.append(k)
                    # self.diagramScene.addItem(k)

                if isinstance(k, StorageTank):
                    print("Loading a Storage")
                    # k.setParent(self.diagramView)
                    k.updateImage()

                    for hx in k.heatExchangers:
                        hx.initLoad()

                    # print("Printing storage tank" + str(k))

                if isinstance(k, Connection):
                    print("Almost done with loading a connection")
                    k.initLoad()
                    for corners in k.getCorners():
                        # copyGroupList.trnsysObj.append(k)
                        self.copyGroupList.addToGroup(corners)

                if isinstance(k, dict):
                    pass

                    # print("Global id is " + str(globalID))
                    # print("trnsys id is " + str(trnsysID))

        # global copyMode
        # global selectionMode
        # global pasting

        self.copyMode = False
        self.selectionMode = False

        self.diagramScene.addItem(self.copyGroupList)
        self.copyGroupList.setFlags(self.copyGroupList.ItemIsMovable)

        self.pasting = True

        # for t in self.trnsysObj:
        #     print("Tr obj is" + str(t) + " " + str(t.trnsysId))

    def clearCopyGroup(self):

        for it in self.copyGroupList.childItems():
            self.copyGroupList.removeFromGroup(it)

        self.pasting = False

    def createSelectionGroup(self, selectionList):
        for t in selectionList:
            if isinstance(t, BlockItem):
                self.selectionGroupList.addToGroup(t)

        self.multipleSelectedMode = False
        self.selectionMode = False

        self.diagramScene.addItem(self.selectionGroupList)
        self.selectionGroupList.setFlags(self.selectionGroupList.ItemIsMovable)

        self.itemsSelected = True

    def clearSelectionGroup(self):
        for it in self.selectionGroupList.childItems():
            self.selectionGroupList.removeFromGroup(it)

        self.itemsSelected = False

    def newDiagram(self):
        self.centralWidget.delBlocks()

        # global id
        # global trnsysID
        # global globalConnID

        # self.id = 0
        # self.trnsysID = 0
        # self.globalConnID = 0

        self.idGen.reset()
        newDiagramDlg(self)

    # Behavior:
    # If saveas has not been used, diagram will be saved in /diagrams
    # if saveas has been used, diagram will be saved in self.saveAsPath

    def save(self):
        print("saveaspath is " + str(self.saveAsPath))
        if self.saveAsPath.name == '':

            filepath = Path(Path(__file__).resolve().parent.joinpath("diagrams"))

            if Path(filepath.joinpath(self.diagramName + '.json')).exists():
                qmb = QMessageBox(self)
                qmb.setText("Warning: " +
                            "This diagram name exists already. Do you want to overwrite or cancel?")
                qmb.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
                qmb.setDefaultButton(QMessageBox.Cancel)
                ret = qmb.exec()
                if ret == QMessageBox.Save:
                    print("Overwriting")
                    self.encodeDiagram(str(filepath.joinpath(self.diagramName + '.json')))
                    msgb = QMessageBox(self)
                    msgb.setText("Saved diagram at /trnsysGUI/diagrams/")
                    msgb.exec()

                else:
                    print("Canceling")
            else:
                self.encodeDiagram(str(filepath.joinpath(self.diagramName + '.json')))
                msgb = QMessageBox(self)
                msgb.setText("Saved diagram at /trnsysGUI/diagrams/")
                msgb.exec()
        else:
            if self.saveAsPath.exists():
                pass
            else:
                self.encodeDiagram(str(self.saveAsPath))
                msgb = QMessageBox(self)
                msgb.setText("Saved diagram at" + str(self.saveAsPath))
                msgb.exec()


        # print(glob.glob("*.json"))

        # filesInDir = glob.glob()
        # if filename in filesInDir:
        #     QMessageBox(self, "Warning", "This diagram name exists already. Please rename this diagram")
        # else:

    def saveAs(self):
        self.saveAsPath = Path(QFileDialog.getSaveFileName(self, "Save diagram", filter="*.json")[0])
        self.diagramName = self.saveAsPath.stem
        # print(self.saveAsPath)
        # print(self.diagramName)

        self.encodeDiagram(str(self.saveAsPath))

    def renameDiagram(self, newName):

        if self.saveAsPath.name != '':
            # print("Path name is " + self.saveAsPath.name)
            if newName + ".json" in self.saveAsPath.glob("*"):
                QMessageBox(self, "Warning", "This diagram name exists already in the directory."
                                             " Please rename this diagram")
            else:
                self.saveAsPath = Path(self.saveAsPath.stem[0:self.saveAsPath.name.index(self.diagramName)] + newName)

        self.diagramName = newName

        # print("Path is now: " + str(self.saveAsPath))
        # print("Diagram name is: " + self.diagramName)

    def editGroups(self):
        groupsEditor(self)

    def setConnLabelVis(self, b):
        for c in self.connectionList:
            c.showLabel(b)

    def findGroupByName(self, name):
        for g in self.groupList:
            if g.displayName == name:
                return g

        return None

    # def mouseMoveEvent(self, e):
    #     print("In editor")
    #     self.parent().mouseMoveEvent(e)


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.centralWidget = DiagramEditor(self)
        self.setCentralWidget(self.centralWidget)
        self.labelVisState = False

        saveDiaAction = QAction(QIcon('images/inbox.png'), "Save system diagram", self)
        saveDiaAction.triggered.connect(self.saveDia)
        loadDiaAction = QAction(QIcon('images/outbox.png'), "Load system diagram", self)
        loadDiaAction.triggered.connect(self.loadDia)
        exportTrnsysAction = QAction(QIcon('images/font-file.png'), "Export trnsys file", self)
        exportTrnsysAction.triggered.connect(self.exportTrnsys)
        renameDiaAction = QAction(QIcon('images/text-label.png'), "Rename system diagram", self)
        renameDiaAction.triggered.connect(self.renameDia)
        deleteDiaAction = QAction(QIcon('images/trash.png'), "Delete system diagram", self)
        deleteDiaAction.triggered.connect(self.deleteDia)

        groupNewAction = QAction(QIcon('images/add-square.png'), "Create Group", self)
        groupNewAction.triggered.connect(self.createGroup)

        autoArrangeAction = QAction(QIcon('images/site-map.png'), "Tidy up connections", self)
        autoArrangeAction.triggered.connect(self.tidyUp)

        zoomInAction = QAction(QIcon('images/zoom-in.png'), "Zoom in", self)
        zoomInAction.triggered.connect(self.setZoomIn)
        zoomOutAction = QAction(QIcon('images/zoom-Out.png'), "Zoom Out", self)
        zoomOutAction.triggered.connect(self.setZoomOut)
        zoom0Action = QAction(QIcon('images/zoom-0.png'), "Reset zoom", self)
        zoom0Action.triggered.connect(self.setZoom0)

        copyAction = QAction(QIcon('images/clipboard.png'), "Copy to clipboard", self)
        copyAction.triggered.connect(self.copySelection)
        copyAction.setShortcut("c")

        pasteAction = QAction(QIcon('images/puzzle-piece.png'), "Paste from clipboard", self)
        pasteAction.triggered.connect(self.pasteSelection)
        pasteAction.setShortcut("v")

        toggleConnLabels = QAction(QIcon('images/labelToggle.png'), "Toggle pipe labels", self)
        toggleConnLabels.triggered.connect(self.toggleConnLabels)

        editGroupsAction = QAction(QIcon('images/modal-list.png'), "Edit groups/loops", self)
        editGroupsAction.triggered.connect(self.editGroups)

        selectMultipleAction = QAction(QIcon('images/elastic.png'), "Select multiple items", self)
        selectMultipleAction.triggered.connect(self.createSelection)
        selectMultipleAction.setShortcut("s")

        multipleDeleteAction = QAction("Delete selection", self)
        multipleDeleteAction.triggered.connect(self.deleteMultiple)
        multipleDeleteAction.setShortcut("Ctrl+d")

        toggleEditorModeAction = QAction("Toggle editor mode", self)
        toggleEditorModeAction.triggered.connect(self.toggleEditorMode)
        toggleEditorModeAction.setShortcut("m")

        toggleSnapAction = QAction("Toggle snap grid", self)
        toggleSnapAction.triggered.connect(self.toggleSnap)
        toggleSnapAction.setShortcut("a")

        toggleAlignModeAction = QAction("Toggle align mode", self)
        toggleAlignModeAction.triggered.connect(self.toggleAlignMode)
        toggleAlignModeAction.setShortcut("q")
        trnsysList = QAction(QIcon('images/bug-1.png'), "Print trnsysObj", self)
        trnsysList.triggered.connect(self.mb_debug)

        self.mb = self.menuBar()
        self.fileMenu = QMenu("File")

        fileMenuNewAction = QAction("New", self)
        fileMenuNewAction.triggered.connect(self.newDia)
        self.fileMenu.addAction(fileMenuNewAction)

        fileMenuOpenAction = QAction("Open", self)

        fileMenuOpenAction.triggered.connect(self.openFile)
        fileMenuOpenAction.setShortcut("Ctrl+o")
        self.fileMenu.addAction(fileMenuOpenAction)

        fileMenuSaveAction = QAction("Save", self)
        fileMenuSaveAction.triggered.connect(self.saveDia)
        fileMenuSaveAction.setShortcut("Ctrl+s")
        self.fileMenu.addAction(fileMenuSaveAction)

        fileMenuSaveAsAction = QAction("Save as", self)
        fileMenuSaveAsAction.triggered.connect(self.saveDiaAs)
        self.fileMenu.addAction(fileMenuSaveAsAction)

        self.mb.addMenu(self.fileMenu)

        self.s1Menu = QMenu("Edit")
        self.s1Menu.addAction(toggleEditorModeAction)
        self.s1Menu.addAction(multipleDeleteAction)
        self.s1Menu.addAction(toggleSnapAction)
        self.s1Menu.addAction(toggleAlignModeAction)
        self.s1Menu.addAction("Place4")
        self.s1Menu.addAction("Place5")

        self.mb.addMenu(self.s1Menu)
        self.mb.addMenu("Help")
        self.mb.addSeparator()

        selectTb = self.addToolBar('Create group...')
        selectTb.setObjectName('CreateGroupTb')

        selectTb.addAction(saveDiaAction)
        selectTb.addAction(loadDiaAction)
        selectTb.addAction(exportTrnsysAction)
        selectTb.addAction(renameDiaAction)
        selectTb.addAction(deleteDiaAction)
        selectTb.addAction(groupNewAction)
        selectTb.addAction(autoArrangeAction)
        selectTb.addAction(zoomInAction)
        selectTb.addAction(zoomOutAction)
        selectTb.addAction(zoom0Action)
        selectTb.addAction(copyAction)
        selectTb.addAction(pasteAction)
        selectTb.addAction(toggleConnLabels)
        selectTb.addAction(editGroupsAction)
        selectTb.addAction(selectMultipleAction)
        selectTb.addAction(trnsysList)

        self.sb = self.statusBar()
        # sb.setToolTip("hi")
        self.sb.showMessage("Mode is " + str(self.centralWidget.editorMode))

    def newDia(self):
        print("Creating new diagram")
        # self.centralWidget.newDiagram()
        self.centralWidget.delBlocks()
        del self.centralWidget

        self.centralWidget = DiagramEditor()
        self.setCentralWidget(self.centralWidget)

    def saveDia(self):
        print("Saving diagram")
        # self.centralWidget.encodeDiagram()
        # filepath = Path(__file__).parent.joinpath("jsonOut.json")
        # self.centralWidget.save(str(filepath))
        self.centralWidget.save()

    def saveDiaAs(self):
        print("Saving diagram as...")
        self.centralWidget.saveAs()

    def loadDia(self):
        print("Loading diagram")
        # Maybe delete all elements before loading?
        # self.centralWidget.delBlocks()
        # filepath = Path(__file__).parent.joinpath("diagrams").joinpath("jsonOut.json")
        # self.centralWidget.decodeDiagram(str(filepath))

        self.openFile()

    def exportTrnsys(self):
        print("Exporting Trnsys file...")
        self.centralWidget.exportData()

    def renameDia(self):
        print("Renaming diagram...")
        self.centralWidget.propertiesDlg()

    def deleteDia(self):
        print("Deleting diagram")
        self.centralWidget.delBlocks()
        msgb = QMessageBox(self)
        msgb.setText("Deleted diagram" + str(self.centralWidget.saveAsPath) + "[" + str(len(self.centralWidget.trnsysObj)) + "]")
        msgb.exec()

    def createGroup(self):
        # print("Tb createGroup pressed")
        # global selectionMode
        self.centralWidget.selectionMode = True
        self.centralWidget.groupMode = True
        self.centralWidget.copyMode = False
        self.centralWidget.multipleSelectMode = False

    def tidyUp(self):
        print("Tidying up...")
        self.centralWidget.cleanUpConnections()

    def setZoomIn(self):
        print("Setting zoom in")
        self.centralWidget.diagramView.scale(1.2, 1.2)

    def setZoomOut(self):
        print("Setting zoom out")
        self.centralWidget.diagramView.scale(0.8, 0.8)

    def setZoom0(self):
        print("Setting zoom 0")
        self.centralWidget.diagramView.resetTransform()

    def copySelection(self):
        print("Copying selection")
        # global selectionMode
        # global copyMode

        self.centralWidget.selectionMode = True
        self.centralWidget.copyMode = True
        self.centralWidget.groupMode = False
        self.centralWidget.multipleSelectMode = False

    def pasteSelection(self):
        print("Pasting selection")
        self.centralWidget.pasteFromClipBoard()
        # global copyMode
        self.centralWidget.copyMode = False

    def editGroups(self):
        self.centralWidget.editGroups()

    def mb_debug(self):
        # print(self.centralWidget.trnsysObj)
        a = [int(s.id) for s in self.centralWidget.trnsysObj]
        a.sort()
        print(a)

        for s in self.centralWidget.trnsysObj:
            if s.id == 11:
                print("Duplicate id obj is " + str(s.displayName) + " " + str(s.id))

        for t in self.centralWidget.trnsysObj:
            t.alignMode = True
            print(t.alignMode)


    def openFile(self):
        print("Opening diagram")
        self.centralWidget.delBlocks()
        fileName = QFileDialog.getOpenFileName(self, "Open diagram", filter="*.json")[0]
        print(fileName)
        if fileName != '':
            self.centralWidget.decodeDiagram(fileName)
        else:
            print("No filename chosen")

    def toggleConnLabels(self):
        self.labelVisState = not self.labelVisState
        self.centralWidget.setConnLabelVis(self.labelVisState)

    def toggleEditorMode(self):
        print("Toggling editor mode")
        self.centralWidget.editorMode = (self.centralWidget.editorMode + 1) % 2
        self.sb.showMessage("Mode is " + str(self.centralWidget.editorMode))

    def toggleAlignMode(self):
        print("Toggling alignMode")
        self.centralWidget.alignMode = not self.centralWidget.alignMode

    def toggleSnap(self):
        self.centralWidget.snapGrid = not self.centralWidget.snapGrid
        self.centralWidget.diagramScene.update()

    def createSelection(self):
        self.centralWidget.clearSelectionGroup()
        self.centralWidget.selectionMode = True
        self.centralWidget.copyMode = False
        self.centralWidget.groupMode = False
        self.centralWidget.multipleSelectMode = True

    def deleteMultiple(self):
        # print("pressed del")
        temp = []
        print(self.centralWidget.selectionGroupList.childItems())

        for t in self.centralWidget.selectionGroupList.childItems():
            temp.append(t)
            self.centralWidget.selectionGroupList.removeFromGroup(t)

        for t in temp:
            if isinstance(t, BlockItem):
                t.deleteBlock()
            elif isinstance(t, Connection):
                t.deleteConn()
            else:
                print("Neiter a Block nor Connection in copyGroupList ")


    def mouseMoveEvent(self, e):
        pass
        # x = e.x()
        # y = e.y()
        #
        # text = "x: {0},  y: {1}".format(x, y)
        # self.sb.showMessage(text)
        # #print("event")


if __name__ == '__main__':
    cssSs_ = cssSs.read()
    app = QApplication(sys.argv)
    app.setApplicationName("Diagram Creator")
    form = MainWindow()
    form.showMaximized()
    form.show()
    # app.setStyleSheet(cssSs_)
    app.exec_()

# Found bug: fixed/when renaming/click on connection, connection gets destroyed
# Found bug: fixed/90 degrees for bridges doesn't work
# Found bug: when dragging bridging connection over another segment, crash
# Found glitch: when having a disr segment, gradient is not correct anymore
# Found bug: IceStorage, when creating new connection and moving block, the connection does not update position
# Found bug: When in mode 1, sometimes dragging leads to segments collaps to a small point
# Found bug: fixed/When reloading, a node was inexistent in loadSegement => setPre() crashed
# Found glitch: fixed/Moving pasted group rapidly produces hang in some segments (only the ones next to port?)

# Todo: Fix bugs
# Todo 0: Implement nice connections to support side handling
# Todo 1:   done/Correct export
# Todo 2:   done/Correct gradient for lines
# Todo 3:   Improve autoarrange of connections
# Todo 4:   old/Prevent loops when adding connections to StorageBlock
# Todo 5:   done/Implement segements list of connection IN ORDER, ie with insert at the correct position
#           s.t. one can easily get distance of segment to fromPort
# Todo 6: Check correct deletion of blocks and connections
# TODO 7: Solve mix up between i/o and left/right side

# TODO: Note that no direct connection between storages allowed
# There is a mess introduced with kwargs because the dencoder returns objects, which cannot have any
# connection to the "outside" of the decoder. This could maybe be improved by returning just the dict
# to the DiagramEditor class, which then can easily create the objects correctly.

# Think about a clean and concise way of putting elements into groups