# pylint: skip-file
# type: ignore

import json
import typing as tp

import trnsysGUI.diagram.getBlockItem as _gbi

from trnsysGUI.doublePipePortItem import DoublePipePortItem
from trnsysGUI.singlePipePortItem import SinglePipePortItem
from trnsysGUI.connection.doublePipeConnection import DoublePipeConnection
from trnsysGUI.connection.singlePipeConnection import SinglePipeConnection


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

                # Adding the blocks to the scene could also be done inside Decoder now (before not possible because
                # no way of accessing the diagramView)

                elif ".__BlockDict__" in i:
                    componentType = i["BlockName"]
                    self.logger.debug("Found a block ")

                    if componentType == "GraphicalItem":
                        bl = _gbi.getBlockItem("GraphicalItem", self.editor, loadedGI=True)
                    elif componentType == "Control" or componentType == "MasterControl":
                        self.logger.warning(f"BlockItem: '{componentType}' is no longer supported in the GUI.")
                        continue
                    else:
                        bl = _gbi.getBlockItem(componentType, self.editor, displayName=i["BlockDisplayName"],
                                               loadedBlock=True)

                    bl.decode(i, resBlockList)

                elif ".__ConnectionDict__" in i:
                    fromPortId, toPortId = self._getPortIds(i)

                    # Looking for the ports the connection is connected to
                    fromPort = None
                    toPort = None
                    for connBl in resBlockList:
                        for p in connBl.inputs + connBl.outputs:
                            if p.id == fromPortId:
                                fromPort = p
                            if p.id == toPortId:
                                toPort = p

                    if fromPort is None:
                        self.logger.debug("Error: Did not found a fromPort")

                    if toPort is None:
                        self.logger.debug("Error: Did not found a toPort")

                    if isinstance(fromPort, SinglePipePortItem) and isinstance(toPort, SinglePipePortItem):
                        c = SinglePipeConnection(fromPort, toPort, self.editor)
                    elif isinstance(fromPort, DoublePipePortItem) and isinstance(toPort, DoublePipePortItem):
                        c = DoublePipeConnection(fromPort, toPort, self.editor)
                    else:
                        raise AssertionError("`fromPort' and `toPort' have different types.")
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
    def _getPortIds(i):
        if "PortFromID" in i and "PortToID" in i:
            # Legacy port ID naming
            fromPortId = i["PortFromID"]
            toPortId = i["PortToID"]
        elif "fromPortId" in i and "toPortId" in i:
            fromPortId = i["fromPortId"]
            toPortId = i["toPortId"]
        else:
            raise AssertionError("Could not find port IDs for connection.")
        return fromPortId, toPortId
