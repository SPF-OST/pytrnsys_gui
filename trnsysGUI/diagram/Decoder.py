# pylint: skip-file
# type: ignore

import json
import typing as tp

from trnsysGUI.AirSourceHP import AirSourceHP
from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.Boiler import Boiler
from trnsysGUI.Collector import Collector
from trnsysGUI.Connection import Connection
from trnsysGUI.Connector import Connector
from trnsysGUI.Control import Control
from trnsysGUI.ExternalHx import ExternalHx
from trnsysGUI.GenericBlock import GenericBlock
from trnsysGUI.Graphicaltem import GraphicalItem
from trnsysGUI.GroundSourceHx import GroundSourceHx
from trnsysGUI.Group import Group
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


class Decoder(json.JSONDecoder):
    """
    Decodes the diagram
    """

    def __init__(self, *args, **kwargs):

        self.editor = kwargs["editor"]
        self.logger = self.editor.logger
        kwargs.pop("editor")
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, arr: tp.Mapping[str, tp.Mapping[str, tp.Any]]) -> tp.Any:
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

            resConnList = []

            sorted_items = sorted(arr.items(), key=lambda t: t[0])

            sorted_keys: tp.Sequence[str]
            sorted_values: tp.Sequence[tp.Mapping[str, tp.Any]]
            sorted_keys, sorted_values = zip(*sorted_items)

            formatted_sorted_keys = ", ".join(sorted_keys)
            self.logger.debug("keys are %s", formatted_sorted_keys)

            for i in sorted_values:
                if type(i) is not dict:
                    continue

                if ".__GroupDict__" in i:
                    self.logger.debug("Found the group dict")
                    self.logger.debug("Decoding group " + str(i["GroupName"]))

                    groupListNames = [g.displayName for g in self.editor.groupList]

                    if i["GroupName"] not in groupListNames:
                        g = Group(
                            i["Position"][0], i["Position"][1], i["Size"][0], i["Size"][1], self.editor.diagramScene
                        )
                        g.setName(i["GroupName"])

                # Adding the blocks to the scene could also be done inside Decoder now (before not possible because
                # no way of accessing the diagramView)

                elif ".__BlockDict__" in i:
                    self.logger.debug("Found a block ")
                    if i["BlockName"] == "TeePiece":
                        bl = TeePiece(
                            i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loadedBlock=True
                        )
                    elif i["BlockName"] == "TVentil":
                        bl = TVentil(
                            i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loadedBlock=True
                        )
                    elif i["BlockName"] == "Pump":
                        bl = Pump(
                            i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loadedBlock=True
                        )
                    elif i["BlockName"] == "Collector":
                        bl = Collector(
                            i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loadedBlock=True
                        )
                    elif i["BlockName"] == "HP":
                        bl = HeatPump(
                            i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loadedBlock=True
                        )
                    elif i["BlockName"] == "IceStorage":
                        bl = IceStorage(
                            i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loadedBlock=True
                        )
                    elif i["BlockName"] == "PitStorage":
                        bl = PitStorage(
                            i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loadedBlock=True
                        )
                    elif i["BlockName"] == "Radiator":
                        bl = Radiator(
                            i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loadedBlock=True
                        )
                    elif i["BlockName"] == "WTap":
                        bl = WTap(
                            i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loadedBlock=True
                        )
                    elif i["BlockName"] == "WTap_main":
                        bl = WTap_main(
                            i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loadedBlock=True
                        )
                    elif i["BlockName"] == "Connector":
                        bl = Connector(
                            i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loadedBlock=True
                        )
                    elif i["BlockName"] == "Boiler":
                        bl = Boiler(
                            i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loadedBlock=True
                        )
                    elif i["BlockName"] == "AirSourceHP":
                        bl = AirSourceHP(
                            i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loadedBlock=True
                        )
                    elif i["BlockName"] == "PV":
                        bl = PV(
                            i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loadedBlock=True
                        )
                    elif i["BlockName"] == "GroundSourceHx":
                        bl = GroundSourceHx(
                            i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loadedBlock=True
                        )

                    # [--- new encoding
                    elif i["BlockName"] == "StorageTank":
                        bl = StorageTank(
                            i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loadedBlock=True
                        )
                    elif i["BlockName"] == "HeatPump":
                        bl = HeatPump(
                            i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loadedBlock=True
                        )
                    elif i["BlockName"] == "HPTwoHx":
                        bl = HeatPumpTwoHx(
                            i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loadedBlock=True
                        )
                    elif i["BlockName"] == "HPDoubleDual":
                        bl = HPDoubleDual(
                            i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loadedBlock=True
                        )
                    elif i["BlockName"] == "ExternalHx":
                        bl = ExternalHx(
                            i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loadedBlock=True
                        )
                    elif i["BlockName"] == "IceStorageTwoHx":
                        bl = IceStorageTwoHx(
                            i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loadedBlock=True
                        )
                    elif i["BlockName"] == "GenericBlock":
                        bl = GenericBlock(
                            i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loadedBlock=True
                        )
                    elif i["BlockName"] == "MasterControl":
                        bl = MasterControl(
                            i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loadedBlock=True
                        )
                    elif i["BlockName"] == "Control":
                        bl = Control(
                            i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"], loadedBlock=True
                        )
                    # --- new encoding]

                    elif i["BlockName"] == "GraphicalItem":
                        bl = GraphicalItem(self.editor.diagramView, loadedGI=True)

                    else:
                        bl = BlockItem(i["BlockName"], self.editor.diagramView, displayName=i["BlockDisplayName"])

                    bl.decode(i, resBlockList)

                elif ".__ConnectionDict__" in i:
                    fromPort = None
                    toPort = None

                    # Looking for the ports the connection is connected to
                    for connBl in resBlockList:
                        for p in connBl.inputs + connBl.outputs:
                            if p.id == i["PortFromID"]:
                                fromPort = p
                            if p.id == i["PortToID"]:
                                toPort = p

                    if fromPort is None:
                        self.logger.debug("Error: Did not found a fromPort")

                    if toPort is None:
                        self.logger.debug("Error: Did not found a toPort")

                    connectionKwargs = self.create_connection_kwargs(i)

                    c = Connection(fromPort, toPort, self.editor, **connectionKwargs)

                    c.decode(i)
                    resConnList.append(c)

                elif "__idDct__" in i:
                    resBlockList.append(i)
                elif "__nameDct__" in i:
                    resBlockList.append(i)
                else:
                    self.logger.debug("Error: Not recognized object in decoder, " + str(i))

            return resBlockList, resConnList

        return arr

    @staticmethod
    def create_connection_kwargs(item: tp.Mapping[str, tp.Any]) -> tp.Mapping[str, tp.Any]:
        connectionKwargs = dict(
            loadedConn=True,
            fromPortId=item["PortFromID"],
            toPortId=item["PortToID"],
            segmentsLoad=item["SegmentPositions"],
            cornersLoad=item["CornerPositions"],
        )

        if "FirstSegmentLabelPos" in item:
            connectionKwargs["labelPos"] = tuple(item["FirstSegmentLabelPos"])

        if "FirstSegmentMassFlowLabelPos" in item:
            connectionKwargs["labelMassPos"] = tuple(item["FirstSegmentMassFlowLabelPos"])

        return connectionKwargs
