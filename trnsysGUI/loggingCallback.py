__all__ = ["configureLoggingCallback"]

import logging as _log
import typing as _tp


def configureLoggingCallback(
    logger: _log.Logger, callback: "_Callback", formatString: _tp.Optional[str] = None
) -> None:
    callbackLogHandler = _CallbackLogHandler(callback)

    if formatString:
        formatter = _log.Formatter(fmt=formatString)
        callbackLogHandler.setFormatter(formatter)

    logger.addHandler(callbackLogHandler)


_Callback = _tp.Callable[[str], None]


class _CallbackLogHandler(_log.Handler):
    def __init__(self, callback: _Callback):
        super().__init__()
        self.callback = callback

    def emit(self, record: _log.LogRecord) -> None:
        message = self.format(record)
        self.callback(message)
