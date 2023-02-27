__all__ = ["createConsoleWidget"]

import asyncio as _aio
import pathlib as _pl
import sys as _sys

import PyQt5.QtWidgets as _qtw
import qtconsole.inprocess as _gtcip
import qtconsole.rich_jupyter_widget as _qtcjw
import tornado as _tornado


def createConsoleWidget(projectFolderToStartIPythonIn: _pl.Path) -> _qtw.QWidget:
    kernelManager = _gtcip.QtInProcessKernelManager()
    kernelManager.start_kernel()
    kernel = kernelManager.kernel
    kernel.gui = "qt"

    _initAsyncIOPatch()

    kernelClient = kernelManager.client()
    kernelClient.start_channels()

    def stop():
        kernelClient.stop_channels()
        kernelManager.shutdown_kernel()

    widget = _qtcjw.RichJupyterWidget()
    widget.kernel_manager = kernelManager
    widget.kernel_client = kernelClient
    widget.exit_requested.connect(stop)
    widget.execute(f"%cd {projectFolderToStartIPythonIn}")

    return widget


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
                type(_aio.get_event_loop_policy())
                is WindowsProactorEventLoopPolicy  # pylint: disable=unidiomatic-typecheck
            ):
                # WindowsProactorEventLoopPolicy is not compatible with tornado 6
                # fallback to the pre-3.8 default of Selector
                _aio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
