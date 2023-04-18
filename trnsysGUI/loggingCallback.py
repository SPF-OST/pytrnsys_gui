__all__ = ["configureLoggingCallback"]

import logging as _log
import typing as _tp

import trnsysGUI.common as _com


def configureLoggingCallback(
    logger: _log.Logger, callback: "_Callback", formatString: _tp.Optional[str] = None
) -> None:
    if _hasCallback(logger, callback):
        raise ValueError("Cannot add same callback to logger twice.")

    callbackLogHandler = _CallbackLogHandler(callback)

    if formatString:
        formatter = _log.Formatter(fmt=formatString)
        callbackLogHandler.setFormatter(formatter)

    logger.addHandler(callbackLogHandler)


def _hasCallback(logger: _log.Logger, callback: "_Callback") -> bool:
    handlers = _getHandlersForCallback(logger, callback)
    return any(handlers)


def _getHandlersForCallback(logger: _log.Logger, callback: "_Callback") -> _tp.Sequence[_log.Handler]:
    return [h for h in logger.handlers if isinstance(h, _CallbackLogHandler) and h.callback == callback]


def removeLoggingCallback(logger: _log.Logger, callback: "_Callback") -> None:
    handlers = _getHandlersForCallback(logger, callback)
    handler = _com.getSingle(handlers)
    logger.removeHandler(handler)


_Callback = _tp.Callable[[str], None]


class _CallbackLogHandler(_log.Handler):
    def __init__(self, callback: _Callback):
        super().__init__()
        self.callback = callback

    def emit(self, record: _log.LogRecord) -> None:
        message = self.format(record)
        self.callback(message)
