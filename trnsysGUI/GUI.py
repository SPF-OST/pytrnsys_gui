#!/usr/bin/python
# import random
import glob
import re
import shutil
import string
import pandas as pd
from datetime import datetime
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
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtSvg import QSvgGenerator, QSvgWidget

from trnsysGUI.Control import Control
from trnsysGUI.MasterControl import MasterControl
from trnsysGUI.FileOrderingDialog import FileOrderingDialog
from trnsysGUI.MyQFileSystemModel import MyQFileSystemModel
from trnsysGUI.MyQTreeView import MyQTreeView
from trnsysGUI.PathSetUp import PathSetUp
from trnsysGUI.CheckBlackBox import CheckBlackBox
from trnsysGUI.FolderSetUp import FolderSetUp
from trnsysGUI.PumpDlg import PumpDlg
from trnsysGUI.DifferenceDlg import DifferenceDlg
from trnsysGUI.BlockDlg import BlockDlg
from trnsysGUI.DeepInspector import DeepInspector
from trnsysGUI.DeleteBlockCommand import DeleteBlockCommand
from trnsysGUI.Boiler import Boiler
from trnsysGUI.AirSourceHP import AirSourceHP
from trnsysGUI.Export import Export
from trnsysGUI.ExternalHx import ExternalHx
from trnsysGUI.IceStorageTwoHx import IceStorageTwoHx
from trnsysGUI.GenericPortPairDlg import GenericPortPairDlg
from trnsysGUI.GroundSourceHx import GroundSourceHx
from trnsysGUI.GroupChooserBlockDlg import GroupChooserBlockDlg
from trnsysGUI.GroupChooserConnDlg import GroupChooserConnDlg
from trnsysGUI.PV import PV

from trnsysGUI.GenericBlock import GenericBlock
from trnsysGUI.Graphicaltem import GraphicalItem
from trnsysGUI.MassFlowVisualizer import MassFlowVisualizer
from trnsysGUI.PipeDataHandler import PipeDataHandler
from trnsysGUI.PortItem import PortItem
from trnsysGUI.RunMain import RunMain
from trnsysGUI.ProcessMain import ProcessMain
from trnsysGUI.TVentilDlg import TVentilDlg
from trnsysGUI.Test_Export import Test_Export
from trnsysGUI.TestDlg import TestDlg
from trnsysGUI.diagramDlg import diagramDlg
from trnsysGUI.groupDlg import groupDlg
from trnsysGUI.groupsEditor import groupsEditor
from trnsysGUI.hxDlg import hxDlg
from trnsysGUI.newDiagramDlg import newDiagramDlg
from trnsysGUI.settingsDlg import settingsDlg

from trnsysGUI.BlockItem import BlockItem

from trnsysGUI.Collector import Collector
from trnsysGUI.ConfigStorage import ConfigStorage
from trnsysGUI.Connector import Connector
from trnsysGUI.Group import Group
from trnsysGUI.HeatPump import HeatPump
from trnsysGUI.HeatPumpTwoHx import HeatPumpTwoHx
from trnsysGUI.HPDoubleDual import HPDoubleDual
from trnsysGUI.IceStorage import IceStorage
from trnsysGUI.PitStorage import PitStorage
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
from trnsysGUI.CreateConnectionCommand import CreateConnectionCommand
from trnsysGUI.ResizerItem import ResizerItem
from trnsysGUI.configFile import configFile

import trnsysGUI.buildDck as dckBuilder

from PyQt5 import QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import os
import sys



__version__ = "1.0.0"
__author__ = "Stefano Marti"
__email__ = "stefano.marti@spf.ch"
__status__ = "Prototype"

from trnsysGUI.segmentDlg import segmentDlg

# CSS file
cssSs = open("res/style.txt", "r")

def calcDist(p1, p2):
    """

    Parameters
    ----------
    p1 : :obj: `QPointF`

    p2 : :obj: `QPointF`

    Returns
    -------

    """
    vec = p1 - p2
    norm = sqrt(vec.x() ** 2 + vec.y() ** 2)
    return norm


class DiagramDecoderPaste(json.JSONDecoder):
    """
    Decodes the clipboard.
    It creates the copied blocks with suffix COPY, it does not set the ids forward.

    """
    def __init__(self, *args, **kwargs):
        self.editor = kwargs["editor"]
        kwargs.pop("editor")
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, arr):
        """
        This is the decoding function from the clipboard. It seems to get executed for every sub dictionary in the json file.
        By looking for the specific key containing the name of dict elements, one can extract the needed dict.
        The name of the dicts is important because the order in which they are loaded matters (some objects depend on others)

        Parameters
        ----------
        arr

        Returns
        -------

        """

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

                        if i["BlockName"] == 'TeePiece':
                            bl = TeePiece(i["BlockName"], self.editor.diagramView,
                                          displayName=i["BlockDisplayName"], loaded=True)
                        elif i["BlockName"] == 'TVentil':
                            bl = TVentil(i["BlockName"], self.editor.diagramView,
                                         displayName=i["BlockDisplayName"], loaded=True)
                        elif i["BlockName"] == 'Pump':
                            bl = Pump(i["BlockName"], self.editor.diagramView,
                                      displayName=i["BlockDisplayName"], loaded=True)
                        elif i["BlockName"] == 'Collector':
                            bl = Collector(i["BlockName"], self.editor.diagramView,
                                           displayName=i["BlockDisplayName"], loaded=True)
                        elif i["BlockName"] == 'Kollektor':
                            i["BlockName"] = 'Collector'
                            bl = Collector(i["BlockName"], self.editor.diagramView,
                                           displayName=i["BlockDisplayName"], loaded=True)
                        elif i["BlockName"] == 'HP':
                            bl = HeatPump(i["BlockName"], self.editor.diagramView,
                                          displayName=i["BlockDisplayName"], loaded=True)
                        elif i["BlockName"] == 'IceStorage':
                            bl = IceStorage(i["BlockName"], self.editor.diagramView,
                                            displayName=i["BlockDisplayName"], loaded=True)
                        elif i["BlockName"] == 'PitStorage':
                            bl = PitStorage(i["BlockName"], self.editor.diagramView,
                                            displayName=i["BlockDisplayName"], loaded=True)
                        elif i["BlockName"] == 'Radiator':
                            bl = Radiator(i["BlockName"], self.editor.diagramView,
                                          displayName=i["BlockDisplayName"], loaded=True)
                        elif i["BlockName"] == 'WTap':
                            bl = WTap(i["BlockName"], self.editor.diagramView,
                                      displayName=i["BlockDisplayName"], loaded=True)
                        elif i["BlockName"] == 'WTap_main':
                            bl = WTap_main(i["BlockName"], self.editor.diagramView,
                                           displayName=i["BlockDisplayName"], loaded=True)
                        elif i["BlockName"] == 'Connector':
                            bl = Connector(i["BlockName"], self.editor.diagramView,
                                           displayName=i["BlockDisplayName"], loaded=True)
                        elif i["BlockName"] == 'GenericBlock':
                            bl = GenericBlock(i["BlockName"], self.editor.diagramView,
                                              displayName=i["BlockDisplayName"], loaded=True)
                        elif i["BlockName"] == 'Boiler':
                            bl = Boiler(i["BlockName"], self.editor.diagramView,
                                               displayName=i["BlockDisplayName"], loaded=True)
                        elif i["BlockName"] == 'AirSourceHP':
                            bl = AirSourceHP(i["BlockName"], self.editor.diagramView,
                                               displayName=i["BlockDisplayName"], loaded=True)
                        elif i["BlockName"] == 'PV':
                            bl = PV(i["BlockName"], self.editor.diagramView,
                                               displayName=i["BlockDisplayName"], loaded=True)
                        elif i["BlockName"] == 'GroundSourceHx':
                            bl = GroundSourceHx(i["BlockName"], self.editor.diagramView,
                                    displayName=i["BlockDisplayName"], loaded=True)

                        # [--- New encoding
                        elif i["BlockName"] == 'StorageTank':
                            bl = StorageTank(i["BlockName"], self.editor.diagramView,
                                               displayName=i["BlockDisplayName"], loaded=True)
                        elif i["BlockName"] == 'HeatPump':
                            bl = HeatPump(i["BlockName"], self.editor.diagramView,
                                               displayName=i["BlockDisplayName"], loaded=True)
                        elif i["BlockName"] == 'HPTwoHx':
                            bl = HeatPumpTwoHx(i["BlockName"], self.editor.diagramView,
                                               displayName=i["BlockDisplayName"], loaded=True)
                        elif i["BlockName"] == 'HPDoubleDual':
                            bl = HPDoubleDual(i["BlockName"], self.editor.diagramView,
                                               displayName=i["BlockDisplayName"], loaded=True)
                        elif i["BlockName"] == 'ExternalHx':
                            bl = ExternalHx(i["BlockName"], self.editor.diagramView,
                                               displayName=i["BlockDisplayName"], loaded=True)
                        elif i["BlockName"] == 'IceStorageTwoHx':
                            bl = IceStorageTwoHx(i["BlockName"], self.editor.diagramView,
                                                displayName=i["BlockDisplayName"], loaded=True)
                        elif i["BlockName"] == 'GenericBlock':
                            bl = GenericBlock(i["BlockName"], self.editor.diagramView,
                                            displayName=i["BlockDisplayName"], loaded=True)
                        elif i["BlockName"] == 'MasterControl':
                            bl = MasterControl(i["BlockName"], self.editor.diagramView,
                                               displayName=i["BlockDisplayName"], loaded=True)
                        elif i["BlockName"] == 'Control':
                            bl = Control(i["BlockName"], self.editor.diagramView,
                                               displayName=i["BlockDisplayName"], loaded=True)
                        # new encoding ---]

                        else:
                            bl = BlockItem(i["BlockName"], self.editor.diagramView, displayName=i["BlockName"],
                                           loaded=True)

                        bl.decodePaste(i, offset_x, offset_y, resConnList, resBlockList)

                    elif ".__ConnectionDict__" in arr[k]:
                        # It is important to load the connections at last because else the ports are not defined.
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

                        # if not i["isVirtualConn"]:  # Now internal connections don't get encoded in the first place
                        if True:
                            for cornerL in i["CornerPositions"]:
                                cornerL[0] += offset_x
                                cornerL[1] += offset_y

                            c = Connection(fport, tPort, i["isVirtualConn"], self.editor,
                                           fromPortId=i["PortFromID"], toPortId=i["PortToID"],
                                           segmentsLoad=i["SegmentPositions"], cornersLoad=i["CornerPositions"], loadedConn=True)
                            c.setName(i["ConnDisplayName"])

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

            return resBlockList, resConnList

        return arr


