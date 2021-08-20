# pylint: skip-file
# type: ignore

import argparse as _ap
import dataclasses as _dc


__all__ = ["getArgsOrExit", "Arguments"]


def getArgsOrExit() -> "Arguments":
    logLevels = "CRITICAL ERROR WARNING INFO DEBUG".split()

    parser = _ap.ArgumentParser()
    parser.add_argument("-l", "--log", default="INFO", choices=logLevels, help="Set the log level", metavar="LEVEL")
    parser.add_argument("-t", "--trace", action="store_true", help="Enable tracing")

    namespace = parser.parse_args()
    logLevel = namespace.log
    shallTrace = namespace.trace

    return Arguments(logLevel, shallTrace)


@_dc.dataclass(frozen=True)
class Arguments:
    logLevel: str
    shallTrace: bool
