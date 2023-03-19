__all__ = ["QtConsoleWidget"]

import asyncio as _aio
import pathlib as _pl
import sys as _sys
import typing as _tp

import qtconsole.inprocess as _qtcip
import qtconsole.rich_jupyter_widget as _qtcjw
import qtconsole.client as _qtcc
import tornado as _tornado


class QtConsoleWidget(_qtcjw.RichJupyterWidget):  # pylint: disable=abstract-method,too-many-ancestors
    def __init__(self):
        super().__init__()
        self.kernel_manager: _tp.Optional[  # pylint: disable=invalid-name # /NOSONAR
            _qtcip.QtInProcessKernelManager
        ] = None
        self.kernel_client: _tp.Optional[_qtcc.KernelClient] = None  # pylint: disable=invalid-name # /NOSONAR

    def isRunning(self):
        return self.kernel_manager and self.kernel_client

    def startInFolder(self, dirPathToStartIPythonIn: _pl.Path) -> None:
        if self.isRunning():
            raise RuntimeError("Console has already been started.")

        self.kernel_manager = _qtcip.QtInProcessKernelManager()
        self.kernel_manager.start_kernel()
        self.kernel_manager.kernel.gui = "qt"

        _initAsyncIOPatch()

        self.kernel_client = self.kernel_manager.client()
        self.kernel_client.start_channels()

        self.execute(f"%cd {dirPathToStartIPythonIn}")

    def shutdown(self) -> None:
        if not self.isRunning():
            raise RuntimeError("Cannot shut down console which hasn't been started.")

        assert self.kernel_client and self.kernel_manager

        self.kernel_client.stop_channels()
        self.kernel_manager.shutdown_kernel()

        self.kernel_client = None
        self.kernel_manager = None


def _initAsyncIOPatch() -> None:
    """set default asyncio policy to be compatible with tornado
    Tornado 6 (at least) is not compatible with the default
    asyncio implementation on Windows
    Pick the older SelectorEventLoopPolicy on Windows
    if the known-incompatible default policy is in use.
    do this as early as possible to make it a low priority and overrideable
    ref: https://github.com/tornadoweb/tornado/issues/2608
    FIXME: if/when tornado supports the defaults in asyncio,
           remove and bump tornado requirement for py38
    """
    if _sys.platform.startswith("win") and _sys.version_info >= (3, 8) and _tornado.version_info < (6, 1):

        try:
            from asyncio import (  # type: ignore[attr-defined]  # pylint: disable=import-outside-toplevel
                WindowsProactorEventLoopPolicy,
                WindowsSelectorEventLoopPolicy,
            )
        except ImportError:
            pass
            # not affected
        else:
            if (
                type(_aio.get_event_loop_policy())  # pylint: disable=unidiomatic-typecheck
                is WindowsProactorEventLoopPolicy
            ):
                # WindowsProactorEventLoopPolicy is not compatible with tornado 6
                # fallback to the pre-3.8 default of Selector
                _aio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