class DiagramDecoder(json.JSONDecoder):
    """
    Decodes the diagram
    """
    def __init__(self, *args, **kwargs):
        self.editor = kwargs["editor"]
        kwargs.pop("editor")
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, arr):
        """
        This is the decoding function. object_hook seems to get executed for every sub dictionary in the json file.
        By looking for the specific key containing the name of dict elements, one can extract the needed dict.
        The name of the dicts is important because the order in which they are loaded matters (some objects depend on others)
        Parameters
        ----------
        arr

        Returns
        -------

        """

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

                    # Adding the blocks to the scene could also be done inside Decoder now (before not possible because
                    # no way of accessing the diagramView)

                    elif ".__BlockDict__" in arr[k]:
                        print("Found a block ")
                        i = arr[k]

                        if i["BlockName"] == 'TeePiece':
                            bl = TeePiece(i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"],
                                          loadedBlock=True)
                        elif i["BlockName"] == 'TVentil':
                            bl = TVentil(i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"],
                                         loadedBlock=True)
                        elif i["BlockName"] == 'Pump':
                            bl = Pump(i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"],
                                      loadedBlock=True)
                        elif i["BlockName"] == 'Collector':
                            bl = Collector(i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"],
                                           loadedBlock=True)
                        elif i["BlockName"] == 'HP':
                            bl = HeatPump(i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"],
                                          loadedBlock=True)
                        elif i["BlockName"] == 'IceStorage':
                            bl = IceStorage(i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"],
                                            loadedBlock=True)
                        elif i["BlockName"] == 'PitStorage':
                            bl = PitStorage(i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"],
                                            loadedBlock=True)
                        elif i["BlockName"] == 'Radiator':
                            bl = Radiator(i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"],
                                          loadedBlock=True)
                        elif i["BlockName"] == 'WTap':
                            bl = WTap(i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"],
                                      loadedBlock=True)
                        elif i["BlockName"] == 'WTap_main':
                            bl = WTap_main(i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"],
                                           loadedBlock=True)
                        elif i["BlockName"] == 'Connector':
                            bl = Connector(i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"],
                                           loadedBlock=True)
                        elif i["BlockName"] == 'Boiler':
                            bl = Boiler(i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"],
                                           loadedBlock=True)
                        elif i["BlockName"] == 'AirSourceHP':
                            bl = AirSourceHP(i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"],
                                           loadedBlock=True)
                        elif i["BlockName"] == 'PV':
                            bl = PV(i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"],
                                           loadedBlock=True)
                        elif i["BlockName"] == 'GroundSourceHx':
                            bl = GroundSourceHx(i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"],
                                           loadedBlock=True)

                        # [--- new encoding
                        elif i["BlockName"] == 'StorageTank':
                            bl = StorageTank(i["BlockName"], self.editor.diagramView,
                                               displayName=i["BlockDisplayName"], loadedBlock=True)
                        elif i["BlockName"] == 'HeatPump':
                            bl = HeatPump(i["BlockName"], self.editor.diagramView,
                                               displayName=i["BlockDisplayName"], loadedBlock=True)
                        elif i["BlockName"] == 'HPTwoHx':
                            bl = HeatPumpTwoHx(i["BlockName"], self.editor.diagramView,
                                               displayName=i["BlockDisplayName"], loadedBlock=True)
                        elif i["BlockName"] == 'HPDoubleDual':
                            bl = HPDoubleDual(i["BlockName"], self.editor.diagramView,
                                               displayName=i["BlockDisplayName"], loadedBlock=True)
                        elif i["BlockName"] == 'ExternalHx':
                            bl = ExternalHx(i["BlockName"], self.editor.diagramView,
                                               displayName=i["BlockDisplayName"], loadedBlock=True)
                        elif i["BlockName"] == 'IceStorageTwoHx':
                            bl = IceStorageTwoHx(i["BlockName"], self.editor.diagramView,
                                                displayName=i["BlockDisplayName"], loadedBlock=True)
                        elif i["BlockName"] == 'GenericBlock':
                            bl = GenericBlock(i["BlockName"], self.editor.diagramView,
                                               displayName=i["BlockDisplayName"], loadedBlock=True)
                        elif i["BlockName"] == 'MasterControl':
                            bl = MasterControl(i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"],
                                           loadedBlock=True)
                        elif i["BlockName"] == 'Control':
                            bl = Control(i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"],
                                           loadedBlock=True)
                        # --- new encoding]

                        elif i["BlockName"] == "GraphicalItem":
                            bl = GraphicalItem(self.editor.diagramView, loadedGI=True)

                        else:
                            bl = BlockItem(i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"])

                        bl.decode(i, resConnList, resBlockList)

                    elif ".__ConnectionDict__" in arr[k]:
                        i = arr[k]

                        fport = None
                        tPort = None

                        # Looking for the ports the connection is connected to
                        for connBl in resBlockList:
                            for p in connBl.inputs + connBl.outputs:
                                if p.id == i["PortFromID"]:
                                    fport = p
                                if p.id == i["PortToID"]:
                                    tPort = p

                        if fport is None:
                            print("Error: Did not found a fromPort")

                        if tPort is None:
                            print("Error: Did not found a toPort")

                        # To allow loading json files without FirstSegmentPos (old version of encoding)
                        if "FirstSegmentLabelPos" in i:
                            c = Connection(fport, tPort, i["isVirtualConn"], self.editor,
                                           fromPortId=i["PortFromID"], toPortId=i["PortToID"],
                                           segmentsLoad=i["SegmentPositions"], cornersLoad=i["CornerPositions"],
                                           labelPos=i["FirstSegmentLabelPos"], loadedConn=True)
                        else:
                            c = Connection(fport, tPort, i["isVirtualConn"], self.editor,
                                           fromPortId=i["PortFromID"], toPortId=i["PortToID"],
                                           segmentsLoad=i["SegmentPositions"], cornersLoad=i["CornerPositions"],
                                           loadedConn=True)

                        c.decode(i, resConnList, resBlockList)

                    elif "__idDct__" in arr[k]:
                        resBlockList.append(arr[k])
                    elif "__nameDct__" in arr[k]:
                        resBlockList.append(arr[k])
                    else:
                        print("Error: Not recognized object in decoder, " + str(arr[k]))

            # return resBlockList, resConnList, resStorageConnList
            return resBlockList, resConnList

        return arr


class DiagramEncoder(json.JSONEncoder):
    """
    This class encodes the diagram (entire diagram or clipboard)
    obj is passed along to get some of the diagram editor porperties, for instance the id-generator
    TrnsysObj are then stored in a list of dictionaries, saved to a json file.
    Important: There is a slight naming error, since the dict containing all sub dicts (dicts for each block, connection
    and Id-generator) has the key ".__BlockDct__", although there are also other elements in there.
    """

    def default(self, obj):
        """

        Parameters
        ----------
        obj
        :type obj: DiagramEditor

        Returns
        -------

        """
        if isinstance(obj, DiagramEditor) or isinstance(obj, copyGroup):
            print("Is diagram or copygroup")

            res = {}
            blockDct = {".__BlockDct__": True}

            for t in obj.trnsysObj:
                if isinstance(t, BlockItem) and t.isVisible() is False:
                    print("Invisible block [probably an insideBlock?]" + str(t) + str(t.displayName))
                    continue
                if isinstance(t, Connection) and t.isVirtualConn:
                    continue

                dictName, dct = t.encode()
                blockDct[dictName + str(t.id)] = dct

            idDict = {"__idDct__": True, "GlobalId": obj.idGen.getID(), "trnsysID": obj.idGen.getTrnsysID(), "globalConnID": obj.idGen.getConnID()}
            blockDct["IDs"] = idDict

            nameDict = {"__nameDct__": True, "DiagramName": obj.diagramName, "ProjectFolder": obj.projectFolder}
            blockDct["Strings"] = nameDict

            for g in obj.groupList:
                dct = {}
                dct[".__GroupDict__"] = True
                dct["GroupName"] = g.displayName
                dct["Position"] = g.x, g.y
                dct["Size"] = g.w, g.h

                blockDct["..__GroupDct-" + g.displayName] = dct

            for gi in obj.graphicalObj:
                dictName, dct = gi.encode()
                blockDct[dictName + str(gi.id)] = dct

            res["Blocks"] = blockDct

            return res
        else:
            print("This is a strange object in DiagramEncoder" + type(obj))
            # return super().default(obj)


class DiagramScene(QGraphicsScene):
    """
    This class serves as container for QGraphicsItems and is used in combination with the DiagramView to display the
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
        Used to set the initial DiagramScene size to approximately DiagramView size
    viewRect2 : :obj:`QGraphicsRectItem`
            Used to set the initial DiagramScene size to approximately DiagramView size
    released : bool
        Enables the display of the selectionRect
    pressed : bool
        Set to True when selectionMode is True and mousePressed
        Set to False when no element in selection

    """

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

        self.selectedItem = None

        # self.viewRect1.setPos(-1300, -100)
        # self.viewRect2.setPos(-1300, -100)

        self.released = False
        self.pressed = False

    def mouseMoveEvent(self, mouseEvent):
        self.parent().sceneMouseMoveEvent(mouseEvent)
        super(DiagramScene, self).mouseMoveEvent(mouseEvent)

        if self.parent().selectionMode and not self.released and self.pressed:
            self.selectionRect.setVisible(True)
            self.sRw = (mouseEvent.scenePos().x() - self.sRstart.x())
            self.sRh = (mouseEvent.scenePos().y() - self.sRstart.y())

            if self.sRw < 0 and self.sRh > 0:  # from top right to bottom left
                rectangleR1 = QRectF(self.sRstart.x(), self.sRstart.y(), -abs(self.sRw), self.sRh).normalized()
                self.selectionRect.setRect(rectangleR1)
            elif self.sRw < 0 and self.sRh < 0: # from bottom right to top left
                rectangleR1 = QRectF(self.sRstart.x(), self.sRstart.y(), -abs(self.sRw), -abs(self.sRh)).normalized()
                self.selectionRect.setRect(rectangleR1)
            elif self.sRw > 0 and self.sRh < 0: # from bottom left to top right
                rectangleR1 = QRectF(self.sRstart.x(), self.sRstart.y(), self.sRw, -abs(self.sRh)).normalized()
                self.selectionRect.setRect(rectangleR1)
            else:
                rectangleR1 = QRectF(self.sRstart.x(), self.sRstart.y(), self.sRw, self.sRh)
                self.selectionRect.setRect(rectangleR1)

    def mouseReleaseEvent(self, mouseEvent):
        print("Releasing mouse in DiagramScene...")
        self.parent().sceneMouseReleaseEvent(mouseEvent)
        super(DiagramScene, self).mouseReleaseEvent(mouseEvent)
        self.parent().moveDirectPorts = False
        if self.parent().pasting:
            # Dismantle group
            self.parent().clearCopyGroup()

        if self.parent().itemsSelected:
            # Dismantle selection
            self.parent().clearSelectionGroup()

        if self.parent().selectionMode:
            # self.released = True
            print("There are elements inside the selection : " + str(self.hasElementsInRect()))
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
                    print("No recognized mode")
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
            super(DiagramScene, self).drawBackground(painter, rect)

    # def mouseMoveEvent(self, e):
    #     self.setMouseTracking(True)
    #     print("In scene")
    #     self.window().mouseMoveEvent(e)

    def keyPressEvent(self, event):
        pass
        if event.key() == Qt.Key_L:
            self.parent().moveDirectPorts = not self.parent().moveDirectPorts
            print("Changing move bool to " + str(self.parent().moveDirectPorts))

        #     print("Toggling mode")
        #     # global editorMode
        #     self.parent().editorMode = (self.parent().editorMode + 1) % 2
        #     self.parent().parent().sb.showMessage("Mode is " + str(self.parent().editorMode))
        #
        # if event.key() == Qt.Key_S:
        #     print("Toggling selectionMode")
        #     # global selectionMode
        #     self.parent().selectionMode = not self.parent().selectionMode


    def mousePressEvent(self, event):
        # self.parent().mousePressEvent(event)
        # TODO : remove resizer when click on other block items
        super(DiagramScene, self).mousePressEvent(event)

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
            print("No items here!")
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
                    if isinstance(items, GraphicalItem) and hasattr(items, 'resizer'):
                        self.removeItem(items.resizer)
                        items.deleteResizer()
                    if isinstance(items, BlockItem) and hasattr(items, 'resizer'):
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
                self.selectionRect.setRect(self.sRstart.x(), self.sRstart.y(), abs(event.scenePos().x() - self.sRstart.x()),
                                           abs(event.scenePos().y() - self.sRstart.y()))
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
                print("Checking block to group")
                if self.isInRect(o.scenePos()):
                    res.append(o)

            if type(o) is Connection:
                print("Checking connection to group")
                if self.isInRect(o.fromPort.scenePos()) and self.isInRect(o.toPort.scenePos()):
                    res.append(o)

        for o in self.parent().graphicalObj:
            if isinstance(o, GraphicalItem):
                print("Checking graphic item to group")
                if self.isInRect(o.scenePos()):
                    res.append(o)

        return res

    def hasElementsInRect(self):
        # Check if there are elements in the selection rectangle
        for o in self.parent().trnsysObj:
            if isinstance(o, BlockItem):
                print("Checking block to group")
                if self.isInRect(o.scenePos()):
                    return True

            if type(o) is Connection:
                print("Checking connection to group")
                if self.isInRect(o.fromPort.scenePos()) and self.isInRect(o.toPort.scenePos()):
                    return True

        for o in self.parent().graphicalObj:
            if isinstance(o, GraphicalItem):
                print("Checking graphic item to group")
                if self.isInRect(o.scenePos()):
                    return True

        return False

    def isInRect(self, point):
        # Check if a point is in the selection rectangle
        # from top left to bottom right
        if point.x() > self.sRstart.x() and point.x() < (
                self.sRstart.x() + self.sRw) and point.y() > self.sRstart.y() and point.y() < (
                self.sRstart.y() + self.sRh):
            print("In rect")
            return True

        # from top right to bottom left
        elif point.x() < self.sRstart.x() and point.x() > (self.sRstart.x() + self.sRw)\
                and point.y() > self.sRstart.y() and point.y() < (self.sRstart.y() + self.sRh):
            print("In rect")
            return True

        # from bottom right to top left
        elif point.x() < self.sRstart.x() and point.x() > (self.sRstart.x() + self.sRw)\
                and point.y() < self.sRstart.y() and point.y() > (self.sRstart.y() + self.sRh):
            print("In rect")
            return True

        # from bottom left to top right
        elif point.x() > self.sRstart.x() and point.x() < (self.sRstart.x() + self.sRw)\
                and point.y() < self.sRstart.y() and point.y() > (self.sRstart.y() + self.sRh):
            print("In rect")
            return True

        else:
            return False


class DiagramView(QGraphicsView):
    """
    Displays the items from the DiagramScene. Here, the drag and drop from the library to the View is implemented.

    """
    def __init__(self, scene, parent=None):
        QGraphicsView.__init__(self, scene, parent)
        # self.setMinimumSize(self.parent().horizontalLayout.height, 700)
        self.adjustSize()
        # self.setMinimumSize(1300, 700)
        self.parent().diagramScene.viewRect2.setPos(-self.width() / 2, -self.height() / 2)
        # self.parent().diagramScene.viewRect2.setPos(1300, 700)
        # Use aliasing or not:
        self.setRenderHint(QPainter.Antialiasing)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('component/name'):
            event.accept()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat('component/name'):
            event.accept()

    def dropEvent(self, event):
        """Here, the dropped icons create BlockItems/GraphicalItems"""
        if event.mimeData().hasFormat('component/name'):
            name = str(event.mimeData().data('component/name'), encoding='utf-8')
            print("name is " + name)
            if name == 'StorageTank':
                bl = StorageTank(name, self)
                # c = ConfigStorage(bl, self)
                self.parent().showConfigStorageDlg(bl)
            elif name == 'TeePiece':
                bl = TeePiece(name, self)
            elif name == 'TVentil':
                bl = TVentil(name, self)
            elif name == 'Pump':
                bl = Pump(name, self)
            elif name == 'Collector':
                bl = Collector(name, self)
            elif name == 'HP':
                bl = HeatPump(name, self)
            elif name == 'IceStorage':
                bl = IceStorage(name, self)
            elif name == 'PitStorage':
                bl = PitStorage(name, self)
            elif name == 'Radiator':
                bl = Radiator(name, self)
            elif name == 'WTap':
                bl = WTap(name, self)
            elif name == 'WTap_main':
                bl = WTap_main(name, self)
            elif name == 'Connector':
                bl = Connector(name, self)
            elif name == 'GenericBlock':
                bl = GenericBlock(name, self)
                # c = GenericPortPairDlg(bl, self)
                self.parent().showGenericPortPairDlg(bl)
            elif name == 'HPTwoHx':
                bl = HeatPumpTwoHx(name, self)
            elif name == 'HPDoubleDual':
                bl = HPDoubleDual(name, self)
            elif name == 'Boiler':
                bl = Boiler(name, self)
            elif name == 'AirSourceHP':
                bl = AirSourceHP(name, self)
            elif name == 'PV':
                bl = PV(name, self)
            elif name == 'GroundSourceHx':
                bl = GroundSourceHx(name, self)
            elif name == 'ExternalHx':
                bl = ExternalHx(name, self)
            elif name == 'IceStorageTwoHx':
                bl = IceStorageTwoHx(name, self)
            elif name == 'GenericItem':
                bl = GraphicalItem(self)
            elif name == 'MasterControl':
                bl = MasterControl(name, self)
            elif name == 'Control':
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

        super(DiagramView, self).mouseReleaseEvent(mouseEvent)

    def wheelEvent(self, event):
        super(DiagramView, self).wheelEvent(event)
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

        super(DiagramView, self).mousePressEvent(event)

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

class newOrLoadWindow(QMessageBox):
    """
        This class represents a dialogue box that is shown when starting the GUI. It asks the user whether a new
        project should be opened or if an exisiting one should be loaded. Its parent class is QMessageBox.
    """
    def __init__(self,parent=None):
        QMessageBox.__init__(self,parent)
        self.setWindowTitle("Initializing options")

        self.addButton(QPushButton("New"), QMessageBox.YesRole)
        self.addButton(QPushButton("Open"), QMessageBox.NoRole)
        self.addButton(QPushButton("Cancel"), QMessageBox.RejectRole)

        #self.setDefaultButton(QPushButton("Cancel"), QMessageBox.RejectRole)



class DiagramEditor(QWidget):
    """
    This class is the central widget of the MainWindow.
    It contains the items library, diagram graphics scene and graphics view, and the inspector widget

    Function of Connections:
    Logically:
    A Connection is composed of a fromPort and a toPort, which gives the direction of the pipe.
    Ports are attached to Blocks.
    Initially, there is a temporary fromPort set to None.
    As soon any Port is clicked and dragged, tempStartPort is set to that Port and startedConnectino is set to True.
    -> startConnection()
    If the mouse is then released over a different Port, a Connection is created, otherwise startedConnection is set to False
    and the process is interrupted.
    -> createConnection()
    Visually:
    A diagram editor has a QGraphicsLineItem (connLineItem) which is set Visible only when a connection is being created

    Function of BlockItems:
    Items can be added to the library by adding them to the model of the library broswer view.
    Then they can be dragged and dropped into the diagram view.

    Function of trnsysExport:
    When exporting the trnsys file, exportData() is called.

    Function of save and load:
    A diagram can be saved to a json file by calling encodeDiagram and can then be loaded by calling decodeDiagram wiht
    appropiate filenames.

    Function of copy-paste:
    Copying a rectangular part of the diagram to the clipboard is just encoding the diagram to the file clipboard.json,
    and pasting will load the clipboard using a slighly different decoder than for loading an entire diagram.
    When the elements are pasted, they compose a group which can be dragged around and is desintegrated when the mouse
    is released.
    It is controlled by the attributes selectionMode, groupMode, copyMode and multipleSelectedMode

    Attributes
    ----------
    projectFolder : str
        Path to the folder of the project
    diagramName : str
        Name used for saving the diagram
    saveAsPath : :obj:`Path`
        Default saving location is trnsysGUI/diagrams, path only set if "save as" used
    idGen : :obj:`IdGenerator`
        Is used to distribute ids (id, trnsysId(for trnsysExport), etc)
    selectionMode : bool
        Enables/disables selection rectangle in DiagramScene
    groupMode : bool
        Enables creation of a new group in DiagramScene
    copyMode : bool
        Enables copying elements in the selection rectangle
    multipleSelectedMode : bool
        Unused
    alignMode : bool
        Enables mode in which a dragged block is aligned to y or x value of another one
        Toggled in the MainWindow class in toggleAlignMode()
    pasting : bool
        Used to allow dragging of the copygroup right after pasting. Set to true after decodingPaste is called.
        Set to false as soon as releasedMouse after decodePaste.
    itemsSelected : bool

    editorMode : int
        Mode 0: Pipes are PolySun-like
        Mode 1: Pipes have only 90deg angles, visio-like
    snapGrid : bool
        Enable/Disable align grid
    snapSize : int
        Size of align grid

    horizontalLayout : :obj:`QHBoxLayout`
    Contains the diagram editor and the layout containing the library browser view and the listview
    vertL : :obj:`QVBoxLayout`
    Cointains the library browser view and the listWidget

    datagen : :obj:`PipeDataHandler`
        Used for generating random massflows for every timestep to test the massflow
        visualizer prototype
    moveDirectPorts: bool
        Enables/Disables moving direct ports of storagetank (doesn't work with HxPorts yet)
    diagramScene : :obj:`QGraphicsScene`
        Contains the "logical" part of the diagram
    diagramView : :obj:`QGraphicsView`
        Contains the visualization of the diagramScene
    startedConnection : Bool
    tempStartPort : :obj:`PortItem`
    connectionList : :obj:`List` of :obj:`Connection`
    trnsysObj : :obj:`List` of :obj:`BlockItem` and :obj:`Connection`
    groupList : :obj:`List` of :obj:`BlockItem` and :obj:`Connection`
    graphicalObj : :obj:`List` of :obj:`GraphicalItem`
    connLine : :obj:`QLineF`
    connLineItem = :obj:`QGraphicsLineItem`

    """
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.projectFolder = parent.projectFolder

        self.diagramName = os.path.split(self.projectFolder)[-1] + '.json'
        self.saveAsPath = Path()
        self.idGen = IdGenerator()

        # Generator for massflow display testing
        self.datagen = PipeDataHandler(self)

        self.testEnabled = False
        self.existReference = True

        self.controlExists = 0
        self.controlDirectory = ''

        self.selectionMode = False
        self.groupMode = False
        self.copyMode = False
        self.multipleSelectedMode = False

        self.alignMode = False

        self.pasting = False
        self.itemsSelected = False

        self.moveDirectPorts = False

        self.editorMode = 1

        # Related to the grid blocks can snap to
        self.snapGrid = False
        self.snapSize = 20

        self.trnsysPath = 'C:\Trnsys17\Exe\TRNExe.exe'

        self.horizontalLayout = QHBoxLayout(self)
        self.libraryBrowserView = QListView(self)
        self.libraryModel = LibraryModel(self)

        self.libraryBrowserView.setGridSize(QSize(65, 65))
        self.libraryBrowserView.setResizeMode(QListView.Adjust)
        self.libraryModel.setColumnCount(0)

        self.libItems = []

        # Resource folder for library icons
        r_folder = "images/"
        componentsList = ['Connector','TeePiece','TVentil','WTap_main','WTap','Pump','Collector','GroundSourceHx','PV',
                          'HP','HPTwoHx','HPDoubleDual','AirSourceHP','StorageTank','IceStorage','PitStorage',
                          'IceStorageTwoHx','ExternalHx','Radiator','Boiler','GenericBlock','GenericItem']
        for component in componentsList:
            self.libItems.append(QtGui.QStandardItem(QIcon(r_folder+component),component))
        #self.libItems.append(QtGui.QStandardItem(QIcon(QPixmap(r_folder + 'MasterControl')), 'MasterControl'))
        #self.libItems.append(QtGui.QStandardItem(QIcon(QPixmap(r_folder + 'control')), 'Control'))

        for i in self.libItems:
            self.libraryModel.appendRow(i)

        self.libraryBrowserView.setModel(self.libraryModel)
        self.libraryBrowserView.setViewMode(self.libraryBrowserView.IconMode)
        self.libraryBrowserView.setDragDropMode(self.libraryBrowserView.DragOnly)

        self.diagramScene = DiagramScene(self)
        self.diagramView = DiagramView(self.diagramScene, self)

        # For list view
        self.vertL = QVBoxLayout()
        self.vertL.addWidget(self.libraryBrowserView)
        self.vertL.setStretchFactor(self.libraryBrowserView, 2)
        self.listV = QListWidget()
        self.vertL.addWidget(self.listV)
        self.vertL.setStretchFactor(self.listV, 1)

        # for file browser
        self.projectPath = ''                                               # XXX
        self.fileList = []                                                  # XXX

        if parent.loadValue == 'new' or parent.loadValue == 'json':
            self.createProjectFolder()

        self.fileBrowserLayout = QVBoxLayout()
        self.pathLayout = QHBoxLayout()
        self.projectPathLabel = QLabel("Project Path:")
        self.PPL = QLineEdit(self.projectFolder)
        self.PPL.setDisabled(True)

        #self.setProjectPathButton = QPushButton("Change path")
        #self.setProjectPathButton.clicked.connect(self.setProjectPath)
        #self.openProjectButton = QPushButton("Open Project")
        #self.openProjectButton.clicked.connect(self.openProject)

        self.pathLayout.addWidget(self.projectPathLabel)
        self.pathLayout.addWidget(self.PPL)
        #self.pathLayout.addWidget(self.setProjectPathButton)
        #self.pathLayout.addWidget(self.openProjectButton)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.splitter = QSplitter(Qt.Vertical,)
        self.splitter.setChildrenCollapsible(False)
        self.scroll.setWidget(self.splitter)
        self.scroll.setFixedWidth(350)
        self.fileBrowserLayout.addLayout(self.pathLayout)
        self.fileBrowserLayout.addWidget(self.scroll)
        self.createDdckTree(self.projectFolder)

        if parent.loadValue == 'new' or parent.loadValue == 'json':
            self.createConfigBrowser(self.projectFolder)
            self.copyGenericFolder(self.projectFolder)
            self.createHydraulicDir(self.projectFolder)
            self.createWeatherAndControlDirs(self.projectFolder)

        self.horizontalLayout.addLayout(self.vertL)
        self.horizontalLayout.addWidget(self.diagramView)
        self.horizontalLayout.addLayout(self.fileBrowserLayout)
        self.horizontalLayout.setStretchFactor(self.diagramView, 5)
        self.horizontalLayout.setStretchFactor(self.libraryBrowserView, 1)

        self.startedConnection = False
        self.tempStartPort = None
        self.connectionList = []
        self.trnsysObj = []
        self.groupList = []
        self.graphicalObj = []

        self.defaultGroup = Group(0, 0, 100, 100, self.diagramScene)
        self.defaultGroup.setName("defaultGroup")

        self.copyGroupList = QGraphicsItemGroup()
        self.selectionGroupList = QGraphicsItemGroup()

        self.printerUnitnr = 0

        # For debug button
        # a = 400  # Start of upmost button y-value
        # b = 50  # distance between starts of button y-values
        # b_start = 75

        # self.button = QPushButton(self)
        # self.button.setText("Print info")
        # self.button.move(b_start, a)
        # self.button.setMinimumSize(120, 40)
        # self.button.clicked.connect(self.button1_clicked)

        # Different colors for connLineColor
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

        # Only for displaying on-going creation of connection
        self.connLine = QLineF()
        self.connLineItem = QGraphicsLineItem(self.connLine)
        self.connLineItem.setPen(QtGui.QPen(connLinecolor, linePx))
        self.connLineItem.setVisible(False)
        self.diagramScene.addItem(self.connLineItem)

        # For line that shows quickly up when using the align mode
        self.alignYLine = QLineF()
        self.alignYLineItem = QGraphicsLineItem(self.alignYLine)
        self.alignYLineItem.setPen(QtGui.QPen(QColor(196, 249, 252), 2))
        self.alignYLineItem.setVisible(False)
        self.diagramScene.addItem(self.alignYLineItem)

        # For line that shows quickly up when using align mode
        self.alignXLine = QLineF()
        self.alignXLineItem = QGraphicsLineItem(self.alignXLine)
        self.alignXLineItem.setPen(QtGui.QPen(QColor(196, 249, 252), 2))
        self.alignXLineItem.setVisible(False)
        self.diagramScene.addItem(self.alignXLineItem)

        test = os.path.join(self.projectFolder,self.diagramName)

        if parent.loadValue == 'load' or parent.loadValue == 'copy':
            self.decodeDiagram(os.path.join(self.projectFolder,self.diagramName),loadValue=parent.loadValue)
        elif parent.loadValue == 'json':
            self.decodeDiagram(parent.jsonPath,loadValue=parent.loadValue)

        # #Search related lists
        # self.bfs_visitedNodes = []
        # self.bfs_neighborNodes = []
        # self.blockList = []

    # Debug function
    def dumpInformation(self):
        print("\n\nHello, this is a dump of the diagram information.\n")
        print("Mode is " + str(self.editorMode) + "\n")

        print("Next ID is " + str(self.idGen.getID()))
        print("Next bID is " + str(self.idGen.getBlockID()))
        print("Next cID is " + str(self.idGen.getConnID()))

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


    # Connections related methods
    def startConnection(self, port):
        """
        When a PortItem is clicked, it is saved into the tempStartPort

        Parameters
        ----------
        port : :obj:`PortItem`

        Returns
        -------

        """
        print("port is " + str(port))
        self.tempStartPort = port
        self.startedConnection = True

    def createConnection(self, startPort, endPort):
        """
        Creates a new connection if startPort and endPort are not the same. Is added as a command to the
        undoStack.

        Parameters
        ----------
        startPort : :obj:`PortItem`
        endPort : :obj:`PortItem`

        Returns
        -------

        """
        # print("Creating connection...")
        if startPort is not endPort:
            # if len(endPort.connectionList) == 0:
            # Connection(startPort, endPort, False, self)

            if isinstance(startPort.parent, StorageTank) and isinstance(endPort.parent, StorageTank)\
                    and startPort.parent != endPort.parent:
                msgSTank = QMessageBox(self)
                msgSTank.setText("Storage Tank to Storage Tank connection is not working atm!")
                msgSTank.exec_()

            command = CreateConnectionCommand(startPort, endPort, False, self, "CreateConn Command")
            self.parent().undoStack.push(command)

    def sceneMouseMoveEvent(self, event):
        """
        Qt method that sets the line signalling the creation of a new connection.

        Parameters
        ----------
        event

        Returns
        -------

        """
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
        """
        This function is called before the export file is generated. It connects all direct ports using TPieces and
        Connections and it connects the HeatExchanger ports using a Connector block (this is because HeatExchangers
        should work like BlockItems. This could maybe be improved by having a HeatExchanger as BlockItem sublclass.)
        Returns
        -------

        """
        for t in self.trnsysObj:
            if type(t) is StorageTank:

                for hx in t.heatExchangers:
                    if hx.sSide == 0:
                        t.connectHxs(self.findStorageCorrespPortsHx([hx.port1, hx.port2]), [hx.port1, hx.port2], t.hxInsideConnsLeft, "L", hx)
                    elif hx.sSide == 2:
                        print("storage of hx R is " + str(t.displayName))
                        print("hx ports are" + str(hx.port1) + str(hx.port2))
                        t.connectHxs(self.findStorageCorrespPortsHx([hx.port1, hx.port2]), [hx.port1, hx.port2], t.hxInsideConnsRight, "R", hx)
                    else:
                        print("heatExchanger has not valid sSide")

                # print("t.leftside has len " + str(len(t.leftSide)))
                # print("t.leftside is " + str(t.rightSide))
                t.connectInside(self.findStorageCorrespPorts(t.leftSide), t.leftSide, t.insideConnLeft, "L")
                t.connectInside(self.findStorageCorrespPorts(t.rightSide), t.rightSide, t.insideConnRight, "R")

                # print("------Checking insideConns")
                # print(t.hxInsideConnsLeft)
                # print(t.hxInsideConnsRight)
                # print(t.insideConnLeft)
                # print(t.insideConnRight)

    def findStorageCorrespPorts(self, portList):
        """
        This function gets the ports on the other side of pipes connected to a port of the StorageTank

        Parameters
        ----------
        portList :obj:`List` of :obj:`PortItem`

        Returns
        -------
        res : :obj:`List` of :obj:`PortItem`
        """

        res = []
        for p in portList:
            firstOutConn = None
            for c in p.connectionList:
                firstOutConn = c
                if c.toPort.parent != c.fromPort.parent:
                    break

            if firstOutConn is not None:
                if firstOutConn.toPort == p:
                    res.append(firstOutConn.fromPort)
                else:
                    res.append(firstOutConn.toPort)
            else:
                print("Error. No corresponding storage port found")
                res.append(p)

        return res

    def findStorageCorrespPortsHx(self, portList):
        """
        Parameters
        ----------
        portList

        Returns
        -------
        res : :obj:`List` of :obj:`PortItem`
        """
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
        """
        Deletes all generated inner connections after exporting to Trnsys
        Returns
        -------

        """
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

    def connectionPrinter(self):
        # name = []
        # fromPort1 = []
        # fromPort2 = []
        # toPort1 = []
        # toPort2 = []
        # for obj in self.trnsysObj:
        #     if isinstance(obj,Connection):
        #         name.append(obj.displayName)
        #         fromPort1.append(obj.fromPort.connectionList[0].displayName)
        #         toPort1.append(obj.toPort.connectionList[0].displayName)
        #         if len(obj.fromPort.connectionList) == 2:
        #             fromPort2.append(obj.fromPort.connectionList[1].displayName)
        #         else:
        #             fromPort2.append('')
        #         if len(obj.toPort.connectionList) == 2:
        #             toPort2.append(obj.toPort.connectionList[1].displayName)
        #         else:
        #             toPort2.append('')
        # table = {
        #         'Name': name,
        #         'from 1': fromPort1,
        #         'from 2': fromPort2,
        #         'to 1': toPort1,
        #         'to 2': toPort2
        #         }
        # df = pd.DataFrame(table, columns=['Name','from 1','from 2','to 1','to 2'])

        name = []
        in1 = []
        in2 = []
        out1 = []
        out2 = []
        for obj in self.trnsysObj:
            if not isinstance(obj,Connection):
                name.append(obj.displayName)
                try:
                    in1.append(obj.inputs[0].connectionList[0].displayName)
                except:
                    in1.append('')
                try:
                    in2.append(obj.inputs[1].connectionList[0].displayName)
                except:
                    in2.append('')
                try:
                    out1.append(obj.outputs[0].connectionList[0].displayName)
                except:
                    out1.append('')
                try:
                    out2.append(obj.outputs[1].connectionList[0].displayName)
                except:
                    out2.append('')
        table = {
                'Name': name,
                'in 1': in1,
                'in 2': in2,
                'out 1': out1,
                'out 2': out2
                }
        df = pd.DataFrame(table, columns=['Name','in 1','in 2','out 1','out 2'])

    def exportData(self,exportTo='hydraulics'):
        print("------------------------> START OF EXPORT <------------------------")

        self.setUpStorageInnerConns()

        self.sortTrnsysObj()

        fullExportText = ''

        ddckFolder = os.path.join(self.projectFolder,'ddck')

        if exportTo == 'mfs':
            mfsFileName = self.diagramName.split('.')[0] + '_mfs.dck'
            exportPath = os.path.join(self.projectFolder,mfsFileName)
            if Path(exportPath).exists():
                qmb = QMessageBox(self)
                qmb.setText("Warning: " + exportPath + " already exists. Do you want to overwrite it or cancel?")
                qmb.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
                qmb.setDefaultButton(QMessageBox.Cancel)
                ret = qmb.exec()
                if ret == QMessageBox.Save:
                    self.canceled = False
                    print("Overwriting")
                    # continue
                else:
                    self.canceled = True
                    print("Canceling")
                    return
            else:
                # Export file does not exist yet
                pass
        elif exportTo == 'hydraulics':
            hydraulicsPath = os.path.join(ddckFolder,"hydraulic\\hydraulic.ddck")
            if Path(hydraulicsPath).exists():
                qmb = QMessageBox(self)
                qmb.setText("Warning: " +
                            "A ddck-file already exists in the hydraulic folder. Do you want to overwrite it or cancel?")
                qmb.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
                qmb.setDefaultButton(QMessageBox.Cancel)
                ret = qmb.exec()
                if ret == QMessageBox.Save:
                    self.canceled = False
                    print("Overwriting")
                    # continue
                else:
                    self.canceled = True
                    print("Canceling")
                    return
            else:
                # Export file does not exist yet
                pass

        print("Printing the TRNSYS file... \n")

        if exportTo == "mfs":
            header = open(os.path.join(ddckFolder,"generic\\head.ddck"),"r")
            headerLines = header.readlines()
            for line in headerLines:
                if line[:4] == "STOP":
                    fullExportText += "STOP = 1 \n"
                else:
                    fullExportText += line
            header.close()
            print("\n")
        elif exportTo == "hydraulics":
            fullExportText += "*************************************\n"
            fullExportText += "**BEGIN hydraulic.ddck\n"
            fullExportText += "*************************************\n"

        simulationUnit = 450
        simulationType = 935
        descConnLength = 20

        exporter = Export(self.trnsysObj, self)


        blackBoxProblem, blackBoxText = exporter.exportBlackBox(exportTo=exportTo)
        if blackBoxProblem:
            return
        fullExportText += blackBoxText
        fullExportText += exporter.exportPumpOutlets()
        fullExportText += exporter.exportMassFlows()
        exportCancelled, divSettingText = exporter.exportDivSetting(simulationUnit - 10,exportTo=exportTo)
        if exportCancelled:
            return
        if exportTo == 'mfs':
            fullExportText += divSettingText
        # fullExportText += exporter.exportDivSetting(simulationUnit - 10)

        fullExportText += exporter.exportParametersFlowSolver(simulationUnit, simulationType, descConnLength)#, parameters, lineNrParameters)
        fullExportText += exporter.exportInputsFlowSolver()
        fullExportText += exporter.exportOutputsFlowSolver(simulationUnit)
        fullExportText += exporter.exportPipeAndTeeTypesForTemp(simulationUnit+1)   # DC-ERROR
        fullExportText += exporter.exportPrintLoops()
        fullExportText += exporter.exportPrintPipeLoops()
        fullExportText += exporter.exportPrintPipeLosses()

        # unitnr should maybe be variable in exportData()

        fullExportText += exporter.exportMassFlowPrinter(self.printerUnitnr, 15)
        fullExportText += exporter.exportTempPrinter(self.printerUnitnr+1, 15)

        # tes = open(os.path.join(ddckFolder, "Tes\\Tes.ddck"), "r")
        # fullExportText += tes.read()
        # tes.close()
        if exportTo == 'mfs':
            fullExportText += "EQUATIONS 1\nTRoomStore=1\n"
            fullExportText += "ENDS"

        print("------------------------> END OF EXPORT <------------------------")

        if exportTo == 'mfs':
            f = open(str(exportPath), 'w')
            f.truncate(0)
            f.write(fullExportText)
            f.close()
        elif exportTo == 'hydraulics':
            if fullExportText[:1] == "\n":
                fullExportText = fullExportText[1:]
            f = open(str(hydraulicsPath), 'w')
            f.truncate(0)
            f.write(fullExportText)
            f.close()

        self.cleanUpExportedElements()
        self.tearDownStorageInnerConns()

        if exportTo == 'mfs':
            return exportPath
        elif exportTo == 'hydraulics':
            return hydraulicsPath

    def exportToHydraulics(self):
        self.setUpStorageInnerConns()
        self.sortTrnsysObj()

        fullExportText = ''
        exportPath = os.path.join(self.hydraulicFolder, self.diagramName + '_Hydraulic.dck')
        i = 1

        while(Path(exportPath).exists()):
            if Path(exportPath).exists():
                qmb = QMessageBox(self)
                qmb.setText("Warning: " +
                            "An export file of the same name already exists inside hydraulics. Do you want to overwrite or cancel?")
                qmb.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
                qmb.setDefaultButton(QMessageBox.Cancel)
                ret = qmb.exec()
                if ret == QMessageBox.Save:
                    self.canceled = False
                    self.fileList.remove(exportPath)
                    break
                else:
                    self.canceled = True
                    exportPath = os.path.join(self.hydraulicFolder, self.diagramName + '_Hydraulic(%i).dck' % i)
                    i += 1
            else:
                print("Exported to %s" % str(exportPath))

        print("Printing the TRNSYS file... \n")

        simulationUnit = 450
        simulationType = 935
        descConnLength = 20

        parameters = 0

        # This has to be changed
        for t in self.trnsysObj:
            if type(t) is StorageTank:
                continue
            if type(t) is Connection and (
                    type(t.fromPort.parent) is StorageTank or type(t.toPort.parent) is StorageTank):
                continue
            if type(t) is HeatPump:
                parameters += 2
                continue
            if type(t) is GenericBlock:
                parameters += len(t.inputs)
                continue
            if type(t) is ExternalHx:
                parameters += 2
                continue
            if type(t) is HeatPumpTwoHx:
                parameters += 3
                continue
            if type(t) is HPDoubleDual:
                parameters += 3
                continue

            parameters += 1

        lineNrParameters = parameters
        parameters = parameters * 4 + 1

        exporter = Export(self.trnsysObj, self)

        blackBoxProblem, blackBoxText = exporter.exportBlackBox()
        if blackBoxProblem:
            return
        fullExportText += blackBoxText
        fullExportText += exporter.exportPumpOutlets()
        # fullExportText += exporter.exportMassFlows()
        # fullExportText += exporter.exportDivSetting(simulationUnit - 10)

        fullExportText += exporter.exportParametersFlowSolver(simulationUnit, simulationType, descConnLength,
                                                              parameters, lineNrParameters)
        fullExportText += exporter.exportInputsFlowSolver(lineNrParameters)
        fullExportText += exporter.exportOutputsFlowSolver(simulationUnit)
        fullExportText += exporter.exportPipeAndTeeTypesForTemp(simulationUnit + 1)  # DC-ERROR

        fullExportText += exporter.exportPrintLoops()
        fullExportText += exporter.exportPrintPipeLoops()
        fullExportText += exporter.exportPrintPipeLosses()

        # unitnr should maybe be variable in exportData()

        fullExportText += exporter.exportMassFlowPrinter(self.printerUnitnr, 15)
        fullExportText += exporter.exportTempPrinter(self.printerUnitnr + 1, 15)

        print("------------------------> END OF EXPORT <------------------------")

        f = open(str(exportPath), 'w')
        f.truncate(0)
        f.write(fullExportText)
        f.close()

        self.cleanUpExportedElements()
        self.tearDownStorageInnerConns()
        self.fileList.append(exportPath)

    def exportToControl(self):
        self.setUpStorageInnerConns()
        self.sortTrnsysObj()

        fullExportText = ''
        exportPath = os.path.join(self.controlDirectory, self.diagramName + '_MasterControl.dck')
        i = 1

        while (Path(exportPath).exists()):
            if Path(exportPath).exists():
                qmb = QMessageBox(self)
                qmb.setText("Warning: " +
                            "An export file of the same name already exists inside Master control. Do you want to overwrite or cancel?")
                qmb.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
                qmb.setDefaultButton(QMessageBox.Cancel)
                ret = qmb.exec()
                if ret == QMessageBox.Save:
                    self.canceled = False
                    self.fileList.remove(exportPath)
                    break
                else:
                    self.canceled = True
                    exportPath = os.path.join(self.controlDirectory, self.diagramName + '_MasterControl(%i).dck' % i)
                    i += 1
            else:
                print("Exported to %s" % str(exportPath))

        print("Printing the TRNSYS file... \n")

        simulationUnit = 450

        parameters = 0

        # This has to be changed
        for t in self.trnsysObj:
            if type(t) is StorageTank:
                continue
            if type(t) is Connection and (
                    type(t.fromPort.parent) is StorageTank or type(t.toPort.parent) is StorageTank):
                continue
            if type(t) is HeatPump:
                parameters += 2
                continue
            if type(t) is GenericBlock:
                parameters += len(t.inputs)
                continue
            if type(t) is ExternalHx:
                parameters += 2
                continue
            if type(t) is HeatPumpTwoHx:
                parameters += 3
                continue
            if type(t) is HPDoubleDual:
                parameters += 3
                continue

            parameters += 1

        exporter = Export(self.trnsysObj, self)

        fullExportText += exporter.exportMassFlows()
        fullExportText += exporter.exportDivSetting(simulationUnit - 10)
        print("------------------------> END OF EXPORT <------------------------")

        f = open(str(exportPath), 'w')
        f.truncate(0)
        f.write(fullExportText)
        f.close()

        self.cleanUpExportedElements()
        self.tearDownStorageInnerConns()
        self.fileList.append(exportPath)


    def cleanUpExportedElements(self):
        for t in self.trnsysObj:
            # if isinstance(t, BlockItem):
            #     t.exportConnsString = ""
            #     t.exportInputName = "0"
            #     t.exportInitialInput = -1
            #     t.exportEquations = []
            #     t.trnsysConn = []
            #
            # if type(t) is Connection:
            #     t.exportConnsString = ""
            #     t.exportInputName = "0"
            #     t.exportInitialInput = -1
            #     t.exportEquations = []
            #     t.trnsysConn = []
            t.cleanUpAfterTrnsysExport()

    def sortTrnsysObj(self):
        res = self.trnsysObj.sort(key=self.sortId)
        for s in self.trnsysObj:
            print("s has tr id " + str(s.trnsysId) + " has dname " + s.displayName)

    def sortId(self, l1):
        """
        Sort function returning a sortable key
        Parameters
        ----------
        l1 : Block/Connection

        Returns
        -------

        """
        return l1.trnsysId



    def setName(self, newName):
        self.diagramName = newName

    def delBlocks(self):
        """
        Deletes the whole diagram

        Returns
        -------

        """
        while len(self.trnsysObj) > 0:
            print("In deleting...")
            self.trnsysObj[0].deleteBlock()

        while len(self.groupList) > 1:
            self.groupList[-1].deleteGroup()

        while len(self.graphicalObj) > 0:
            self.graphicalObj[0].deleteBlock()

        print("Groups are " + str(self.groupList))

    def newDiagram(self):
        self.centralWidget.delBlocks()

        # global id
        # global trnsysID
        # global globalConnID

        # self.id = 0
        # self.trnsysID = 0
        # self.globalConnID = 0

        self.idGen.reset()
        # newDiagramDlg(self)
        self.showNewDiagramDlg()


    # Encoding / decoding
    def encode(self, filename, encodeList):
        """
        Encoding function. Not used. encodeDiagram is used instead
        Parameters
        ----------
        filename : str
        encodeList : :obj:`list` of :obj:`BlockItem` and :obj:`Connection`

        Returns
        -------

        """
        with open(filename, 'w') as jsonfile:
            json.dump(encodeList, jsonfile, indent=4, sort_keys=True, cls=DiagramEncoder)

    def encodeDiagram(self, filename):
        """
        Encodes the diagram to a json file.

        Parameters
        ----------
        filename : str

        Returns
        -------

        """
        print("filename is at encoder " + str(filename))
        # if filename != "":
        with open(filename, 'w') as jsonfile:
            json.dump(self, jsonfile, indent=4, sort_keys=True, cls=DiagramEncoder)

    def decodeDiagram(self, filename, loadValue='load'):
        """
        Decodes a diagram saved as a json-file. It also checks which folders exist in the ddck-directory of the pro-
        ject. It deletes all folders in the ddck-directory, which neither have a corresponding blockItem in the json-
        file nor are the generic, hydraulic, or a Tes-folder. Such folders are created when an item is dropped, but not
        saved in the diagram-json afterwards.

        Parameters
        ----------
        filename : str

        Returns
        -------

        """
        # try:
        #     with open(filename, 'r') as jsonfile:
        #         blocklist = json.load(jsonfile, cls=DiagramDecoder, editor=self)  # Working
        # except:
        #     print("No such file: " + filename)

        with open(filename, 'r') as jsonfile:
            blocklist = json.load(jsonfile, cls=DiagramDecoder, editor=self)

        if len(self.groupList) == 0:
            print("self.group is empty, adding default group")
            self.defaultGroup = Group(0, 0, 100, 100, self.diagramScene)
            self.defaultGroup.setName("defaultGroup")

        blockFolderNames = []

        for j in blocklist["Blocks"]:
            # print("J is " + str(j))

            for k in j:
                if isinstance(k, BlockItem):
                    k.setParent(self.diagramView)
                    k.changeSize()
                    self.diagramScene.addItem(k)
                    blockFolderNames.append(k.displayName)
                    # blockFolderNames.append(k.name + '_' + k.displayName)
                    # k.setBlockToGroup("defaultGroup")

                if isinstance(k, StorageTank):
                    print("Loading a Storage")
                    k.setParent(self.diagramView)
                    k.updateImage()
                    # k.setBlockToGroup("defaultGroup")
                    for hx in k.heatExchangers:
                        hx.initLoad()

                    # print("Printing storage tank" + str(k))

                if isinstance(k, Connection):
                    if k.toPort == None or k.fromPort == None:
                        continue
                    # name = k.displayName
                    # testFrom = k.fromPort
                    # testTo = k.toPort
                    print("Almost done with loading a connection")
                    # print("Connection displ name " + str(k.displayName))
                    # print("Connection fromPort" + str(k.fromPort))
                    # print("Connection toPort" + str(k.toPort))
                    # print("Connection from " + k.fromPort.parent.displayName + " to " + k.toPort.parent.displayName)
                    k.initLoad()
                    a = 1
                    # k.setConnToGroup("defaultGroup")

                if isinstance(k, GraphicalItem):
                    k.setParent(self.diagramView)
                    self.diagramScene.addItem(k)
                    # k.resizer.setPos(k.w, k.h)
                    # k.resizer.itemChange(k.resizer.ItemPositionChange, k.resizer.pos())

                if isinstance(k, dict):
                    if "__idDct__" in k:
                        # here we don't set the ids because the copyGroup would need access to idGen
                        print("Found the id dict while loading, not setting the ids")
                        # global globalID
                        # global trnsysID
                        # global globalConnID

                        self.idGen.setID(k["GlobalId"])
                        self.idGen.setTrnsysID(k["trnsysID"])
                        self.idGen.setConnID(k["globalConnID"])
                        # self.idGen.setBlockID()

                    if "__nameDct__" in k:
                        print("Found the name dict while loading")
                        if loadValue == 'load':
                            self.diagramName = k["DiagramName"]
                            self.projectFolder = k["ProjectFolder"]

        blockFolderNames.append('generic')
        blockFolderNames.append('hydraulic')
        blockFolderNames.append('weather')
        blockFolderNames.append('control')

        ddckFolder = os.path.join(self.projectFolder,'ddck')
        ddckFolders = os.listdir(ddckFolder)
        additionalFolders = []

        for folder in ddckFolders:
            if folder not in blockFolderNames and 'StorageTank' not in folder:
                additionalFolders.append(folder)

        if len(additionalFolders) > 0:
            warnBox = QMessageBox()
            warnBox.setWindowTitle("Additional ddck-folders")

            if len(additionalFolders) == 1:
                text = "The following ddck-folder does not have a corresponding component in the diagram:"
            else:
                text = "The following ddck-folders do not have a corresponding component in the diagram:"

            for folder in additionalFolders:
                text += "\n\t" + folder

            warnBox.setText(text)
            warnBox.setStandardButtons(QMessageBox.Ok)
            warnBox.setDefaultButton(QMessageBox.Ok)
            warnBox.exec()

        for t in self.trnsysObj:
            print("Tr obj is" + str(t) + " " + str(t.trnsysId))
            if hasattr(t, "isTempering"):
                print("tv has " +str(t.isTempering))
        # tempList = []

    def exportSvg(self):
        """
        For exporting a svg file (text is still too large)
        Returns
        -------

        """
        generator = QSvgGenerator()
        generator.setResolution(300)
        generator.setSize(QSize(self.diagramScene.width(), self.diagramScene.height()))
        # generator.setViewBox(QRect(0, 0, 800, 800))
        generator.setViewBox(self.diagramScene.sceneRect())
        generator.setFileName("VectorGraphicsExport.svg")

        painter = QPainter()
        painter.begin(generator)
        painter.setRenderHint(QPainter.Antialiasing)
        self.diagramScene.render(painter)
        painter.end()

    def copyElements(self):
        """
        Copies elements
        Returns
        -------

        """
        clipboardGroup = copyGroup(self)
        print(self.diagramScene.elementsInRect())

        for t in self.diagramScene.elementsInRect():
            print("element in rect is" + str(t))
            clipboardGroup.trnsysObj.append(t)

        self.saveToClipBoard(clipboardGroup)

    def saveToClipBoard(self, copyList):
        filename = 'clipboard.json'

        with open(filename, 'w') as jsonfile:
            json.dump(copyList, jsonfile, indent=4, sort_keys=True, cls=DiagramEncoder)

        print("Copy complete!")

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

                if isinstance(k, GraphicalItem):
                    k.setParent(self.diagramView)
                    self.diagramScene.addItem(k)
                    # k.resizer.setPos(k.w, k.h)
                    # k.resizer.itemChange(k.resizer.ItemPositionChange, k.resizer.pos())

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
            if isinstance(t, GraphicalItem):
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


    # Saving related
    def save(self):
        """
        If saveas has not been used, diagram will be saved in "/diagrams"
        If saveas has been used, diagram will be saved in self.saveAsPath
        Returns
        -------

        """
        # print("saveaspath is " + str(self.saveAsPath))
        # if self.saveAsPath.name == '':

        # if getattr(sys, 'frozen', False):
        #     ROOT_DIR = os.path.dirname(sys.executable)
        # elif __file__:
        #     ROOT_DIR = os.path.dirname(__file__)
        # filepaths = os.path.join(ROOT_DIR, 'filepaths.txt')
        # print(ROOT_DIR, filepaths)
        # with open(filepaths, 'r') as file:
        #     data = file.readlines()

        self.diagramName = os.path.split(self.projectFolder)[-1] + '.json'
        diagramPath = os.path.join(self.projectFolder,self.diagramName)

        if os.path.isfile(diagramPath):
            qmb = QMessageBox(self)
            qmb.setText("Warning: " +
                        "This diagram name exists already. Do you want to overwrite or cancel?")
            qmb.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
            qmb.setDefaultButton(QMessageBox.Cancel)
            ret = qmb.exec()
            if ret == QMessageBox.Save:
                print("Overwriting")
                self.encodeDiagram(diagramPath)
                msgb = QMessageBox(self)
                msgb.setText("Saved diagram at " + diagramPath)
                msgb.exec()

            else:
                print("Canceling")
        else:
            self.encodeDiagram(diagramPath)
            msgb = QMessageBox(self)
            msgb.setText("Saved diagram at " + diagramPath)
            msgb.exec()


                # self.encodeDiagram(str(filepath.joinpath(self.diagramName + '.json')))
                # msgb = QMessageBox(self)
                # msgb.setText("Saved diagram at /trnsysGUI/diagrams/")
                # msgb.exec()
        # else:
        #     if self.saveAsPath.exists():
        #         pass
        #     else:
        #         self.encodeDiagram(str(self.saveAsPath))
        #         msgb = QMessageBox(self)
        #         msgb.setText("Saved diagram at" + str(self.saveAsPath))
        #         msgb.exec()

    def saveAs(self):
        if getattr(sys, 'frozen', False):
            ROOT_DIR = os.path.dirname(sys.executable)
        elif __file__:
            ROOT_DIR = os.path.dirname(__file__)
        filepaths = os.path.join(ROOT_DIR, 'filepaths.txt')
        with open(filepaths, 'r') as file:
            data = file.readlines()
        defaultDir = (data[1][:-1])
        pickedPath = Path(QFileDialog.getSaveFileName(self, "Save diagram", defaultDir, filter="*.json")[0])
        if str(pickedPath) == ".":
            msgb = QMessageBox(self)
            msgb.setText("No valid path selected, aborting save as")
            msgb.exec()
            return
        # print("picked path is" + str(pickedPath))

        self.saveAsPath = pickedPath
        self.diagramName = self.saveAsPath.stem
        # print(self.saveAsPath)
        # print(self.diagramName)

        self.encodeDiagram(str(self.saveAsPath))

    def saveToProject(self):
        projectPath = self.projectPath

    def renameDiagram(self, newName):
        """

        Parameters
        ----------
        newName

        Returns
        -------

        """

        if self.saveAsPath.name != '':
            # print("Path name is " + self.saveAsPath.name)
            if newName + ".json" in self.saveAsPath.glob("*"):
                QMessageBox(self, "Warning", "This diagram name exists already in the directory."
                                             " Please rename this diagram")
            else:
                self.saveAsPath = Path(self.saveAsPath.stem[0:self.saveAsPath.name.index(self.diagramName)] + newName)

        self.diagramName = newName
        self.parent().currentFile = newName
        # fromPath = self.projectFolder
        # destPath = os.path.dirname(__file__)
        # destPath = os.path.join(destPath, 'default')
        # destPath = os.path.join(destPath, newName)
        # os.rename(fromPath, destPath)

        # print("Path is now: " + str(self.saveAsPath))
        # print("Diagram name is: " + self.diagramName)

    def saveAtClose(self):
        print("saveaspath is " + str(self.saveAsPath))


        # closeDialog = closeDlg()
        # if closeDialog.closeBool:
        filepath = Path(Path(__file__).resolve().parent.joinpath("recent"))
        self.encodeDiagram(str(filepath.joinpath(self.diagramName + '.json')))




    # Mode related
    def setAlignMode(self, b):
        self.alignMode = True

    def setEditorMode(self, b):
        self.editorMode = b

    def setMoveDirectPorts(self, b):
        """
        Sets the bool moveDirectPorts. When mouse released in diagramScene, moveDirectPorts is set to False again
        Parameters
        ----------
        b : bool

        Returns
        -------

        """
        self.moveDirectPorts = b

    def setSnapGrid(self, b):
        self.snapGrid = b

    def setSnapSize(self, s):
        self.snapSize = s

    def setitemsSelected(self, b):
        self.itemsSelected = b



    # Misc
    def editGroups(self):
        self.showGroupsEditor()

    def setConnLabelVis(self, b):
        for c in self.trnsysObj:
            if isinstance(c, Connection) and not c.isVirtualConn:
                c.showLabel(b)
            if isinstance(c, BlockItem):
                c.label.setVisible(b)
            if isinstance(c, TVentil):
                c.posLabel.setVisible(b)
        # Faster alternative, untested
        # for c in self.connectionList:
        #     if not c.isVirtualConn:
        #         c.showLabel(b)

    def updateConnGrads(self):
        for t in self.trnsysObj:
            if isinstance(t, Connection):
                t.updateSegGrads()

    def findGroupByName(self, name):
        for g in self.groupList:
            if g.displayName == name:
                return g

        return None


    # Dialog calls
    def showBlockDlg(self, bl):
        c = BlockDlg(bl, self)

    def showPumpDlg(self, bl):
        c = PumpDlg(bl, self)

    def showDiagramDlg(self):
        c = diagramDlg(self)

    def showGenericPortPairDlg(self, bl):
        c = GenericPortPairDlg(bl, self)

    def showGroupChooserBlockDlg(self, bl):
        c = GroupChooserBlockDlg(bl, self)

    def showGroupChooserConnDlg(self, conn):
        c = GroupChooserConnDlg(conn, self)
    
    def showGroupDlg(self, group, itemList):
        c = groupDlg(group, self, itemList)

    def showHxDlg(self, hx):
        c = hxDlg(hx, self)

    def showNewDiagramDlg(self):
        c = newDiagramDlg(self)

    # Not used
    # def showNewPortDlg(self):
    #     c = newPortDlg

    def showSegmentDlg(self, seg):
        c = segmentDlg(seg, self)

    def showTVentilDlg(self, bl):
        c = TVentilDlg(bl, self)

    def showConfigStorageDlg(self, bl):
        c = ConfigStorage(bl, self)

    def showGroupsEditor(self):
        c = groupsEditor(self)

    def testFunctionInspection(self, *args):
        print("Ok, here is my log")
        print(int(args[0])+1)
        if len(self.connectionList) > 0:
            self.connectionList[0].highlightConn()

    def getConnection(self, n):
        return self.connectionList[int(n)]

    # Unused
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

    def setTrnsysIdBack(self):
        self.idGen.trnsysID = max(t.trnsysId for t in self.trnsysObj)

    def findStorageCorrespPorts1(self, portList):
        """
        This function gets the ports on the other side of pipes connected to a port of the StorageTank. Unused

        Parameters
        ----------
        portList : :obj:`List` of :obj:`PortItems`

        Returns
        -------

        """

        res = []
        # print("Finding c ports")
        for p in portList:
            if len(p.connectionList) > 0:           # check if not >1 needed
                # connectionList[0] is the hidden connection created when the portPair is
                i = 0
                # while type(p.connectionList[i].fromPort.parent) is StorageTank and type(p.connectionList[i].toPort.parent) is StorageTank:
                while (p.connectionList[i].fromPort.parent) == (p.connectionList[i].toPort.parent):
                    i += 1
                if len(p.connectionList) >= i+1:
                    if p.connectionList[i].fromPort is p:
                        res.append(p.connectionList[i].toPort)
                    elif p.connectionList[i].toPort is p:
                        res.append(p.connectionList[i].fromPort)
                    else:
                        print("Port is not fromPort nor toPort")

        # [print(p.parent.displayName) for p in res]
        return res

    # Graph searach related methods, unused
    def bfs_b(self):
        self.bfs(self.connectionList[0].fromPort)
        # self.dfs1(self.connectionList[0].fromPort, 8, 0)
        # print(self.dfs2(self.connectionList[0].fromPort, 8, 0))

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

    def delGroup(self):
        """
        This is used for deleting the first connected componts group found by BFS, unused
        Returns
        -------

        """
        for bl in self.blockList:
            bl.deleteBlock()

    def testFunction(self):
        """
        This function tests whether the exporting function is working correctly by comparing
        an exported file to a reference file.
        Warning message will be shown if any difference is found between the files.
        -------
        Things to note : The fileDir must be changed to corresponding directories on the PC

        """

        i = 0
        self.tester = Test_Export()
        self.testPassed = True
        msg = QMessageBox(self)
        msg.setWindowTitle('Test Result')
        # fileDir = 'U:/Desktop/TrnsysGUI/trnsysGUI/'
        # examplesFilePath = fileDir + 'examplesNewEncoding/'
        # exportedFilePath = fileDir + 'export_test/'
        # originalFilePath = fileDir + 'Reference/'

        if getattr(sys, 'frozen', False):
            ROOT_DIR = os.path.dirname(sys.executable)
        elif __file__:
            ROOT_DIR = os.path.dirname(__file__)  # This is your Project Root
        examplesFilePath = os.path.join(ROOT_DIR, 'examples')
        exportedFilePath = os.path.join(ROOT_DIR, 'export_test')
        originalFilePath = os.path.join(ROOT_DIR, 'Reference')

        exportedFileList = []
        originalFileList = []
        exampleFileList = []

        errorList1 = []
        errorLIst2 = []

        fileNoList = []



        msg.setText("Test in progress")
        msg.show()

        QCoreApplication.processEvents()

        # Clear the window
        # self.delBlocks()

        # open, decode and export every example file

        self.testEnabled = True
        for files in os.listdir(examplesFilePath):
            fileName = os.path.join(examplesFilePath, files)
            exampleFileList.append(fileName)
            self.decodeDiagram(fileName)
            # Export example files
            self.exportData()
            self.delBlocks()
        self.testEnabled = False

        # get all files from exportedFile folder and Original folder
        self.tester.retrieveFiles(exportedFilePath, originalFilePath, exportedFileList,
                                  originalFileList)

        # check if exported files exist inside reference folder
        j = 0
        while j < len(exportedFileList):
            if not self.tester.checkFileExists(exportedFileList[j], originalFileList):
                self.existReference = False
                testDlg = TestDlg(exportedFileList[j])
                if testDlg.exportBool:
                    self.delBlocks()
                    self.decodeDiagram(exampleFileList[j])
                    self.exportData()
                    self.delBlocks()
                self.existReference = True
            j += 1

        # Retrieve newly added files if any
        self.tester.retrieveFiles(exportedFilePath, originalFilePath, exportedFileList,
                                  originalFileList)

        # check if the files are identical
        fileNoList, self.testPassed = self.tester.checkFiles(exportedFileList, originalFileList)
        # i, self.testPassed = self.tester.checkFiles(exportedFileList, originalFileList)

        if self.testPassed:
            msg.setText("All files tested, no discrepancy found")
            msg.exec_()
        else:
            for fileNo in fileNoList:
                errorFile = originalFileList[fileNo]
                errorList1, errorList2 = self.tester.showDifference(exportedFileList[fileNo], originalFileList[fileNo])
                msg.setText("%d files tested, discrepancy found in %s" % ((fileNo + 1), errorFile))
                msg.exec_()
                DifferenceDlg(self, errorList1, errorList2, originalFileList[fileNo])
            # errorFile = originalFileList[i]
            # errorList1, errorList2 = self.tester.showDifference(exportedFileList[i], originalFileList[i])
            # msg.setText("%d files tested, discrepancy found in %s" % ((i + 1), errorFile))
            # msg.exec_()
            # DifferenceDlg(self, errorList1, errorList2)

        # Disable test and delete the exported files
        self.tester.deleteFiles(exportedFilePath)

    def printPDF(self):
        """
            ---------------------------------------------
            Export diagram as pdf onto specified folder
            fn = user input directory
            ---------------------------------------------
        """
        fn, _ = QFileDialog.getSaveFileName(self, 'Export PDF', None, 'PDF files (.pdf);;All Files()')
        if fn != '':
            if QFileInfo(fn).suffix() == "": fn += '.pdf'
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOrientation(QPrinter.Landscape)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(fn)
            painter = QPainter(printer)
            self.diagramScene.render(painter)
            painter.end()
            print("File exported to %s" % fn)

    def setProjectPath(self):
        """
        This method is called when the 'Set Path' button for the file explorers is clicked.
        It sets the project path to the one defined by the user and updates the root path of every
        item inside the main window.
        If the path defined by the user doesn't exist. Creates that path.
        """
        self.projectPath = str(QFileDialog.getExistingDirectory(self, "Select Project Path"))
        if self.projectPath !='':
            self.PPL.setText(self.projectPath)
            # self.addButton.setEnabled(True)
            # self.delButton.setEnabled(True)

            loadPath = os.path.join(self.projectPath, 'ddck')
            if not os.path.exists(loadPath):
                os.makedirs(loadPath)

            self.createConfigBrowser(self.projectPath)
            self.copyGenericFolder(self.projectPath)
            self.createHydraulicDir(self.projectPath)
            self.createWeatherAndControlDirs(self.projectPath)
            self.createDdckTree(loadPath)

            for o in self.trnsysObj:
                if hasattr(o, 'updateTreePath'):
                    o.updateTreePath(self.projectPath)
                elif hasattr(o, 'createControlDir'):
                    o.createControlDir()

    # def openFile(self):
    #     print("Opening diagram")
    #     # self.centralWidget.delBlocks()
    #     fileName = QFileDialog.getOpenFileName(self, "Open diagram", "examples", filter="*.json")[0]
    #     print(fileName)
    #     try:
    #         self.statusBar().removeWidget(self.fileNameDisplay)
    #     except:
    #         pass
    #     self.fileNameDisplay = QLabel("Opened from " + fileName)
    #     self.statusBar().addWidget(self.fileNameDisplay)
    #     if fileName != '':
    #         self.centralWidget.idGen.reset()
    #         self.currentFile = fileName
    #         self.centralWidget.delBlocks()
    #         self.centralWidget.decodeDiagram(fileName)
    #     else:
    #         print("No filename chosen")
    #     try:
    #         self.exportedTo
    #     except AttributeError:
    #         pass
    #     else:
    #         del self.exportedTo

    def openProject(self):
        self.projectPath = str(QFileDialog.getExistingDirectory(self, "Select Project Path"))
        if self.projectPath !='':

            test = self.parent()

            self.parent().newDia()
            self.PPL.setText(self.projectPath)
            loadPath = os.path.join(self.projectPath, 'ddck')

            self.createConfigBrowser(self.projectPath)
            self.copyGenericFolder(self.projectPath)
            self.createHydraulicDir(self.projectPath)
            self.createWeatherAndControlDirs(self.projectPath)
            self.createDdckTree(loadPath)
            # todo : open diagram
            # todo : add files into list

    def createDdckTree(self, loadPath):
        treeToRemove = self.findChild(QTreeView, 'ddck')
        try:
            # treeToRemove.hide()
            treeToRemove.deleteLater()
        except AttributeError:
            print("Widget doesnt exist!")
        else:
            print("Deleted widget")
        if self.projectPath == '':
            loadPath = os.path.join(loadPath, 'ddck')
        if not os.path.exists(loadPath):
            os.makedirs(loadPath)
        self.model = MyQFileSystemModel()
        self.model.setRootPath(loadPath)
        self.model.setName('ddck')
        self.tree = MyQTreeView(self.model, self)
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(loadPath))
        self.tree.setObjectName("ddck")
        self.tree.setMinimumHeight(600)
        self.tree.setSortingEnabled(True)
        self.splitter.insertWidget(0, self.tree)

    def createConfigBrowser(self, loadPath):
        self.layoutToRemove = self.findChild(QHBoxLayout, 'Config_Layout')
        try:
            # treeToRemove.hide()
            self.layoutToRemove.deleteLater()
        except AttributeError:
            print("Widget doesnt exist!")
        else:
            print("Deleted widget")
        configPath = os.path.dirname(__file__)
        configPath = os.path.join(configPath, 'project')
        configPath = os.path.join(configPath, 'keepMe')
        self.emptyConfig = os.path.join(configPath, 'run.config')
        # projectPath = os.path.join(configPath, self.date_time)
        shutil.copy(self.emptyConfig, loadPath)
        self.HBox = QHBoxLayout()
        self.refreshButton = QPushButton(self)
        self.refreshButton.setIcon(QIcon('images/rotate-to-right.png'))
        self.refreshButton.clicked.connect(self.refreshConfig)
        self.model = MyQFileSystemModel()
        self.model.setRootPath(loadPath)
        self.model.setName('Config File')
        self.model.setFilter(QDir.Files)
        self.tree = MyQTreeView(self.model, self)
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(loadPath))
        self.tree.setObjectName("config")
        self.tree.setFixedHeight(60)
        self.tree.setSortingEnabled(False)
        self.HBox.addWidget(self.refreshButton)
        self.HBox.addWidget(self.tree)
        self.HBox.setObjectName("Config_Layout")
        self.fileBrowserLayout.addLayout(self.HBox)
        print(self.emptyConfig)

    # def createProjectFolder(self):
    #     self.date_time = datetime.now().strftime("%Y%m%d%H%M%S")
    #     projectPath = os.path.dirname(__file__).replace('/','\\')
    #     projectPath = os.path.join(projectPath, 'project')
    #     projectPath = os.path.join(projectPath, self.date_time)
    #     if not os.path.exists(projectPath):
    #         os.makedirs(projectPath)
    #     return projectPath

    def createProjectFolder(self):
        if not os.path.exists(self.projectFolder):
            os.makedirs(self.projectFolder)

    def refreshConfig(self):
        # configPath = os.path.dirname(__file__)
        # configPath = os.path.join(configPath, 'project')
        # configPath = os.path.join(configPath, self.date_time)
        # emptyConfig = os.path.join(configPath, 'run.config')
        if self.projectPath == '':
            localPath = self.projectFolder
        else:
            localPath = self.projectPath

        self.configToEdit = os.path.join(localPath, 'run.config')
        os.remove(self.configToEdit)
        shutil.copy(self.emptyConfig, localPath)
        self.configToEdit = os.path.join(localPath, 'run.config')

        localDdckPath = os.path.join(localPath, "ddck")
        with open(self.configToEdit, 'r') as file:
            lines = file.readlines()
        localPathStr = "string LOCAL$ %s" % str(localDdckPath)
        # localPathStr.replace('/', '\\')
        lines[21] = localPathStr + '\n'

        with open(self.configToEdit, 'w') as file:
            file.writelines(lines)

        # print(localPathStr)
        self.userInputList()

    def userInputList(self):
        print(self.fileList)
        dia = FileOrderingDialog(self.fileList, self)

    def copyGenericFolder(self, loadPath):

        genericPath = os.path.dirname(__file__)
        genericPath = os.path.join(genericPath, 'project')
        genericPath = os.path.join(genericPath, 'keepMe')
        genericPath = os.path.join(genericPath, 'generic')
        self.headerFile = os.path.join(genericPath, 'head.ddck')
        self.endFile = os.path.join(genericPath, 'end.ddck')

        self.genericFolder = os.path.join(loadPath, 'ddck')
        self.genericFolder = os.path.join(self.genericFolder, 'generic')

        if not os.path.exists(self.genericFolder):
            os.makedirs(self.genericFolder)

        shutil.copy(self.headerFile, self.genericFolder)
        shutil.copy(self.endFile, self.genericFolder)

    def createHydraulicDir(self, projectPath):

        self.hydraulicFolder = os.path.join(projectPath, 'ddck')
        self.hydraulicFolder = os.path.join(self.hydraulicFolder, 'hydraulic')

        if not os.path.exists(self.hydraulicFolder):
            os.makedirs(self.hydraulicFolder)

    def createWeatherAndControlDirs(self,projectPath):

        ddckFolder = os.path.join(projectPath, 'ddck')
        weatherFolder = os.path.join(ddckFolder, 'weather')
        controlFolder = os.path.join(ddckFolder, 'control')

        if not os.path.exists(weatherFolder):
            os.makedirs(weatherFolder)

        if not os.path.exists(controlFolder):
            os.makedirs(controlFolder)

    # def addFile(self):
    #     fileName = QFileDialog.getOpenFileName(self, "Load file", filter="*.ddck")[0]
    #     simpFileName = fileName.split('/')[-1]
    #     loadPath = os.path.join(self.projectPath, 'ddck')
    #     loadPath = os.path.join(loadPath, simpFileName)
    #     if fileName != '':
    #         print("file loaded into %s" % loadPath)
    #         if Path(loadPath).exists():
    #             qmb = QMessageBox()
    #             qmb.setText("Warning: " +
    #                         "A file with the same name exists already. Do you want to overwrite or cancel?")
    #             qmb.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
    #             qmb.setDefaultButton(QMessageBox.Cancel)
    #             ret = qmb.exec()
    #             if ret == QMessageBox.Save:
    #                 print("Overwriting")
    #                 # continue
    #             else:
    #                 print("Canceling")
    #                 return
    #         shutil.copy(fileName, loadPath)
    # def printEMF(self):
    #     """
    #                 ---------------------------------------------
    #                 Export diagram as EMF onto specified folder
    #                 fn = user input directory
    #                 ---------------------------------------------
    #             """
    #     fn, _ = QFileDialog.getSaveFileName(self, 'Export EMF', None, 'EMF files (.emf);;All Files()')
    #     if fn != '':
    #         if QFileInfo(fn).suffix() == "": fn += '.jpg'
    #         printer = QPrinter(QPrinter.HighResolution)
    #         printer.setOrientation(QPrinter.Landscape)
    #         printer.setOutputFormat(QPrinter.PdfFormat)
    #         printer.setOutputFileName(fn)
    #         painter = QPainter(printer)
    #         self.diagramScene.render(painter)
    #         painter.end()
    #         print("File exported to %s" % fn)




