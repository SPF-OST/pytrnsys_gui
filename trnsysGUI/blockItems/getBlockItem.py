from __future__ import annotations

import typing as _tp

from trnsysGUI.AirSourceHP import AirSourceHP  # type: ignore[attr-defined]
from trnsysGUI.BlockItem import BlockItem  # type: ignore[attr-defined]
from trnsysGUI.Boiler import Boiler  # type: ignore[attr-defined]
from trnsysGUI.CentralReceiver import CentralReceiver  # type: ignore[attr-defined]
from trnsysGUI.Collector import Collector  # type: ignore[attr-defined]
from trnsysGUI.ExternalHx import ExternalHx  # type: ignore[attr-defined]
from trnsysGUI.GenericBlock import GenericBlock  # type: ignore[attr-defined]
from trnsysGUI.GraphicalItem import GraphicalItem  # type: ignore[attr-defined]
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
from trnsysGUI.pumpsAndTaps.tap import Tap  # type: ignore[attr-defined]
from trnsysGUI.pumpsAndTaps.tapMains import TapMains  # type: ignore[attr-defined]
from trnsysGUI.connection.connectors.connector import Connector  # type: ignore[attr-defined]
from trnsysGUI.connection.connectors.doubleDoublePipeConnector import DoubleDoublePipeConnector
from trnsysGUI.connection.connectors.singleDoublePipeConnector import SingleDoublePipeConnector
from trnsysGUI.crystalizer import Crystalizer
from trnsysGUI.geotherm import Geotherm
from trnsysGUI.pumpsAndTaps.pump import Pump  # type: ignore[attr-defined]
from trnsysGUI.sink import Sink
from trnsysGUI.source import Source
from trnsysGUI.sourceSink import SourceSink
from trnsysGUI.storageTank.widget import StorageTank
from trnsysGUI.teePieces.doublePipeTeePiece import DoublePipeTeePiece
from trnsysGUI.teePieces.teePiece import TeePiece
from trnsysGUI.water import Water

if _tp.TYPE_CHECKING:
    import trnsysGUI.diagram.Editor as _ed


def getBlockItem(
    componentTypeName: str, editor: _ed.Editor, displayName: _tp.Optional[str] = None  # type: ignore[name-defined]
) -> BlockItem | GraphicalItem:
    """
    returns a "blockItem" instance of a specific diagram component
    componentType: name of the component, e.g., "StorageTank"
    """

    blockItems = {
        "StorageTank": {"blockItem": StorageTank, "displayNamePrefix": "Tes"},
        "TeePiece": {"blockItem": TeePiece, "displayNamePrefix": "Tee"},
        "DPTee": {"blockItem": DoublePipeTeePiece, "displayNamePrefix": "DTee"},
        "SPCnr": {"blockItem": SingleDoublePipeConnector, "displayNamePrefix": "SCnr"},
        "DPCnr": {"blockItem": DoubleDoublePipeConnector, "displayNamePrefix": "DCnr"},
        "TVentil": {"blockItem": TVentil, "displayNamePrefix": "Val"},
        "Pump": {"blockItem": Pump, "displayNamePrefix": "Pump"},
        "Collector": {"blockItem": Collector, "displayNamePrefix": "Coll"},
        "Kollektor": {"blockItem": Collector, "displayNamePrefix": "Coll"},
        "HP": {"blockItem": HeatPump, "displayNamePrefix": "HP"},
        "IceStorage": {"blockItem": IceStorage, "displayNamePrefix": "IceS"},
        "PitStorage": {"blockItem": PitStorage, "displayNamePrefix": "PitS"},
        "Radiator": {"blockItem": Radiator, "displayNamePrefix": "Rad"},
        "WTap": {"blockItem": Tap, "displayNamePrefix": "WtTp"},
        "WTap_main": {"blockItem": TapMains, "displayNamePrefix": "WtSp"},
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

    if componentTypeName == "GraphicalItem":
        return GraphicalItem(editor)

    if componentTypeName not in blockItems:
        raise ValueError(f"Unknown kind of block item: `{componentTypeName}`.")

    parts = blockItems[componentTypeName]
    clazz = parts["blockItem"]
    prefix = parts["displayNamePrefix"]

    if displayName:
        return clazz(componentTypeName, editor, displayName=displayName, loadedBlock=True)

    return clazz(componentTypeName, editor, displayNamePrefix=prefix)
