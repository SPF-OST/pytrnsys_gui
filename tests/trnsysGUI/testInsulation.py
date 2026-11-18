import pytest as _pt

import trnsysGUI.hydraulicLoops.insulation as _ins


def _evaluateTrnsysExpression(
    expression: str, nominalDiameter: float, thermalConductivity: float
) -> float:
    variables = {
        "DN": nominalDiameter,
        "LamIns": thermalConductivity,
        "GE": lambda x, y: float(x >= y),
        "GT": lambda x, y: float(x > y),
        "LE": lambda x, y: float(x <= y),
    }
    return eval(expression, {}, variables)  # pylint: disable=eval-used


@_pt.mark.parametrize(
    "nominalDiameter, thicknessForLowConductivity, thicknessForHighConductivity",
    [
        (5, 30, 40),
        (10, 30, 40),
        (15, 30, 40),
        (19.9, 30, 40),
        (20, 40, 50),
        (32, 40, 50),
        (40, 50, 60),
        (50, 50, 60),
        (65, 60, 80),
        (80, 60, 80),
        (100, 80, 100),
        (150, 80, 100),
        (175, 80, 120),
        (200, 80, 120),
        (300, 80, 120),
    ],
)
def testMinimumInsulationThickness(
    nominalDiameter: float,
    thicknessForLowConductivity: float,
    thicknessForHighConductivity: float,
) -> None:
    expression = _ins.getMinimumInsulationThicknessInMmExpression(
        "DN", "LamIns"
    )

    assert (
        _evaluateTrnsysExpression(expression, nominalDiameter, 0.03)
        == thicknessForLowConductivity
    )
    assert (
        _evaluateTrnsysExpression(expression, nominalDiameter, 0.035)
        == thicknessForHighConductivity
    )
