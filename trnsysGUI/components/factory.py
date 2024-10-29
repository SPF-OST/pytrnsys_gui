import collections.abc as _cabc
import dataclasses as _dc
import logging as _log

import PyQt5.QtGui as _qtg

import pytrnsys.utils.result as _res
import pytrnsys.utils.warnings as _warn

import trnsysGUI.blockItems.names as _bnames
import trnsysGUI.images as _img

from .plugin import factory as _pfactory

_LOGGER = _log.getLogger(__name__)


@_dc.dataclass
class Component:
    name: str
    icon: _qtg.QIcon


# This can't be a constant as QPixmaps are created and in order to create those
# a QApplication must have already been created
def _getHardCodedComponents() -> _cabc.Sequence[Component]:
    return [
        Component("Connector", _img.CONNECTOR_SVG.icon()),
        Component("TeePiece", _img.TEE_PIECE_SVG.icon()),
        Component("DPTee", _img.DP_TEE_PIECE_SVG.icon()),
        Component("SPCnr", _img.SINGLE_DOUBLE_PIPE_CONNECTOR_SVG.icon()),
        Component("DPCnr", _img.DOUBLE_DOUBLE_PIPE_CONNECTOR_SVG.icon()),
        Component("TVentil", _img.T_VENTIL_SVG.icon()),
        Component("WTap_main", _img.TAP_MAINS_SVG.icon()),
        Component(_bnames.TAP, _img.TAP_SVG.icon()),
        Component("Pump", _img.PUMP_SVG.icon()),
        Component("Collector", _img.COLLECTOR_SVG.icon()),
        Component("GroundSourceHx", _img.GROUND_SOURCE_HX_SVG.icon()),
        Component("PV", _img.PV_SVG.icon()),
        Component("HP", _img.HP_SVG.icon()),
        Component("HPTwoHx", _img.HP_TWO_HX_SVG.icon()),
        Component("HPDoubleDual", _img.HP_DOUBLE_DUAL_SVG.icon()),
        Component("HPDual", _img.HP_DUAL_SVG.icon()),
        Component("AirSourceHP", _img.AIR_SOURCE_HP_SVG.icon()),
        Component("StorageTank", _img.STORAGE_TANK_SVG.icon()),
        Component("IceStorage", _img.ICE_STORAGE_SVG.icon()),
        Component("IceStorageTwoHx", _img.ICE_STORAGE_TWO_HX_SVG.icon()),
        Component("ExternalHx", _img.EXTERNAL_HX_SVG.icon()),
        Component("Radiator", _img.RADIATOR_SVG.icon()),
        Component("Boiler", _img.BOILER_SVG.icon()),
        Component("Sink", _img.SINK_SVG.icon()),
        Component("Source", _img.SOURCE_SVG.icon()),
        Component("SourceSink", _img.SOURCE_SINK_SVG.icon()),
        Component("Geotherm", _img.GEOTHERM_SVG.icon()),
        Component("Water", _img.WATER_SVG.icon()),
        Component("Crystalizer", _img.CRYSTALIZER_SVG.icon()),
        Component("CSP_CR", _img.CENTRAL_RECEVIER_SVG.icon()),
        Component("CSP_PT", _img.PT_FIELD_SVG.icon()),
        Component("powerBlock", _img.STEAM_POWER_BLOCK_SVG.icon()),
        Component("coldSaltTank", _img.SALT_TANK_COLD_SVG.icon()),
        Component("hotSaltTank", _img.SALT_TANK_HOT_SVG.icon()),
        Component("GenericBlock", _img.GENERIC_BLOCK_PNG.icon()),
        Component("GraphicalItem", _img.GENERIC_ITEM_PNG.icon()),
    ]


def getComponents() -> _warn.ValueWithWarnings[_cabc.Sequence[Component]]:
    pluginComponentsWithWarnings = _getPluginComponents()

    allComponents = [
        *_getHardCodedComponents(),
        *pluginComponentsWithWarnings.value,
    ]

    return pluginComponentsWithWarnings.withValue(allComponents)


def _getPluginComponents() -> (
    _warn.ValueWithWarnings[_cabc.Sequence[Component]]
):
    pluginFactory = _pfactory.Factory.createDefault()

    pluginComponentNames = pluginFactory.getTypeNames()

    pluginComponents = []
    namesOfComponentsWhichCouldntBeLoaded = []
    for pluginComponentName in pluginComponentNames:
        result = _createPluginComponent(pluginComponentName, pluginFactory)
        if _res.isError(result):
            namesOfComponentsWhichCouldntBeLoaded.append(pluginComponentName)
            error = _res.error(result).withContext(
                f"Could not load component {pluginComponentName}"
            )
            _LOGGER.error(error.message)
            continue
        pluginComponent = _res.value(result)

        pluginComponents.append(pluginComponent)

    if namesOfComponentsWhichCouldntBeLoaded:
        formattedNames = "\n".join(
            f"\t - {name}" for name in namesOfComponentsWhichCouldntBeLoaded
        )
        warning = f"""\
The following plugin components couldn't be loaded (see log file for details):
{formattedNames}

"""
    else:
        warning = None

    valueWithWarnings = _warn.ValueWithWarnings.create(
        pluginComponents, warning
    )
    return valueWithWarnings


def _createPluginComponent(
    pluginComponentName: str, pluginFactory: _pfactory.Factory
) -> _res.Result[Component]:
    result = pluginFactory.create(pluginComponentName)
    if _res.isError(result):
        return _res.error(result)
    plugin = _res.value(result)

    icon = plugin.graphics.accessor.icon()
    pluginComponent = Component(pluginComponentName, icon)
    return pluginComponent
