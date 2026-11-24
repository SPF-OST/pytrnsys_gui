import types as _types

import pydantic as _pc
import pytest as _pt

import pytrnsys.utils.result as _res

import trnsysGUI.components.plugin.factory as _pfactory
import trnsysGUI.components.plugin.specification.model as _model
import trnsysGUI.electrical.connection as _econn
import trnsysGUI.electrical.export as _eexp


def testAllPluginSpecificationsLoad() -> None:
    factory = _pfactory.Factory.createDefault()
    for typeName in factory.getTypeNames():
        result = factory.create(typeName)
        assert not _res.isError(result), typeName


def testElectricalNodeHasSourcesAndTenDemands() -> None:
    plugin = _res.value(_pfactory.Factory.createDefault().create("EBNODE"))

    names = [t.name for t in plugin.electricalTerminals]
    directions = {t.name: t.direction for t in plugin.electricalTerminals}

    assert names == ["PvBat", "Bat", "Grid", *[f"D{i}" for i in range(1, 11)]]
    assert directions["PvBat"] == "in"
    assert directions["Bat"] == directions["Grid"] == "bi"
    assert directions["D10"] == "out"


def testSpecificationWithOnlyElectricalTerminalsIsValid() -> None:
    specification = _model.Specification.model_validate(
        {
            "defaultName": "inv",
            "description": "Inverter",
            "size": (120, 120),
            "electrical-terminals": [{"name": "Pv", "position": (0, 60)}],
        }
    )
    assert specification.electricalTerminals
    assert specification.electricalTerminals[0].direction == "bi"


def testSpecificationWithoutAnyConnectionIsInvalid() -> None:
    with _pt.raises(_pc.ValidationError):
        _model.Specification(defaultName="x", description="x", size=(120, 120))


@_pt.mark.parametrize("name", ["pv", "Pv_1", "", "P v"])
def testInvalidTerminalNames(name: str) -> None:
    with _pt.raises(_pc.ValidationError):
        _model.ElectricalTerminal(name=name, position=(0, 0))


def testVariableNameAndNameValidation() -> None:
    assert _econn.getVariableName("inv_ebNode") == "PelInv_ebNode"

    existing = [_types.SimpleNamespace(name="inv_ebNode")]
    assert _econn.getProblemWithName("ok_Name2", existing) is None  # type: ignore[arg-type]
    assert _econn.getProblemWithName("inv_ebNode", existing)  # type: ignore[arg-type]
    assert _econn.getProblemWithName("2abc", existing)  # type: ignore[arg-type]


def testElectricalDdckListsConnectionsAndPrintsTheirPowers() -> None:
    def terminal(qualifiedName: str) -> _types.SimpleNamespace:
        return _types.SimpleNamespace(qualifiedName=qualifiedName)

    connection = _types.SimpleNamespace(
        name="inv_ebNode",
        variableName="PelInv_ebNode",
        fromTerminal=terminal("inv.Dem"),
        toTerminal=terminal("ebNode.PvBat"),
    )
    editor = _types.SimpleNamespace(electricalConnections=[connection])

    content = _eexp.createElectricalDdck(editor, "project")

    assert "** PelInv_ebNode  inv.Dem -> ebNode.PvBat" in content
    assert "ASSIGN project_Pel.prt unitPrintElectrical" in content
    assert "INPUTS 1\nPelInv_ebNode\n***\nPelInv_ebNode\n" in content


@_pt.mark.parametrize(
    "selectedFile",
    [r"C:\run\results\sim\sim_Mfr.prt", r"C:\run\results\sim\sim_Pel.prt"],
)
def testVisualizerFindsAllPrintersOfTheRun(selectedFile: str) -> None:
    import trnsysGUI.mainWindow as _mw  # pylint: disable=import-outside-toplevel

    base = r"C:\run\results\sim\sim_"
    # pylint: disable=protected-access
    getFiles = _mw._getVisualizerFiles  # type: ignore[attr-defined]
    assert getFiles(selectedFile) == (
        base + "Mfr.prt",
        base + "T.prt",
        base + "Pel.prt",
    )
