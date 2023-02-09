__all__ = ["configureLoggingCallback"]

import logging as _log
import typing as _tp


def configureLoggingCallback(logger: _log.Logger, callback: "_Callback", format: _tp.Optional[str] = None) -> None:
    callbackLogHandler = _CallbackLogHandler(callback)

    if format:
        formatter = _log.Formatter(fmt=format)
        callbackLogHandler.setFormatter(formatter)

    logger.addHandler(callbackLogHandler)


_Callback = _tp.Callable[[str], None]


class _CallbackLogHandler(_log.Handler):
    def __init__(self, callback: _Callback):
        super().__init__()
        self._callback = callback

    def emit(self, record: _log.LogRecord) -> None:
        message = self.format(record)
        self._callback(message)
