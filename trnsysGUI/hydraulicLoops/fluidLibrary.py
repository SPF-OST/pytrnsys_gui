"""Library of fluids that can be added to a diagram (Project -> Fluids...).

The properties are constants (one value per fluid at the reference temperature given in the description). The
values are typical values: check them against the data sheet of the fluid used and edit them in the diagram if
needed. The built-in `water` and `brine` (Tyfocor LS) have the values of head.ddck (`RHOWAT`, `CPWAT`, `LAMWAT`,
`RHOBRI`, `CPBRI`).
"""

from __future__ import annotations

import dataclasses as _dc
import typing as _tp

from . import _serialization as _ser


@_dc.dataclass(frozen=True)
class LibraryFluid:  # pylint: disable=too-many-instance-attributes
    name: str
    specificHeatCapacityInJPerKgK: float
    densityInKgPerM3: float
    thermalConductivityInWPerMK: float
    dynamicViscosityInPaS: float
    description: str

    def createFluid(self) -> _ser.Fluid:
        return _ser.Fluid(
            self.name,
            specificHeatCapacityInJPerKgK=self.specificHeatCapacityInJPerKgK,
            densityInKgPerM3=self.densityInKgPerM3,
            thermalConductivityInWPerMK=self.thermalConductivityInWPerMK,
            dynamicViscosityInPaS=self.dynamicViscosityInPaS,
        )


WATER = LibraryFluid(
    "water",
    4190.0,
    998.0,
    0.58,
    1.0e-3,
    "Water, 20 degC (head.ddck: RHOWAT, CPWAT, LAMWAT)",
)
BRINE = LibraryFluid(
    "brine",
    3816.0,
    1016.0,
    0.40,
    2.3e-3,
    "Propylene glycol Tyfocor LS, 55 degC (head.ddck: RHOBRI, CPBRI; conductivity and viscosity typical values)",
)

LIBRARY_FLUIDS: _tp.Sequence[LibraryFluid] = (
    LibraryFluid(
        "ethyleneGlycol30",
        3680.0,
        1040.0,
        0.48,
        2.2e-3,
        "Ethylene glycol 30 % (vol.) in water, 20 degC (typical values)",
    ),
    LibraryFluid(
        "propyleneGlycol40",
        3700.0,
        1035.0,
        0.42,
        4.5e-3,
        "Propylene glycol 40 % (vol.) in water, 20 degC (typical values)",
    ),
    LibraryFluid(
        "air",
        1006.0,
        1.204,
        0.0257,
        1.81e-5,
        "Dry air, 20 degC, 1 atm",
    ),
    LibraryFluid(
        "thermalOil",
        2050.0,
        920.0,
        0.106,
        1.5e-3,
        "Synthetic heat transfer oil (e.g. Therminol 66), 150 degC (typical values)",
    ),
)

BUILT_IN_DESCRIPTIONS = {
    WATER.name: WATER.description,
    BRINE.name: BRINE.description,
}
