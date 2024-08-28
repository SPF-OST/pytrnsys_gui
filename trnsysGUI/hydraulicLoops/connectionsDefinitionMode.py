import enum as _enum


class ConnectionsDefinitionMode(_enum.Enum):
    INDIVIDUAL = "individual"
    LOOP_WIDE_DEFAULTS = "loop-wide-defaults"
    DUMMY_PIPES = "dummy-pipes"

    def useLoopWideDefaults(self) -> bool:
        return self == self.LOOP_WIDE_DEFAULTS
