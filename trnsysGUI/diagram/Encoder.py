# pylint: disable=invalid-name

import json

from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.diagram import Editor as _de


class Encoder(json.JSONEncoder):
    """
    This class encodes the diagram (entire diagram or clipboard)
    obj is passed along to get some of the diagram editor porperties, for instance the id-generator
    TrnsysObj are then stored in a list of dictionaries, saved to a json file.
    Important: There is a slight naming error, since the dict containing all sub dicts (dicts for each block, connection
    and Id-generator) has the key ".__BlockDct__", although there are also other elements in there.
    """

    def default(self, obj):  # pylint: disable=arguments-renamed
        """

        Parameters
        ----------
        obj
        :type obj: trnsysGUI.DiagramEditor.DiagramEditor

        Returns
        -------

        """
        logger = obj.logger

        if isinstance(obj, _de.Editor):
            res = {}
            blockDct = {".__BlockDct__": True}

            for item in obj.trnsysObj:
                if isinstance(item, BlockItem) and not item.isVisible():
                    logger.debug("Invisible block [probably an insideBlock?]" + str(item) + str(item.displayName))
                    continue

                dictName, dct = item.encode()
                blockDct[dictName + str(item.id)] = dct

            idDict = {
                "__idDct__": True,
                "GlobalId": obj.idGen.getID(),
                "trnsysID": obj.idGen.getTrnsysID(),
                "globalConnID": obj.idGen.getConnID(),
            }
            blockDct["IDs"] = idDict

            nameDict = {"__nameDct__": True, "DiagramName": obj.diagramName, "ProjectFolder": obj.projectFolder}
            blockDct["Strings"] = nameDict

            for graphicalItem in obj.graphicalObj:
                dictName, dct = graphicalItem.encode()
                blockDct[dictName + str(graphicalItem.id)] = dct

            res["Blocks"] = blockDct

            res["hydraulicLoops"] = obj.hydraulicLoops.toJson()

            return res
        logger.debug("This is a strange object in Encoder" + type(obj))
        return None
