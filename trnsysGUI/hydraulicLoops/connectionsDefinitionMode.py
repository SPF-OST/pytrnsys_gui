import enum as _enum


class ConnectionsDefinitionMode(_enum.Enum):
    INDIVIDUAL = _enum.auto()
    LOOP_WIDE_DEFAULTS = _enum.auto()
    DUMMY_PIPES = _enum.auto()

    def useLoopWideDefaults(self) -> bool:
        return self == self.LOOP_WIDE_DEFAULTS