class MainWindow(QMainWindow):
    """
    This is the class containing the entire GUI window

    It has a menubar, a central widget and a message bar at the bottom. The central widget is
    the QWidget subclass containing the items library, the diagram editor and the element inspector
    listview.

    QActions comprise an icon (optionally), a description (tool tip) and the parent widget
    They are connected to a method via the Signals-and-Slots framework, allowing the execution of functions by an event.
    Shortcuts can be assigned to QActions.
    They get included into the application either by being added to a menu or a tool bar.

    Attributes
    ----------
    loadValue : str
        Indicates whether a new project was created, an old one loaded or the process was cancelled
    centralWidget : DiagramEditor

    labelVisState : bool

    massFlowEnabled : bool

    calledByVisualizeMf : bool

    currentFile : str
        Probably obsolete (NEM 07.10.2020)
    fileMenu : QMenu

    editMenu : QMenu

    helpMenu : QMenu

    """

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.loadValue = ''

        qmb = newOrLoadWindow(self)
        qmb.setText("Do you want to start a new project or open an existing one?")
        ret = qmb.exec()

        if ret == 1:
            self.loadDialogue()
            if self.loadValue == 'json':
                ret = 0
            elif self.loadValue == 'cancel':
                ret = 2

        if ret == 0:
            if self.loadValue != 'json':
                self.loadValue = 'new'
            pathDialog = FolderSetUp(self)
            self.projectFolder = pathDialog.projectFolder

        if ret == 2:
            self.loadValue = 'cancel'

        self.centralWidget = DiagramEditor(self)
        self.setCentralWidget(self.centralWidget)
        if self.loadValue == 'json':
            self.centralWidget.save()
        self.labelVisState = False
        self.massFlowEnabled = False
        self.calledByVisualizeMf = False
        self.currentFile = 'Untitled'

        # Toolbar actions
        saveDiaAction = QAction(QIcon('images/inbox.png'), "Save", self)
        saveDiaAction.triggered.connect(self.saveDia)

        loadDiaAction = QAction(QIcon('images/outbox.png'), "Open", self)
        loadDiaAction.triggered.connect(self.loadDia)

        # exportTrnsysAction = QAction(QIcon('images/font-file.png'), "Export trnsys file", self)
        # exportTrnsysAction.triggered.connect(self.exportTrnsys)

        updateConfigAction = QAction(QIcon('images/updateConfig.png'), "Update run.config", self)
        updateConfigAction.triggered.connect(self.updateRun)

        runSimulationAction = QAction(QIcon('images/runSimulation.png'), "Run simulation", self)
        runSimulationAction.triggered.connect(self.runSimulation)

        processSimulationAction = QAction(QIcon('images/processSimulation.png'), "Process data", self)
        processSimulationAction.triggered.connect(self.processSimulation)

        # renameDiaAction = QAction(QIcon('images/text-label.png'), "Rename system diagram", self)
        # renameDiaAction.triggered.connect(self.renameDia)

        deleteDiaAction = QAction(QIcon('images/trash.png'), "Delete diagram", self)
        deleteDiaAction.triggered.connect(self.deleteDia)

        # groupNewAction = QAction(QIcon('images/add-square.png'), "Create Group", self)
        # groupNewAction.triggered.connect(self.createGroup)

        # autoArrangeAction = QAction(QIcon('images/site-map.png'), "Tidy up connections", self)
        # autoArrangeAction.triggered.connect(self.tidyUp)

        zoomInAction = QAction(QIcon('images/zoom-in.png'), "Zoom in", self)
        zoomInAction.triggered.connect(self.setZoomIn)

        zoomOutAction = QAction(QIcon('images/zoom-Out.png'), "Zoom out", self)
        zoomOutAction.triggered.connect(self.setZoomOut)

        # zoom0Action = QAction(QIcon('images/zoom-0.png'), "Reset zoom", self)
        # zoom0Action.triggered.connect(self.setZoom0)

        #copyAction = QAction(QIcon('images/clipboard.png'), "Copy to clipboard", self)
        #copyAction.triggered.connect(self.copySelection)
        #copyAction.setShortcut("Ctrl+c")

        #pasteAction = QAction(QIcon('images/puzzle-piece.png'), "Paste from clipboard", self)
        #pasteAction.triggered.connect(self.pasteSelection)
        #pasteAction.setShortcut("Ctrl+v")

        toggleConnLabels = QAction(QIcon('images/labelToggle.png'), "Toggle labels", self)
        toggleConnLabels.triggered.connect(self.toggleConnLabels)

        exportHydraulicsAction = QAction(QIcon('images/exportHydraulics.png'), "Export hydraulic.ddck", self)
        exportHydraulicsAction.triggered.connect(self.exportHydraulicsDdck)

        exportDckAction = QAction(QIcon('images/exportDck.png'), "Export dck", self)
        exportDckAction.triggered.connect(self.exportDck)

        editGroupsAction = QAction(QIcon('images/modal-list.png'), "Edit groups/loops", self)
        editGroupsAction.triggered.connect(self.editGroups)

        selectMultipleAction = QAction(QIcon('images/elastic.png'), "Select multiple items", self)
        selectMultipleAction.triggered.connect(self.createSelection)
        selectMultipleAction.setShortcut("s")

        #deleteShortcut = QtGui.QKeySequence("Delete, Backspace, Ctrl+d")
        #multipleDeleteAction = QAction("Delete selection", self)
        #multipleDeleteAction.triggered.connect(self.deleteMultiple)
        #multipleDeleteAction.setShortcuts(deleteShortcut)

        # toggleEditorModeAction = QAction("Toggle editor mode", self)
        # toggleEditorModeAction.triggered.connect(self.toggleEditorMode)
        # toggleEditorModeAction.setShortcut("m")

        toggleSnapAction = QAction("Toggle snap grid", self)
        toggleSnapAction.triggered.connect(self.toggleSnap)
        toggleSnapAction.setShortcut("a")

        toggleAlignModeAction = QAction("Toggle align mode", self)
        toggleAlignModeAction.triggered.connect(self.toggleAlignMode)
        toggleAlignModeAction.setShortcut("q")

        runMassflowSolverAction = QAction(QIcon('images/runMfs.png'), "Run the massflow solver", self)
        runMassflowSolverAction.triggered.connect(self.runAndVisMf)

        openVisualizerAction = QAction(QIcon('images/visMfs.png'), "Start visualization of mass flows", self)
        openVisualizerAction.triggered.connect(self.visualizeMf)

        # runMassflowSolverAction = QAction(QIcon('images/gear.png'), "Run the massflow solver", self)
        # runMassflowSolverAction.triggered.connect(self.runMassflowSolver)

        trnsysList = QAction(QIcon('images/bug-1.png'), "Print trnsysObj", self)
        trnsysList.triggered.connect(self.mb_debug)

        loadVisual = QAction(QIcon('images/hard-drive.png'), "Load MRF", self)
        loadVisual.triggered.connect(self.loadVisualization)

        #testAppAction = QAction("Test", self)
        #testAppAction.triggered.connect(self.testApp)
        #testAppAction.setShortcut("Ctrl+t")

        runAction = QAction(QIcon('images/rotate-to-right.png'), "Run", self)
        runAction.triggered.connect(self.runApp)

        # Tool bar
        tb = self.addToolBar('Main Toolbar...')
        tb.setObjectName('Toolbar')
        tb.addAction(saveDiaAction)
        tb.addAction(loadDiaAction)
        tb.addAction(zoomInAction)
        tb.addAction(zoomOutAction)
        tb.addAction(toggleConnLabels)
        tb.addAction(runMassflowSolverAction)
        tb.addAction(openVisualizerAction)
        tb.addAction(exportHydraulicsAction)
        tb.addAction(updateConfigAction)
        tb.addAction(exportDckAction)
        tb.addAction(runSimulationAction)
        tb.addAction(processSimulationAction)
        #tb.addAction(exportTrnsysAction)
        # tb.addAction(renameDiaAction)
        # tb.addAction(groupNewAction)
        # tb.addAction(autoArrangeAction)
        # tb.addAction(zoom0Action)
        # tb.addAction(copyAction)
        # tb.addAction(pasteAction)
        # tb.addAction(editGroupsAction)
        # tb.addAction(selectMultipleAction)
        #tb.addAction(runMassflowSolverAction)
        #tb.addAction(loadVisual)
        #tb.addAction(trnsysList)
        #tb.addAction(runAction)
        tb.addAction(deleteDiaAction)


        # Menu bar actions
        self.fileMenu = QMenu("File")

        fileMenuNewAction = QAction("New", self)
        fileMenuNewAction.triggered.connect(self.newDia)
        fileMenuNewAction.setShortcut("Ctrl+n")
        self.fileMenu.addAction(fileMenuNewAction)

        fileMenuOpenAction = QAction("Open", self)
        fileMenuOpenAction.triggered.connect(self.openFile)
        fileMenuOpenAction.setShortcut("Ctrl+o")
        self.fileMenu.addAction(fileMenuOpenAction)

        fileMenuSaveAction = QAction("Save", self)
        fileMenuSaveAction.triggered.connect(self.saveDia)
        fileMenuSaveAction.setShortcut("Ctrl+s")
        self.fileMenu.addAction(fileMenuSaveAction)

        fileMenuCopyToNewAction = QAction("Copy to new folder", self)
        fileMenuCopyToNewAction.triggered.connect(self.copyToNew)
        self.fileMenu.addAction(fileMenuCopyToNewAction)

        #fileMenuSaveAsAction = QAction("Save as", self)
        #fileMenuSaveAsAction.triggered.connect(self.saveDiaAs)
        #self.fileMenu.addAction(fileMenuSaveAsAction)

        #changeSettingsAction = QAction("Change settings", self)
        #changeSettingsAction.triggered.connect(self.changeSettings)
        #self.fileMenu.addAction(changeSettingsAction)

        exportAsPDF = QAction("Export as PDF", self)
        exportAsPDF.triggered.connect(self.exportPDF)
        exportAsPDF.setShortcut("Ctrl+e")
        self.fileMenu.addAction(exportAsPDF)

        # exportAsEMF = QAction("Export as EMF", self)
        # exportAsEMF.triggered.connect(self.exportEMF)
        # exportAsEMF.setShortcut("Ctrl+F")
        # self.fileMenu.addAction(exportAsEMF)

        #movePortAction = QAction("Move direct ports", self)
        #movePortAction.triggered.connect(self.movePorts)
        #movePortAction.setShortcut("ctrl+m")

        #setPathAction = QAction("Set Paths", self)
        #setPathAction.triggered.connect(self.setPaths)
        #self.fileMenu.addAction(setPathAction)

        debugConnections = QAction("Debug Conn", self)
        debugConnections.triggered.connect(self.debugConns)
        self.fileMenu.addAction(debugConnections)

        self.editMenu = QMenu("Edit")
        # self.editMenu.addAction(toggleEditorModeAction)
        #self.editMenu.addAction(multipleDeleteAction)
        self.editMenu.addAction(toggleSnapAction)
        self.editMenu.addAction(toggleAlignModeAction)
        #self.editMenu.addAction(movePortAction)
        #self.editMenu.addAction(copyAction)
        #self.editMenu.addAction(pasteAction)
        #self.editMenu.addAction(testAppAction)


        AboutAction = QAction("About", self)
        AboutAction.triggered.connect(self.showAbout)

        VersionAction = QAction("Version", self)
        VersionAction.triggered.connect(self.showVersion)

        CreditsAction = QAction("Credits", self)
        CreditsAction.triggered.connect(self.showCredits)

        self.helpMenu = QMenu("Help")
        self.helpMenu.addAction(AboutAction)
        self.helpMenu.addAction(VersionAction)
        self.helpMenu.addAction(CreditsAction)

        # Menu bar
        self.mb = self.menuBar()
        self.mb.addMenu(self.fileMenu)
        self.mb.addMenu(self.editMenu)
        self.mb.addMenu(self.helpMenu)
        self.mb.addSeparator()

        # Status bar
        self.sb = self.statusBar()
        self.sb.showMessage("Mode is " + str(self.centralWidget.editorMode))

        # QUndo framework
        self.undoStack = QUndoStack(self)
        undoAction = self.undoStack.createUndoAction(self, "Undo")
        undoAction.setShortcut("Ctrl+z")

        redoAction = self.undoStack.createRedoAction(self, "Redo")
        redoAction.setShortcut("Ctrl+y")

        self.editMenu.addAction(undoAction)
        self.editMenu.addAction(redoAction)


        # self.undowidget = QUndoView(self.undoStack, self)
        # self.undowidget.setMinimumSize(300, 100)

    def changeSettings(self):
        settingsDialog = settingsDlg(self)


        if ret == 1:
            self.projectFolder, projectFile = os.path.split(QFileDialog.getOpenFileName(self, "Open diagram", filter="*.json")[0].replace('/', '\\'))


    def loadDialogue(self):
        self.projectFolder, projectFile = os.path.split(QFileDialog.getOpenFileName(self, "Open diagram", filter="*.json")[0].replace('/', '\\'))

        properProjectCheck1 = os.path.split(self.projectFolder)[-1] == projectFile.replace('.json', '')
        properProjectCheck2 = 'ddck' in os.listdir(self.projectFolder)
        if properProjectCheck1 and properProjectCheck2:
            self.loadValue = 'load'
        else:
            projectMB = QMessageBox(self)
            projectMB.setText("The json you are opening does not have a proper project folder environment. Do you want to continue and create one?")
            projectMB.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
            projectMB.setDefaultButton(QMessageBox.Cancel)
            projectRet = projectMB.exec()

            if projectRet == QMessageBox.Cancel:
                self.loadValue = 'cancel'
            else:
                self.loadValue = 'json'
                self.jsonPath = os.path.join(self.projectFolder, projectFile)

    def newDia(self):
        qmb = QMessageBox()
        qmb.setText("Are you sure you want to start a new project? Unsaved progress on the current one will be lost.")
        qmb.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        qmb.setDefaultButton(QMessageBox.Cancel)
        ret = qmb.exec()
        if ret == QMessageBox.Yes:
            print("Initializing new project")

            self.loadValue = 'new'
            pathDialog = FolderSetUp(self)
            self.projectFolder = pathDialog.projectFolder

            self.centralWidget = DiagramEditor(self)
            self.setCentralWidget(self.centralWidget)
        else:
            print("Canceling")
            return

    def saveDia(self):
        print("Saving diagram")
        self.centralWidget.save()

    def copyToNew(self):
        print("Copying project to new folder")

        self.loadValue = 'copy'
        pathDialog = FolderSetUp(self)
        self.projectFolder = pathDialog.projectFolder

        shutil.copytree(self.centralWidget.projectFolder,self.projectFolder)

        jsonOld = os.path.split(self.centralWidget.projectFolder)[-1] + '.json'
        self.centralWidget.projectFolder = self.projectFolder
        jsonNew = os.path.split(self.projectFolder)[-1] + '.json'
        os.rename(os.path.join(self.projectFolder,jsonOld),os.path.join(self.projectFolder,jsonNew))

        self.centralWidget = DiagramEditor(self)
        self.setCentralWidget(self.centralWidget)

    def saveDiaAs(self):
        print("Saving diagram as...")
        self.centralWidget.saveAs()

    def loadDia(self):
        print("Loading diagram")
        self.openFile()

    def updateRun(self):
        print("Updating run.config")
        configPath = os.path.join(self.projectFolder, 'run.config')
        runConfig = configFile(configPath,self.centralWidget)
        runConfig.updateConfig()

    def runSimulation(self):
        ddckPath = os.path.join(self.projectFolder,"ddck")

        #   Check hydraulic.ddck
        hydraulicPath = os.path.join(ddckPath,"hydraulic\\hydraulic.ddck")
        if not os.path.isfile(hydraulicPath):
            self.exportHydraulicsDdck()
        infile = open(hydraulicPath, 'r')
        hydraulicLines = infile.readlines()
        blackBoxLines = []
        for i in range(len(hydraulicLines)):
            if "Black box component temperatures" in hydraulicLines[i]:
                j = i+1
                while hydraulicLines[j] != '\n':
                    blackBoxLines.append(hydraulicLines[j])
                    j +=1
                break
        messageText = "Is this correct?\n\n"
        for line in blackBoxLines:
            messageText += line
        qmb = QMessageBox()
        qmb.setText(messageText)
        qmb.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        qmb.setDefaultButton(QMessageBox.No)
        ret = qmb.exec()
        if ret == QMessageBox.No:
            qmb = QMessageBox()
            qmb.setText(
                "Please make sure the black box component temperatures are correct in hydraulic.ddck before starting a simluation.")
            qmb.setStandardButtons(QMessageBox.Ok)
            qmb.setDefaultButton(QMessageBox.Ok)
            qmb.exec()
            return

        #   Check ddcks of storage tanks
        storageWithoutFile = []
        for object in self.centralWidget.trnsysObj:
            if isinstance(object,StorageTank):
                storageTankFile = os.path.join(object.displayName,object.displayName + ".ddck")
                storageTankPath = os.path.join(ddckPath,storageTankFile)
                if not(os.path.isfile(storageTankPath)):
                    storageWithoutFile.append(object.displayName + "\n")

        if not(not(storageWithoutFile)):
            messageText = "The following storage tank(s) do(es) not have a corresponding ddck:\n\n"
            for storage in storageWithoutFile:
                messageText += storage
            messageText += "\nPlease make sure you that you export the ddck for every storage tank before starting a simulation."
            qmb = QMessageBox()
            qmb.setText(messageText)
            qmb.setStandardButtons(QMessageBox.Ok)
            qmb.setDefaultButton(QMessageBox.Ok)
            qmb.exec()
            return

        #   Update run.config
        self.updateRun()

        #   Start simulation
        runApp = RunMain()
        runApp.runAction(self.centralWidget.projectFolder)

        return

    def processSimulation(self):
        processPath = os.path.join(self.projectFolder, "process.config")
        if not os.path.isfile(processPath):
            messageText = "No such file:\n" + processPath
            qmb = QMessageBox()
            qmb.setText(messageText)
            qmb.setStandardButtons(QMessageBox.Ok)
            qmb.setDefaultButton(QMessageBox.Ok)
            qmb.exec()
            return
        processApp = ProcessMain()
        processApp.processAction(self.centralWidget.projectFolder)
        return

    def exportTrnsys(self):
        print("Exporting Trnsys file...")
        noErrorExists = self.debugConns()
        qmb = QMessageBox()

        ddckFolder = os.path.join(self.projectFolder, 'ddck')
        ddckFolders = os.listdir(ddckFolder)
        numberOfControlFolders = 0

        for folder in ddckFolders:
            if 'Control' in folder:
                controlFolder = os.path.join(ddckFolder,folder)
                numberOfControlFolders += 1

        controlMissing = True

        if numberOfControlFolders > 1:
            qmb.setText("A system can only have one control!")
            qmb.exec_()
            return
        elif numberOfControlFolders == 1:
            for file in os.listdir(controlFolder):
                if file.endswith('.ddck'):
                    controlMissing = False

        if controlMissing:
            qmb.setText("Please add a control-ddck before exporting!")
            qmb.exec_()
            return

        # if self.centralWidget.controlExists < 1:

        if not noErrorExists:
            qmb.setText("Ignore connection errors and continue with export?")
            qmb.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
            qmb.setDefaultButton(QMessageBox.Cancel)
            ret = qmb.exec()
            if ret == QMessageBox.Save:
                print("Overwriting")
                # continue
            else:
                print("Canceling")
                return
        self.centralWidget.exportData()
        #self.centralWidget.exportToHydraulics()
        #self.centralWidget.exportToControl()

    def renameDia(self):
        print("Renaming diagram...")
        # self.centralWidget.propertiesDlg()
        self.centralWidget.showDiagramDlg()

    def deleteDia(self):
        qmb = QMessageBox()
        qmb.setText("Are you sure you want to delete the diagram? (There is no possibility to \"undo\".)")
        qmb.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        qmb.setDefaultButton(QMessageBox.Cancel)
        ret = qmb.exec()
        if ret == QMessageBox.Yes:
            print("Deleting diagram")
            self.centralWidget.delBlocks()
        else:
            print("Canceling")
            return

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

        self.centralWidget.copyElements()

    def pasteSelection(self):
        print("Pasting selection")
        self.centralWidget.pasteFromClipBoard()
        # global copyMode
        self.centralWidget.copyMode = False

    def editGroups(self):
        self.centralWidget.editGroups()

    def mb_debug(self):
        pass
        # print(self.centralWidget.trnsysObj)
        # a = [int(s.id) for s in self.centralWidget.trnsysObj]
        # a.sort()
        # print(a)
        #
        # for s in self.centralWidget.trnsysObj:
        #     if s.id == 11:
        #         print("Duplicate id obj is " + str(s.displayName) + " " + str(s.id))
        #
        # for t in self.centralWidget.trnsysObj:
        #     t.alignMode = True
        #     print(t.alignMode)



        # temp = []
        # for t in self.centralWidget.trnsysObj:
        #     if isinstance(t, BlockItem):
        #         for p in t.inputs + t.outputs:
        #             if p not in temp:
        #                 temp.append(p)
        #
        # for p in temp:
        #     if p.isFromHx:
        #         print("Port with parent " + str(p.parent.displayName) + "is from Hx")
        #
        # res = True
        #
        # for b in self.centralWidget.trnsysObj:
        #     if isinstance(b, Connection) and b not in self.centralWidget.connectionList:
        #         res = False
        #
        # print("editor connectionList is consistent with trnsysObj: " + str(res))

        # dIns = DeepInspector(self.centralWidget)

    def runAndVisMf(self):
        self.calledByVisualizeMf = True
        mfrFile, tempFile = self.runMassflowSolver()
        if os.path.isfile(mfrFile) and os.path.isfile(tempFile):
            MassFlowVisualizer(self,mfrFile, tempFile)
            self.massFlowEnabled = True
        else:
            print("No mfrFile or tempFile found!")

    def visualizeMf(self):
        qmb = QMessageBox()
        qmb.setText("Please select the mass flow rate prt-file that you want to visualize.")
        qmb.setStandardButtons(QMessageBox.Ok)
        qmb.setDefaultButton(QMessageBox.Ok)
        qmb.exec()

        mfrFile = QFileDialog.getOpenFileName(self, "Open diagram", filter="*Mfr.prt")[0].replace('/', '\\')
        tempFile = mfrFile.replace("Mfr", "T")
        self.calledByVisualizeMf = True
        if os.path.isfile(mfrFile) and os.path.isfile(tempFile):
            MassFlowVisualizer(self,mfrFile, tempFile)
            self.massFlowEnabled = True
        else:
            print("No mfrFile or tempFile found!")

    def openFile(self):
        print("Opening diagram")
        qmb = QMessageBox()
        qmb.setText("Are you sure you want to open another project? Unsaved progress on the current one will be lost.")
        qmb.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        qmb.setDefaultButton(QMessageBox.Cancel)
        ret = qmb.exec()

        if ret == QMessageBox.Yes:
            self.loadDialogue()
            self.centralWidget.idGen.reset()
            self.centralWidget.delBlocks()

            if self.loadValue == 'json':
                pathDialog = FolderSetUp(self)
                self.projectFolder = pathDialog.projectFolder

            self.centralWidget = DiagramEditor(self)
            self.setCentralWidget(self.centralWidget)

            if self.loadValue == 'json':
                self.centralWidget.save()

            try:
                self.exportedTo
            except AttributeError:
                pass
            else:
                del self.exportedTo
        else:
            return




    def openFileAtStartUp(self):
        """
        Opens the most recently modified file from the recent folder

        Things to note : file directory must be changed to corresponding directory on individual PCs
        -------
        """

        print("Opening diagram")
        self.centralWidget.delBlocks()

        # list_of_files = glob.glob('U:/Desktop/TrnsysGUI/trnsysGUI/recent/*')

        if getattr(sys, 'frozen', False):
            ROOT_DIR = os.path.dirname(sys.executable)
        elif __file__:
            ROOT_DIR = os.path.dirname(__file__)
        filePath = os.path.join(ROOT_DIR, 'recent')
        filePath = os.path.join(filePath, '*')
        list_of_files = glob.glob(filePath)

        if len(list_of_files) != 0:
            latest_file = max(list_of_files, key=os.path.getmtime)
        else:
            latest_file = ''

        while len(list_of_files) > 10:
            list_of_files = glob.glob(filePath)
            try:
                fileToDelete = min(list_of_files, key=os.path.getmtime)
            except FileNotFoundError:
                print("File not found")
            else:
                os.remove(fileToDelete)

        try:
            latest_file
        except FileNotFoundError:
            print("File not found")
        else:
            if latest_file != '':
                self.currentFile = latest_file
                self.centralWidget.delBlocks()
                self.centralWidget.decodeDiagram(latest_file)
            else:
                print("No filename available")

    def toggleConnLabels(self):
        self.labelVisState = not self.labelVisState
        self.centralWidget.setConnLabelVis(self.labelVisState)

    def exportHydraulicsDdck(self):
        statusQuo = self.labelVisState
        if not statusQuo:
            self.toggleConnLabels()
        self.centralWidget.exportData(exportTo='hydraulics')
        if not statusQuo:
            self.toggleConnLabels()

    def exportDck(self):
        dckBuilder.buildDck(self.projectFolder)

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
        print("Child Items")
        print(self.centralWidget.selectionGroupList.childItems())

        for t in self.centralWidget.selectionGroupList.childItems():
            temp.append(t)
            self.centralWidget.selectionGroupList.removeFromGroup(t)

        for t in temp:
            if isinstance(t, BlockItem):
                t.deleteBlock()
            elif isinstance(t, Connection):
                t.deleteConn()
            elif isinstance(t, GraphicalItem):
                t.deleteBlock()
            else:
                print("Neiter a Block nor Connection in copyGroupList ")

    def runMassflowSolver(self):
        print("Running massflow solver...")

        exportPath = self.centralWidget.exportData(exportTo='mfs')
        self.exportedTo = exportPath
        print(exportPath)
        if exportPath != 'None':
            msgb = QMessageBox(self)
            if not os.path.isfile(self.centralWidget.trnsysPath):
                msgb.setText("TRNExe.exe not found!")
                msgb.exec()
                return 0, 0
            print("trnsyspath:", self.centralWidget.trnsysPath)
            cmd = self.centralWidget.trnsysPath + ' ' + str(exportPath) + r' /H'
            os.system(cmd)
            mfrFile = os.path.join(self.projectFolder, self.projectFolder.split("\\")[-1]  + '_Mfr.prt')
            tempFile = os.path.join(self.projectFolder, self.projectFolder.split("\\")[-1]  + '_T.prt')
            if not os.path.isfile(mfrFile) or not os.path.isfile(tempFile):
                msgb.setText("Execution of Trnsys NOT succesful")
                msgb.exec()
                del self.exportedTo
            else:
                if not self.calledByVisualizeMf:
                    msgb.setText("Execution of Trnsys succesful")
                    msgb.exec()
            self.calledByVisualizeMf = False
            return mfrFile, tempFile

    # def loadVisualization(self):
    #
    #     currentFilePath = self.currentFile
    #     if '\\' in currentFilePath:
    #         diaName = currentFilePath.split('\\')[-1][:-5]
    #     elif '/' in currentFilePath:
    #         diaName = currentFilePath.split('/')[-1][:-5]
    #     else:
    #         diaName = currentFilePath
    #     if getattr(sys, 'frozen', False):
    #         ROOT_DIR = os.path.dirname(sys.executable)
    #     elif __file__:
    #         ROOT_DIR = os.path.dirname(__file__)
    #
    #     filepaths = os.path.join(ROOT_DIR, 'filepaths')
    #     with open(filepaths, 'r') as file:
    #         data = file.readlines()
    #
    #     filePath = data[0][:-1]
    #     MfrFilePath = os.path.join(filePath, diaName + '_Mfr.prt')
    #     TempFilePath = os.path.join(filePath, diaName + '_T.prt')
    #     print(MfrFilePath, TempFilePath)
    #
    #     if os.path.exists(MfrFilePath) and os.path.exists(TempFilePath):
    #         MassFlowVisualizer(self, MfrFilePath, TempFilePath)
    #         self.massFlowEnabled = True
    #     else:
    #         msgb = QMessageBox(self)
    #         msgb.setText("MFR or Temperature file does not exist!")
    #         msgb.exec()

    def loadVisualization(self):
        MfrFile = QFileDialog.getOpenFileName(self, "Select Mfr File", "exports", filter="*_Mfr.prt")[0]
        if MfrFile == '':
            msgb = QMessageBox(self)
            msgb.setText("No Mfr file chosen!")
            msgb.exec()
            return
        TempFile = QFileDialog.getOpenFileName(self, "Select Temperature File", "exports", filter="*_T.prt")[0]
        if TempFile == '':
            msgb = QMessageBox(self)
            msgb.setText("No Temperature file chosen!")
            msgb.exec()
            return

        selectedMfrFileName = str(MfrFile).split("/")[-1][:-8]
        selectedTempFileName = str(TempFile).split("/")[-1][:-6]

        currentFilePath = self.currentFile
        if '\\' in currentFilePath:
            diaName = currentFilePath.split('\\')[-1][:-5]
        elif '/' in currentFilePath:
            diaName = currentFilePath.split('/')[-1][:-5]
        else:
            diaName = currentFilePath

        if selectedMfrFileName == selectedTempFileName == diaName:
            MassFlowVisualizer(self, MfrFile, TempFile)
            self.massFlowEnabled = True
        else:
            print(selectedMfrFileName, selectedTempFileName, diaName)
            msgb = QMessageBox(self)
            msgb.setText("MFR or Temperature file does not correspond to current diagram!")
            msgb.exec()



    def movePorts(self):
        self.centralWidget.moveDirectPorts = True

    def mouseMoveEvent(self, e):
        pass
        # x = e.x()
        # y = e.y()
        #
        # text = "x: {0},  y: {1}".format(x, y)
        # self.sb.showMessage(text)
        # #print("event")

    def showAbout(self):
        msgb = QMessageBox(self)
        msgb.setText("PyQt based diagram editor coupled to Trnsys functions")
        msgb.exec()

    def showVersion(self):
        msgb = QMessageBox(self)
        msgb.setText("Currrent version is " + __version__ + " with status " + __status__)
        msgb.exec()

    def showCredits(self):
        msgb = QMessageBox(self)
        msgb.setText("<p><b>Contributors:</b></p>"
                     "<p>Stefano Marti, Dani Carbonell, Mattia Battaglia, Jeremias Schmidli, and Martin Neugebauer.")
        #"Icons made by Jeremias Schmidli and with icons by Vaadin from  www.flaticon.com</p>"
        msgb.exec()

    def testApp(self):
        self.newDia()
        self.centralWidget.testFunction()
        self.newDia()

        msgb = QMessageBox(self)
        msgb.setText("Test Complete, please restart the application. ")
        msgb.exec()

        self.close()

    def exportPDF(self):
        self.centralWidget.printPDF()

    def closeEvent(self, e):
        qmb = QMessageBox()
        qmb.setText("Do you want to save the current state of the project before closing the program?")
        qmb.setStandardButtons(QMessageBox.Save | QMessageBox.Close | QMessageBox.Cancel)
        qmb.setDefaultButton(QMessageBox.Cancel)
        ret = qmb.exec()
        if ret == QMessageBox.Cancel:
            e.ignore()
        elif ret == QMessageBox.Close:
            e.accept()
        elif ret == QMessageBox.Save:
            self.centralWidget.save()
            e.accept


    def setPaths(self):
        """
        Sets the export, diagram, ddck and trnsys path.
        """
        pathDialog = PathSetUp(self)

    def setFolder(self):
        """
            Sets the export, diagram, ddck and trnsys path.
        """
        pathDialog = FolderSetUp(self)

    def checkFilePaths(self):
        """
        Checks if all file paths have been set. If not, call setPaths
        """
        if getattr(sys, 'frozen', False):
            ROOT_DIR = os.path.dirname(sys.executable)
        elif __file__:
            ROOT_DIR = os.path.dirname(__file__)
        filepath = os.path.join(ROOT_DIR, 'filepaths.txt')
        if not os.path.isfile(filepath):
            open(filepath, 'w+')
            open(filepath,'w+')
        with open(filepath, 'r') as file:
            data = file.readlines()
        if len(data) < 2:
            pathSetUpDialog = PathSetUp(self)

    def setTrnsysPath(self):
        """
        Sets the trnsys path during start up, after user has defined it.
        """
        noOfRequiredPaths = 4
        if getattr(sys, 'frozen', False):
            ROOT_DIR = os.path.dirname(sys.executable)
        elif __file__:
            ROOT_DIR = os.path.dirname(__file__)
        filepaths = os.path.join(ROOT_DIR, 'filepaths.txt')
        with open(filepaths, 'r') as file:
            data = file.readlines()
        if len(data) == noOfRequiredPaths:
            self.centralWidget.trnsysPath = os.path.join(data[3][:-1], 'TRNExe.exe')

    def debugConns(self):
        """
        Check each block items for error connections.
        Returns warning message if blockitem contains two input connections or two output connections
        """
        print("trnsysObjs:", self.centralWidget.trnsysObj)
        self.noErrorConns = True
        for o in self.centralWidget.trnsysObj:
            print(o)
            if isinstance(o, BlockItem) and len(o.outputs) == 1 and len(o.inputs) == 1:
                print("Checking block connections", o.displayName)
                objInput = o.inputs[0]
                objOutput = o.outputs[0]
                connToInputToPort = objInput.connectionList[0].toPort
                connToOutputToPort = objOutput.connectionList[0].toPort
                connToInputFromPort = objInput.connectionList[0].fromPort
                connToOutputFromPort = objOutput.connectionList[0].fromPort
                connName1 = objInput.connectionList[0].displayName
                connName2 = objOutput.connectionList[0].displayName
                objName = o.displayName

                if objInput == connToInputToPort and objOutput == connToOutputToPort:
                    msgBox = QMessageBox()
                    msgBox.setText("both %s and %s are input ports into %s" % (connName1, connName2, objName))
                    msgBox.exec_()
                    self.noErrorConns = False

                elif objInput == connToInputFromPort and objOutput == connToOutputFromPort:
                    msgBox = QMessageBox()
                    msgBox.setText("both %s and %s are output ports from %s" % (connName1, connName2, objName))
                    msgBox.exec_()
                    self.noErrorConns = False
        return self.noErrorConns

    def runApp(self):
        runApp = RunMain()
        if self.centralWidget.projectPath == '':
            print("Temp path:", self.centralWidget.projectFolder)
            runApp.runAction(self.centralWidget.projectFolder)
        else:
            print("Project path:", self.centralWidget.projectPath)
            runApp.runAction(self.centralWidget.projectPath)

