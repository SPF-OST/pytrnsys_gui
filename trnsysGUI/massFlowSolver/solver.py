import enum as _enum
import typing as _tp


class MassFlowSolver(_enum.StrEnum):
    """The value of the `massFlowSolver` project setting.

    A `StrEnum`, so that the project file stores the member's value.
    """

    JULIA = "julia"
    TYPE_9352 = "type9352"

    @property
    def trnsysTypeNumber(self) -> int:
        match self:
            case MassFlowSolver.JULIA:
                return 4750
            case MassFlowSolver.TYPE_9352:
                return 9352
            case _:
                _tp.assert_never(self)


# Label 1 of the Type 4750 unit: relative to the TRNSYS installation's
# `UserLib\ReleaseDLLs`, so that the deck works wherever TRNSYS is installed.
JULIA_SCRIPT_LABEL = "MassFlowSolver\\MassFlowSolver.jl"
