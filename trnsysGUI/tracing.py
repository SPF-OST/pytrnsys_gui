# pylint: skip-file
# type: ignore

import trace as _trc
import typing as _tp
import abc as _abc
import logging as _log
import sys as _sys

_TCo = _tp.TypeVar("_TCo")

__all__ = ["createTracer", "TracerBase"]

_logger = _log.getLogger("root")


class TracerBase(_abc.ABC):
    @_abc.abstractmethod
    def run(self, func: _tp.Callable[[], _TCo]) -> _TCo:
        pass


class _DummyTracer(TracerBase):
    def run(self, func: _tp.Callable[[], _TCo]) -> _TCo:
        return func()


class _Tracer(TracerBase):
    def __init__(self):
        ignoredirs = [_sys.prefix]
        self._trace = _trc.Trace(count=False, trace=True, timing=True, ignoredirs=ignoredirs)

    def run(self, func: _tp.Callable[[], _TCo]) -> _TCo:
        return self._trace.runfunc(func)


def createTracer(shallTrace: bool) -> TracerBase:
    if not shallTrace:
        _logger.debug("Tracing is DISABLED.")
        return _DummyTracer()

    _logger.info("Tracing is ENABLED.")
    return _Tracer()
