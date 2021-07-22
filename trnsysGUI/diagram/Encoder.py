# pylint: skip-file
# type: ignore

import json

from trnsysGUI.diagram import Editor as _de
from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.Connection import Connection
from trnsysGUI.copyGroup import copyGroup


class Encoder(json.JSONEncoder):
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
        :type obj: trnsysGUI.DiagramEditor.DiagramEditor

        Returns
        -------

        """
        logger = obj.logger

        if isinstance(obj, _de.Editor) or isinstance(obj, copyGroup):
            logger.debug("Is diagram or copygroup")

            res = {}
            blockDct = {".__BlockDct__": True}

            for t in obj.trnsysObj:
                if isinstance(t, BlockItem) and not t.isVisible():
                    logger.debug("Invisible block [probably an insideBlock?]" + str(t) + str(t.displayName))
                    continue

                dictName, dct = t.encode()
                blockDct[dictName + str(t.id)] = dct

            idDict = {
                "__idDct__": True,
                "GlobalId": obj.idGen.getID(),
                "trnsysID": obj.idGen.getTrnsysID(),
                "globalConnID": obj.idGen.getConnID(),
            }
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
            logger.debug("This is a strange object in Encoder" + type(obj))
            # return super().default(obj)
