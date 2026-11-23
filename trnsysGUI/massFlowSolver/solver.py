import typing as _tp

MassFlowSolver = _tp.Literal["julia", "type9352"]

JULIA: MassFlowSolver = "julia"
TYPE_9352: MassFlowSolver = "type9352"

TRNSYS_TYPE_NUMBERS: _tp.Mapping[MassFlowSolver, int] = {
    JULIA: 4750,
    TYPE_9352: 9352,
}

# Label 1 of the Type 4750 unit: relative to the TRNSYS installation's
# `UserLib\ReleaseDLLs`, so that the deck works wherever TRNSYS is installed.
JULIA_SCRIPT_LABEL = "MassFlowSolver\\MassFlowSolver.jl"


def getTrnsysTypeNumber(massFlowSolver: MassFlowSolver) -> int:
    return TRNSYS_TYPE_NUMBERS[massFlowSolver]
