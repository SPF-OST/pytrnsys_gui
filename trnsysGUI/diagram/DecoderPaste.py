# pylint: skip-file
# type: ignore

import json

from trnsysGUI.AirSourceHP import AirSourceHP
from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.Boiler import Boiler
from trnsysGUI.Collector import Collector
from trnsysGUI.Connection import Connection
from trnsysGUI.Connector import Connector
from trnsysGUI.Control import Control
from trnsysGUI.ExternalHx import ExternalHx
from trnsysGUI.GenericBlock import GenericBlock
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


class DecoderPaste(json.JSONDecoder):
    """
    Decodes the clipboard.
    It creates the copied blocks with suffix COPY, it does not set the ids forward.

    """

    def __init__(self, *args, **kwargs):
        self.editor = kwargs["editor"]
        self.logger = self.editor.logger
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

            resConnList = []
            self.logger.debug("keys are " + str(sorted((arr.keys()))))
            for k in sorted((arr.keys())):
                if type(arr[k]) is dict:
                    if ".__BlockDict__" in arr[k]:
                        i = arr[k]

                        if i["BlockName"] == "TeePiece":
                            bl = TeePiece(
                                i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loaded=True
                            )
                        elif i["BlockName"] == "TVentil":
                            bl = TVentil(
                                i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loaded=True
                            )
                        elif i["BlockName"] == "Pump":
                            bl = Pump(
                                i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loaded=True
                            )
                        elif i["BlockName"] == "Collector":
                            bl = Collector(
                                i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loaded=True
                            )
                        elif i["BlockName"] == "Kollektor":
                            i["BlockName"] = "Collector"
                            bl = Collector(
                                i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loaded=True
                            )
                        elif i["BlockName"] == "HP":
                            bl = HeatPump(
                                i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loaded=True
                            )
                        elif i["BlockName"] == "IceStorage":
                            bl = IceStorage(
                                i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loaded=True
                            )
                        elif i["BlockName"] == "PitStorage":
                            bl = PitStorage(
                                i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loaded=True
                            )
                        elif i["BlockName"] == "Radiator":
                            bl = Radiator(
                                i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loaded=True
                            )
                        elif i["BlockName"] == "WTap":
                            bl = WTap(
                                i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loaded=True
                            )
                        elif i["BlockName"] == "WTap_main":
                            bl = WTap_main(
                                i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loaded=True
                            )
                        elif i["BlockName"] == "Connector":
                            bl = Connector(
                                i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loaded=True
                            )
                        elif i["BlockName"] == "GenericBlock":
                            bl = GenericBlock(
                                i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loaded=True
                            )
                        elif i["BlockName"] == "Boiler":
                            bl = Boiler(
                                i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loaded=True
                            )
                        elif i["BlockName"] == "AirSourceHP":
                            bl = AirSourceHP(
                                i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loaded=True
                            )
                        elif i["BlockName"] == "PV":
                            bl = PV(
                                i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loaded=True
                            )
                        elif i["BlockName"] == "GroundSourceHx":
                            bl = GroundSourceHx(
                                i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loaded=True
                            )

                        # [--- New encoding
                        elif i["BlockName"] == "StorageTank":
                            bl = StorageTank(
                                i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loaded=True
                            )
                        elif i["BlockName"] == "HeatPump":
                            bl = HeatPump(
                                i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loaded=True
                            )
                        elif i["BlockName"] == "HPTwoHx":
                            bl = HeatPumpTwoHx(
                                i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loaded=True
                            )
                        elif i["BlockName"] == "HPDoubleDual":
                            bl = HPDoubleDual(
                                i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loaded=True
                            )
                        elif i["BlockName"] == "ExternalHx":
                            bl = ExternalHx(
                                i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loaded=True
                            )
                        elif i["BlockName"] == "IceStorageTwoHx":
                            bl = IceStorageTwoHx(
                                i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loaded=True
                            )
                        elif i["BlockName"] == "GenericBlock":
                            bl = GenericBlock(
                                i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loaded=True
                            )
                        elif i["BlockName"] == "MasterControl":
                            bl = MasterControl(
                                i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loaded=True
                            )
                        elif i["BlockName"] == "Control":
                            bl = Control(
                                i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loaded=True
                            )
                        # new encoding ---]

                        else:
                            bl = BlockItem(
                                i["BlockName"], self.editor.diagramView, displayName=i["BlockName"], loaded=True
                            )

                        bl.decodePaste(i, offset_x, offset_y, resConnList, resBlockList)

                    elif ".__ConnectionDict__" in arr[k]:
                        # It is important to load the connections at last because else the ports are not defined.
                        i = arr[k]

                        fport = None
                        tPort = None
                        self.logger.debug("Loading a connection in paste")
                        self.logger.debug("blocks are " + str(resBlockList))

                        for connBl in resBlockList:
                            # if "COPY" in connBl.displayName and connBl.displayName[-4:None] == 'COPY':
                            if True:
                                for p in connBl.inputs + connBl.outputs:
                                    if p.id == i["PortFromID"]:
                                        fport = p
                                    if p.id == i["PortToID"]:
                                        tPort = p

                        if fport is None:
                            self.logger.debug("Did not found a fromPort")

                        if tPort is None:
                            self.logger.debug("Did not found a tPort")

                        if True:
                            for cornerL in i["CornerPositions"]:
                                cornerL[0] += offset_x
                                cornerL[1] += offset_y

                            c = Connection(
                                fport,
                                tPort,
                                self.editor,
                                fromPortId=i["PortFromID"],
                                toPortId=i["PortToID"],
                                segmentsLoad=i["SegmentPositions"],
                                cornersLoad=i["CornerPositions"],
                                loadedConn=True,
                            )
                            c.setName(i["ConnDisplayName"])

                            # Note: This wouldn't allow two connections to the same port (which is not really used, but ok)
                            # fport.id = getID()
                            # tPort.id = getID()
                            resConnList.append(c)
                        else:
                            self.logger.debug(
                                "This is an internal connection (e.g. in the storage) and thus is not created now"
                            )

                    elif "__idDct__" in arr[k]:
                        resBlockList.append(arr[k])
                    else:
                        self.logger.debug("Error: Not recognized object in decoder")

            return resBlockList, resConnList

        return arr
