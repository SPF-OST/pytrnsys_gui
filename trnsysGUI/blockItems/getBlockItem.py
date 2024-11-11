from __future__ import annotations

import typing as _tp

import pytrnsys.utils.result as _res

import trnsysGUI.blockItems.names as _names
import trnsysGUI.internalPiping as _ip
import trnsysGUI.names.create as _cname
import trnsysGUI.names.manager as _nm
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
from trnsysGUI.Radiator import Radiator  # type: ignore[attr-defined]
from trnsysGUI.SaltTankCold import SaltTankCold  # type: ignore[attr-defined]
from trnsysGUI.SaltTankHot import SaltTankHot  # type: ignore[attr-defined]
from trnsysGUI.SteamPowerBlock import SteamPowerBlock  # type: ignore[attr-defined]
from trnsysGUI.TVentil import TVentil  # type: ignore[attr-defined]
from trnsysGUI.connection.connectors.connector import Connector  # type: ignore[attr-defined]
from trnsysGUI.connection.connectors.doubleDoublePipeConnector import (
    DoubleDoublePipeConnector,
)
from trnsysGUI.connection.connectors.singleDoublePipeConnector import (
    SingleDoublePipeConnector,
)
from trnsysGUI.crystalizer import Crystalizer
from trnsysGUI.geotherm import Geotherm
from trnsysGUI.pumpsAndTaps.pump import Pump  # type: ignore[attr-defined]
from trnsysGUI.pumpsAndTaps.tap import Tap  # type: ignore[attr-defined]
from trnsysGUI.pumpsAndTaps.tapMains import TapMains  # type: ignore[attr-defined]
from trnsysGUI.sink import Sink
from trnsysGUI.source import Source
from trnsysGUI.sourceSink import SourceSink
from trnsysGUI.storageTank.widget import StorageTank
from trnsysGUI.teePieces.doublePipeTeePiece import DoublePipeTeePiece
from trnsysGUI.teePieces.teePiece import TeePiece
from trnsysGUI.water import Water

import trnsysGUI.components.pluginComponent as _pcomp
import trnsysGUI.components.plugin.factory as _pfactory


if _tp.TYPE_CHECKING:  # pragma: no cover
    import trnsysGUI.diagram.Editor as _ed


