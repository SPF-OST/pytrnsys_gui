# pylint: skip-file
# type: ignore

import json as _json
import typing as _tp

import trnsysGUI.blockItems.getBlockItem as _gbi
import trnsysGUI.connection.connectionBase as _cb
import trnsysGUI.connection.doublePipeConnection as _dpc
import trnsysGUI.connection.singlePipeConnection as _spc
import trnsysGUI.connection.undo as _cundo
import trnsysGUI.doublePipePortItem as _dbi
import trnsysGUI.singlePipePortItem as _spi


class Decoder(_json.JSONDecoder):
    """
    Decodes the diagram
    """

    _UNSET_ERROR_NAME = "ERROR_NAME_NOT_SET_IN_DECODE"

    def __init__(self, *args, **kwargs):

        self.editor = kwargs["editor"]
        self.logger = self.editor.logger
        kwargs.pop("editor")
        _json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, arr: _tp.Mapping[str, _tp.Mapping[str, _tp.Any]]) -> _tp.Any:
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

            sortedItems = sorted(arr.items(), key=lambda t: t[0])

            sortedKeys: _tp.Sequence[str]
            sortedValues: _tp.Sequence[_tp.Mapping[str, _tp.Any]]
            sortedKeys, sortedValues = zip(*sortedItems)

            formattedSortedKeys = ", ".join(sortedKeys)
            self.logger.debug("keys are %s", formattedSortedKeys)

            for i in sortedValues:
                if type(i) is not dict:
                    continue

                # Adding the blocks to the scene could also be done inside Decoder now (before not possible because
                # no way of accessing the diagramView)

                elif ".__BlockDict__" in i:
                    componentType = i["BlockName"]
                    self.logger.debug("Found a block ")

                    if componentType == "GraphicalItem":
                        bl = _gbi.getBlockItem("GraphicalItem", self.editor)
                    elif componentType == "Control" or componentType == "MasterControl":
                        self.logger.warning(f"BlockItem: '{componentType}' is no longer supported in the GUI.")
                        continue
                    else:
                        bl = _gbi.getBlockItem(componentType, self.editor, displayName=i["BlockDisplayName"])

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

                    connection: _cb.ConnectionBase
                    match (fromPort, toPort):
                        case (None, _):
                            raise AssertionError("Couldn't find from port.")
                        case (_, None):
                            raise AssertionError("Couldn't find to port.")
                        case (_spi.SinglePipePortItem(), _spi.SinglePipePortItem()):
                            connection = _spc.SinglePipeConnection(
                                self._UNSET_ERROR_NAME, fromPort, toPort, self.editor
                            )
                        case (_dbi.DoublePipePortItem(), _dbi.DoublePipePortItem()):
                            connection = _dpc.DoublePipeConnection(
                                self._UNSET_ERROR_NAME, fromPort, toPort, self.editor
                            )
                        case _:
                            raise AssertionError("`fromPort' and `toPort' have different types.")

                    connection.decode(i)
                    _cundo.reAddConnection(connection)
                    self.editor.diagramScene.addItem(connection)
                    resConnList.append(connection)

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
