# pylint: skip-file
# type: ignore

import json

import trnsysGUI.BlockItem as _bi
import trnsysGUI.diagram.Editor as _de


class Encoder(json.JSONEncoder):
    def default(self, obj):
        assert isinstance(obj, _de.Editor), f"Object to encode must be an `{_de.Editor.__name__}`."

        res = {}
        blockDct = {".__BlockDct__": True}

        for i, trnsysObject in enumerate(obj.trnsysObj, start=1):
            if isinstance(trnsysObject, _bi.BlockItem):
                assert trnsysObject.isVisible()

            dictName, dct = trnsysObject.encode()
            key = f"{dictName}{i}"
            blockDct[key] = dct

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