def createBlockItem(
    componentTypeName: str,
    editor: _ed.Editor,  # type: ignore[name-defined]
    namesManager: _nm.NamesManager,
    displayName: _tp.Optional[str] = None,
) -> BlockItem | GraphicalItem:
    """
    returns a "blockItem" instance of a specific diagram component
    componentType: name of the component, e.g., "StorageTank"
    """

    blockItems = {
        "StorageTank": {"blockItem": StorageTank, "baseDisplayName": "Tes"},
        "TeePiece": {"blockItem": TeePiece, "baseDisplayName": "Tee"},
        "DPTee": {"blockItem": DoublePipeTeePiece, "baseDisplayName": "DTee"},
        "SPCnr": {
            "blockItem": SingleDoublePipeConnector,
            "baseDisplayName": "SCnr",
        },
        "DPCnr": {
            "blockItem": DoubleDoublePipeConnector,
            "baseDisplayName": "DCnr",
        },
        "TVentil": {"blockItem": TVentil, "baseDisplayName": "Val"},
        "Pump": {"blockItem": Pump, "baseDisplayName": "Pump"},
        "Collector": {"blockItem": Collector, "baseDisplayName": "Coll"},
        "Kollektor": {"blockItem": Collector, "baseDisplayName": "Coll"},
        "HP": {"blockItem": HeatPump, "baseDisplayName": "HP"},
        "IceStorage": {"blockItem": IceStorage, "baseDisplayName": "IceS"},
        "Radiator": {"blockItem": Radiator, "baseDisplayName": "Rad"},
        _names.TAP: {"blockItem": Tap, "baseDisplayName": "WtTp"},
        "WTap_main": {"blockItem": TapMains, "baseDisplayName": "WtSp"},
        "Connector": {"blockItem": Connector, "baseDisplayName": "Conn"},
        "GenericBlock": {"blockItem": GenericBlock, "baseDisplayName": "GBlk"},
        "HPTwoHx": {"blockItem": HeatPumpTwoHx, "baseDisplayName": "HP"},
        "HPDoubleDual": {"blockItem": HPDoubleDual, "baseDisplayName": "HPDD"},
        "HPDual": {"blockItem": HPDual, "baseDisplayName": "HPDS"},
        "Boiler": {"blockItem": Boiler, "baseDisplayName": "Bolr"},
        "AirSourceHP": {"blockItem": AirSourceHP, "baseDisplayName": "Ashp"},
        "PV": {"blockItem": PV, "baseDisplayName": "PV"},
        "GroundSourceHx": {
            "blockItem": GroundSourceHx,
            "baseDisplayName": "Gshx",
        },
        "ExternalHx": {"blockItem": ExternalHx, "baseDisplayName": "Hx"},
        "IceStorageTwoHx": {
            "blockItem": IceStorageTwoHx,
            "baseDisplayName": "IceS",
        },
        "Sink": {"blockItem": Sink, "baseDisplayName": "QSnk"},
        "Source": {"blockItem": Source, "baseDisplayName": "QSrc"},
        "SourceSink": {"blockItem": SourceSink, "baseDisplayName": "QExc"},
        "Geotherm": {"blockItem": Geotherm, "baseDisplayName": "GeoT"},
        "Water": {"blockItem": Water, "baseDisplayName": "QWat"},
        "Crystalizer": {"blockItem": Crystalizer, "baseDisplayName": "Cryt"},
        "powerBlock": {
            "blockItem": SteamPowerBlock,
            "baseDisplayName": "StPB",
        },
        "CSP_PT": {"blockItem": ParabolicTroughField, "baseDisplayName": "PT"},
        "CSP_CR": {"blockItem": CentralReceiver, "baseDisplayName": "CR"},
        "coldSaltTank": {"blockItem": SaltTankCold, "baseDisplayName": "ClSt"},
        "hotSaltTank": {"blockItem": SaltTankHot, "baseDisplayName": "HtSt"},
    }

    if componentTypeName == "GraphicalItem":
        return GraphicalItem(editor)

    if componentTypeName in blockItems:
        parts = blockItems[componentTypeName]
        clazz = parts["blockItem"]
        baseDisplayName = parts["baseDisplayName"]
    else:
        clazz = _pcomp.PluginComponent
        baseDisplayName = _getBaseDisplayNameForPluginComponent(
            componentTypeName
        )

    displayName = _addOrCreateAndAddDisplayName(
        displayName, clazz, baseDisplayName, namesManager
    )

    blockItem = clazz(componentTypeName, editor, displayName)

    return blockItem


def _getBaseDisplayNameForPluginComponent(componentTypeName: str) -> str:
    factory = _pfactory.Factory.createDefault()
    pluginResult = factory.create(componentTypeName)
    plugin = _res.value(pluginResult)
    baseDisplayName = plugin.baseDisplayName
    return baseDisplayName


def _addOrCreateAndAddDisplayName(
    displayName: str | None,
    blockItemClass: type[BlockItem],
    baseDisplayName: str,
    namesManager: _nm.NamesManager,
) -> str:
    if not displayName:
        createNamingHelper = _cname.CreateNamingHelper(namesManager)
        checkDdckFolder = (
            blockItemClass.hasDdckDirectory()
            if issubclass(blockItemClass, _ip.HasInternalPiping)
            else False
        )
        displayName = createNamingHelper.generateName(
            baseDisplayName, checkDdckFolder, firstGeneratedNameHasNumber=False
        )

    namesManager.addName(displayName)

    return displayName