if __name__ == '__main__':
    # sys.stdout = open('errorLog', 'w')
    cssSs_ = cssSs.read()
    app = QApplication(sys.argv)
    app.setApplicationName("Diagram Creator")
    form = MainWindow()
    form.showMaximized()
    # form.openFileAtStartUp()
    form.show()
    form.checkFilePaths()
    form.setTrnsysPath()


    # app.setStyleSheet(cssSs_)

    # match = re.compile(r'\d{1,} {1,}\d{1,}')
    # match2 = re.compile(r'\d+')
    # x = match.sub("AAAA" ,"29 12 0 0         !1 : Collector", count=1)
    # x = match2.findall("29 12 0 0         !1 : Collector")
    # print(x)
    # print(type(x))
    app.exec_()


# Found bug: when dragging bridging connection over another segment, crash
# Found glitch: when having a disr segment, gradient is not correct anymore
# Found bug: IceStorage, when creating new connection and moving block, the connection does not update position
# Found bug: When in mode 1, sometimes dragging leads to segments collaps to a small point

# Improve autoarrange of connections
# TODO:   old/Prevent loops when adding connections to StorageBlock
# TODO 7: Solve mix up between i/o and left/right side

# There is a mess introduced with kwargs because the dencoder returns objects, which cannot have any
# connection to the "outside" of the decoder. This could maybe be improved by returning just the dict
# to the DiagramEditor class, which then can easily create the objects correctly.
