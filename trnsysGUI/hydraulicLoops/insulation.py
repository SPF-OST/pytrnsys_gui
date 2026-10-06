import dataclasses as _dc
import typing as _tp

# Insulation materials with a thermal conductivity up to this value may use
# the thinner insulation thicknesses.
LOW_THERMAL_CONDUCTIVITY_LIMIT_IN_W_PER_M_K = 0.03


@_dc.dataclass(frozen=True)
class _ThicknessClass:
    smallestNominalDiameter: int
    thicknessForLowConductivityInMm: int
    thicknessForHighConductivityInMm: int


# Minimum insulation thicknesses of heating and hot water pipes as a
# function of the nominal diameter (DN) and of the thermal conductivity of
# the insulation material (<= 0.03 W/(m*K) and > 0.03 to <= 0.05 W/(m*K)).
# See Kanton Zürich, "Wärmedämmvorschriften", Ausgabe 2009, Tabelle 6
# "Minimale Dämmstärke für Heizungs- und Warmwasserleitungen" (based on the
# MuKEn and SIA 380/1 / SIA 384/1:2009).
_THICKNESS_CLASSES: _tp.Sequence[_ThicknessClass] = [
    _ThicknessClass(10, 30, 40),  # DN 10 - 15
    _ThicknessClass(20, 40, 50),  # DN 20 - 32
    _ThicknessClass(40, 50, 60),  # DN 40 - 50
    _ThicknessClass(65, 60, 80),  # DN 65 - 80
    _ThicknessClass(100, 80, 100),  # DN 100 - 150
    _ThicknessClass(175, 80, 120),  # DN 175 - 200
]


def getMinimumInsulationThicknessInMmExpression(
    nominalDiameterName: str, thermalConductivityName: str
) -> str:
    """Returns a TRNSYS expression for the minimum insulation thickness in mm

    The nominal diameter is taken to be the inner diameter in mm. Diameters
    falling between two DN classes are assigned to the smaller class, and
    diameters outside the table are assigned to the nearest class.
    """

    lowConductivityExpression = _getStepExpression(
        nominalDiameterName,
        lambda c: c.thicknessForLowConductivityInMm,
    )

    highConductivityExpression = _getStepExpression(
        nominalDiameterName,
        lambda c: c.thicknessForHighConductivityInMm,
    )

    limit = LOW_THERMAL_CONDUCTIVITY_LIMIT_IN_W_PER_M_K
    return (
        f"LE({thermalConductivityName},{limit})*({lowConductivityExpression})"
        f"+GT({thermalConductivityName},{limit})*({highConductivityExpression})"
    )


def _getStepExpression(
    nominalDiameterName: str,
    getThicknessInMm: _tp.Callable[[_ThicknessClass], int],
) -> str:
    firstClass, *otherClasses = _THICKNESS_CLASSES

    terms = [str(getThicknessInMm(firstClass))]
    previousThicknessInMm = getThicknessInMm(firstClass)
    for thicknessClass in otherClasses:
        thicknessInMm = getThicknessInMm(thicknessClass)
        increaseInMm = thicknessInMm - previousThicknessInMm
        if increaseInMm:
            terms.append(
                f"{increaseInMm}*GE({nominalDiameterName},{thicknessClass.smallestNominalDiameter})"
            )
        previousThicknessInMm = thicknessInMm

    return "+".join(terms)
