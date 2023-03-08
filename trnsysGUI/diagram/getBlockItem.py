

from trnsysGUI.AirSourceHP import AirSourceHP  # type: ignore[attr-defined]
from trnsysGUI.BlockItem import BlockItem  # type: ignore[attr-defined]
from trnsysGUI.Boiler import Boiler  # type: ignore[attr-defined]
from trnsysGUI.CentralReceiver import CentralReceiver  # type: ignore[attr-defined]
from trnsysGUI.Collector import Collector  # type: ignore[attr-defined]
from trnsysGUI.ExternalHx import ExternalHx  # type: ignore[attr-defined]
from trnsysGUI.GenericBlock import GenericBlock  # type: ignore[attr-defined]
from trnsysGUI.Graphicaltem import GraphicalItem  # type: ignore[attr-defined]
from trnsysGUI.GroundSourceHx import GroundSourceHx  # type: ignore[attr-defined]
from trnsysGUI.HPDoubleDual import HPDoubleDual  # type: ignore[attr-defined]
from trnsysGUI.HPDual import HPDual  # type: ignore[attr-defined]
from trnsysGUI.HeatPump import HeatPump  # type: ignore[attr-defined]
from trnsysGUI.HeatPumpTwoHx import HeatPumpTwoHx  # type: ignore[attr-defined]
from trnsysGUI.IceStorage import IceStorage  # type: ignore[attr-defined]
from trnsysGUI.IceStorageTwoHx import IceStorageTwoHx  # type: ignore[attr-defined]
from trnsysGUI.PV import PV  # type: ignore[attr-defined]
from trnsysGUI.ParabolicTroughField import ParabolicTroughField  # type: ignore[attr-defined]
from trnsysGUI.PitStorage import PitStorage  # type: ignore[attr-defined]
from trnsysGUI.Radiator import Radiator  # type: ignore[attr-defined]
from trnsysGUI.SaltTankCold import SaltTankCold  # type: ignore[attr-defined]
from trnsysGUI.SaltTankHot import SaltTankHot  # type: ignore[attr-defined]
from trnsysGUI.SteamPowerBlock import SteamPowerBlock  # type: ignore[attr-defined]
from trnsysGUI.TVentil import TVentil  # type: ignore[attr-defined]
from trnsysGUI.TeePiece import TeePiece  # type: ignore[attr-defined]
from trnsysGUI.WTap import WTap  # type: ignore[attr-defined]
from trnsysGUI.WTap_main import WTap_main  # type: ignore[attr-defined]
from trnsysGUI.connectors.connector import Connector  # type: ignore[attr-defined]
from trnsysGUI.connectors.doubleDoublePipeConnector import DoubleDoublePipeConnector
from trnsysGUI.connectors.singleDoublePipeConnector import SingleDoublePipeConnector
from trnsysGUI.crystalizer import Crystalizer
from trnsysGUI.doublePipeTeePiece import DoublePipeTeePiece
from trnsysGUI.geotherm import Geotherm
from trnsysGUI.pump import Pump  # type: ignore[attr-defined]
from trnsysGUI.sink import Sink
from trnsysGUI.source import Source
from trnsysGUI.sourceSink import SourceSink
from trnsysGUI.storageTank.widget import StorageTank
from trnsysGUI.water import Water


def getBlockItem(componentType, editor, displayName=None, loadedBlock=None):
    # todo: provide this to Decoder as well
    """ returns an "blockItem" instance of a specific diagram component
        componentType: name of the component, e.g., "StorageTank"
        """

    blockItems = {"StorageTank": {"blockItem": StorageTank, "displayNamePrefix": "Tes"},
                  "TeePiece": {"blockItem": TeePiece, "displayNamePrefix": "Tee"},
                  "DPTee": {"blockItem": DoublePipeTeePiece, "displayNamePrefix": "DTee"},
                  "SPCnr": {"blockItem": SingleDoublePipeConnector, "displayNamePrefix": "SCnr"},
                  "DPCnr": {"blockItem": DoubleDoublePipeConnector, "displayNamePrefix": "DCnr"},
                  "TVentil": {"blockItem": TVentil, "displayNamePrefix": "Val"},
                  "Pump": {"blockItem": Pump, "displayNamePrefix": "Pump"},
                  "Collector": {"blockItem": Collector, "displayNamePrefix": "Coll"},
                  "HP": {"blockItem": HeatPump, "displayNamePrefix": "HP"},
                  "IceStorage": {"blockItem": IceStorage, "displayNamePrefix": "IceS"},
                  "PitStorage": {"blockItem": PitStorage, "displayNamePrefix": "PitS"},
                  "Radiator": {"blockItem": Radiator, "displayNamePrefix": "Rad"},
                  "WTap": {"blockItem": WTap, "displayNamePrefix": "WtTp"},
                  "WTap_main": {"blockItem": WTap_main, "displayNamePrefix": "WtSp"},
                  "Connector": {"blockItem": Connector, "displayNamePrefix": "Conn"},
                  "GenericBlock": {"blockItem": GenericBlock, "displayNamePrefix": "GBlk"},
                  "HPTwoHx": {"blockItem": HeatPumpTwoHx, "displayNamePrefix": "HP"},
                  "HPDoubleDual": {"blockItem": HPDoubleDual, "displayNamePrefix": "HPDD"},
                  "HPDual": {"blockItem": HPDual, "displayNamePrefix": "HPDS"},
                  "Boiler": {"blockItem": Boiler, "displayNamePrefix": "Bolr"},
                  "AirSourceHP": {"blockItem": AirSourceHP, "displayNamePrefix": "Ashp"},
                  "PV": {"blockItem": PV, "displayNamePrefix": "PV"},
                  "GroundSourceHx": {"blockItem": GroundSourceHx, "displayNamePrefix": "Gshx"},
                  "ExternalHx": {"blockItem": ExternalHx, "displayNamePrefix": "Hx"},
                  "IceStorageTwoHx": {"blockItem": IceStorageTwoHx, "displayNamePrefix": "IceS"},
                  "GraphicalItem": {"blockItem": GraphicalItem, "displayNamePrefix": None},
                  "Sink": {"blockItem": Sink, "displayNamePrefix": "QSnk"},
                  "Source": {"blockItem": Source, "displayNamePrefix": "QSrc"},
                  "SourceSink": {"blockItem": SourceSink, "displayNamePrefix": "QExc"},
                  "Geotherm": {"blockItem": Geotherm, "displayNamePrefix": "GeoT"},
                  "Water": {"blockItem": Water, "displayNamePrefix": "QWat"},
                  "Crystalizer": {"blockItem": Crystalizer, "displayNamePrefix": "Cryt"},
                  "powerBlock": {"blockItem": SteamPowerBlock, "displayNamePrefix": "StPB"},
                  "CSP_PT": {"blockItem": ParabolicTroughField, "displayNamePrefix": "PT"},
                  "CSP_CR": {"blockItem": CentralReceiver, "displayNamePrefix": "CR"},
                  "coldSaltTank": {"blockItem": SaltTankCold, "displayNamePrefix": "ClSt"},
                  "hotSaltTank": {"blockItem": SaltTankHot, "displayNamePrefix": "HtSt"},
                  }
    if componentType not in blockItems:
        raise AssertionError(f"Unknown kind of block item: {componentType}")
    else:
        parts = blockItems[componentType]

    if parts["blockItem"] == GraphicalItem:  # may not be needed
        item = parts["blockItem"](editor)
    else:
        item = parts["blockItem"](componentType, editor, displayNamePrefix=parts["displayNamePrefix"])

    return item
