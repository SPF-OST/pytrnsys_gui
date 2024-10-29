__all__ = ["QtConsoleWidget"]

import pathlib as _pl
import typing as _tp

import qtconsole.client as _qtcc
import qtconsole.manager as _qtcm
import qtconsole.rich_jupyter_widget as _qtcjw


class QtConsoleWidget(
    _qtcjw.RichJupyterWidget
):  # pylint: disable=abstract-method,too-many-ancestors
    _KERNEL = "python3"

    def __init__(self) -> None:
        super().__init__()
        # pylint: disable=invalid-name # /NOSONAR
        self.kernel_manager: _tp.Optional[_qtcm.KernelManager] = None
        # pylint: disable=invalid-name # /NOSONAR
        self.kernel_client: _tp.Optional[_qtcc.QtKernelClient] = None

    def isRunning(self) -> bool:
        return bool(self.kernel_manager and self.kernel_client)

    def startInFolder(self, dirPathToStartIPythonIn: _pl.Path) -> None:
        if self.isRunning():
            raise RuntimeError("Console has already been started.")

        self.kernel_manager = _qtcm.QtKernelManager(self._KERNEL)
        self.kernel_manager.start_kernel()

        kernelClient = self.kernel_manager.client()
        kernelClient.start_channels()

        self.kernel_client = kernelClient

        self.execute(f"%cd {dirPathToStartIPythonIn}")

    def shutdown(self) -> None:
        if not self.isRunning():
            raise RuntimeError(
                "Cannot shut down console which hasn't been started."
            )

        assert self.kernel_client and self.kernel_manager

        self.kernel_client.stop_channels()
        self.kernel_manager.shutdown_kernel()

        self.kernel_client = None
        self.kernel_manager = None
