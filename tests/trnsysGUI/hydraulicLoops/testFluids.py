import re as _re

import trnsysGUI.hydraulicLoops._dialogs.edit.dialog as _dialog
import trnsysGUI.hydraulicLoops._dialogs.edit.model as _gmodel
import trnsysGUI.hydraulicLoops.fluidLibrary as _lib
import trnsysGUI.hydraulicLoops.model as _model


def testLibraryFluidNamesAreValidUniqueAndNotBuiltIn() -> None:
    names = [f.name for f in _lib.LIBRARY_FLUIDS]

    assert all(_re.match(r"^[A-Za-z][A-Za-z0-9_]*$", n) for n in names)
    assert len({n.lower() for n in names}) == len(names)
    assert not set(names) & set(_lib.BUILT_IN_DESCRIPTIONS)
    assert all(
        f.specificHeatCapacityInJPerKgK > 0 and f.densityInKgPerM3 > 0
        for f in _lib.LIBRARY_FLUIDS
    )


def testOwnFluidsAreSavedAndLoadedWithTheDiagram() -> None:
    ownFluid = _lib.LIBRARY_FLUIDS[0].createFluid()
    fluids = _model.Fluids([ownFluid])

    loaded = _model.Fluids.createFromJson(fluids.toJson())

    assert [f.name for f in loaded.fluids] == [
        "brine",
        ownFluid.name,
        "water",
    ]
    loadedOwnFluid = loaded.getFluid(ownFluid.name)
    assert loadedOwnFluid
    assert loadedOwnFluid.to_dict() == ownFluid.to_dict()
    # fluids are compared by identity: new pipes take the water of this diagram
    assert loaded.getDefaultFluid() is loaded.getFluid("water")


def testDiagramWithoutFluidsHasTheBuiltInOnes() -> None:
    loaded = _model.Fluids.createFromJson([])

    assert [f.name for f in loaded.fluids] == ["brine", "water"]
    water = loaded.getDefaultFluid()
    assert water.densityInKgPerM3 == 998.0
    assert water.thermalConductivityInWPerMK == 0.58


def testEditedWaterIsKeptAndUsedForNewPipes() -> None:
    water = _lib.WATER.createFluid()
    edited = type(water)(
        "water",
        specificHeatCapacityInJPerKgK=4180.0,
        densityInKgPerM3=992.0,
        thermalConductivityInWPerMK=0.63,
        dynamicViscosityInPaS=0.65e-3,
    )

    loaded = _model.Fluids.createFromJson(_model.Fluids([edited]).toJson())

    default = loaded.getDefaultFluid()
    assert default.densityInKgPerM3 == 992.0
    assert default.dynamicViscosityInPaS == 0.65e-3


def testFluidsSavedWithoutConductivityAndViscosityGetWaterValues() -> None:
    oldJson: list[dict] = [
        {
            "name": "myOil",
            "specificHeatCapacityInJPerKgK": 2100.0,
            "densityInKgPerM3": 880.0,
            "__version__": "5b1d8eb8-e9c0-4c6a-b14f-0a7216b60132",
        },
        {
            "name": "brine",
            "specificHeatCapacityInJPerKgK": {
                "name": "CPBRI_SI",
                "__version__": "3196024b-6775-42bc-92d2-e11d60c64bac",
            },
            "densityInKgPerM3": {
                "name": "RHOBRI",
                "__version__": "3196024b-6775-42bc-92d2-e11d60c64bac",
            },
            "__version__": "5b1d8eb8-e9c0-4c6a-b14f-0a7216b60132",
        },
    ]

    loaded = _model.Fluids.createFromJson(oldJson)

    myOil = loaded.getFluid("myOil")
    assert myOil
    assert myOil.thermalConductivityInWPerMK == 0.58
    assert myOil.dynamicViscosityInPaS == 1.0e-3
    brine = loaded.getFluid("brine")
    assert brine and brine.thermalConductivityInWPerMK == 0.40


def testPipeDiameterIsEnteredInMillimetresAndStoredInCentimetres() -> None:
    connection = _gmodel.Connection(
        "pipe",
        diameterInCm=1.0,
        uValueInWPerM2K=1.0,
        lengthInM=1.0,
        shallBeSimulated=True,
        connection=None,  # type: ignore[arg-type]
    )

    # pylint: disable=protected-access
    _dialog._setConnectionDiameter(connection, "200")

    assert connection.diameterInCm == 20.0
