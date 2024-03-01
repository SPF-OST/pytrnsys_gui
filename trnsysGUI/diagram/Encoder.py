# pylint: skip-file
# type: ignore

import json

import trnsysGUI.BlockItem as _bi
import trnsysGUI.diagram.Editor as _de


class Encoder(json.JSONEncoder):
    def default(self, obj):
        assert isinstance(obj, _de.Editor), f"Object to encode must be an `{_de.Editor.__name__}`."

        logger = obj.logger

        res = {}
        blockDct = {".__BlockDct__": True}

        for t in obj.trnsysObj:
            if isinstance(t, _bi.BlockItem) and not t.isVisible():
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

        for gi in obj.graphicalObj:
            dictName, dct = gi.encode()
            blockDct[dictName + str(gi.id)] = dct

        res["Blocks"] = blockDct

        res["hydraulicLoops"] = obj.hydraulicLoops.toJson()

        return res
