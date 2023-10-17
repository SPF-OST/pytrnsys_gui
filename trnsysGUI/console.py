__all__ = ["QtConsoleWidget"]

import pathlib as _pl
import sys as _sys
import typing as _tp

import ipykernel.kernelspec as _ipyksp
import jupyter_client.kernelspec as _jcksp
import qtconsole.client as _qtcc
import qtconsole.manager as _qtcm
import qtconsole.rich_jupyter_widget as _qtcjw

import trnsysGUI.pyinstaller as _pyinst


class QtConsoleWidget(_qtcjw.RichJupyterWidget):  # pylint: disable=abstract-method,too-many-ancestors
    _KERNEL = "python3"

    def __init__(self) -> None:
        super().__init__()
        self.kernel_manager: _tp.Optional[_qtcm.KernelManager] = None  # pylint: disable=invalid-name # /NOSONAR
        self.kernel_client: _tp.Optional[_qtcc.KernelClient] = None  # pylint: disable=invalid-name # /NOSONAR

    def isRunning(self) -> bool:
        return bool(self.kernel_manager and self.kernel_client)

    def startInFolder(self, dirPathToStartIPythonIn: _pl.Path) -> None:
        if self.isRunning():
            raise RuntimeError("Console has already been started.")

        self.kernel_manager = _qtcm.QtKernelManager(self._KERNEL, kernel_spec_manager=_KernelSpecManager())
        self.kernel_manager.start_kernel()

        kernelClient = self.kernel_manager.client()
        kernelClient.start_channels()

        self.kernel_client = kernelClient

        self.execute(f"%cd {dirPathToStartIPythonIn}")

    def shutdown(self) -> None:
        if not self.isRunning():
            raise RuntimeError("Cannot shut down console which hasn't been started.")

        assert self.kernel_client and self.kernel_manager

        self.kernel_client.stop_channels()
        self.kernel_manager.shutdown_kernel()

        self.kernel_client = None
        self.kernel_manager = None


class _KernelSpecManager(_jcksp.KernelSpecManager):
    def get_kernel_spec(self, kernel_name: str) -> _jcksp.KernelSpec:  # /NOSONAR
        if kernel_name != _jcksp.NATIVE_KERNEL_NAME:
            raise _jcksp.NoSuchKernel(kernel_name)

        return _jcksp.KernelSpec(_ipyksp.RESOURCES, **_getKernelDict())

    def get_all_specs(self) -> _tp.Mapping[str, _tp.Any]:
        return {_jcksp.NATIVE_KERNEL_NAME: {"resource_dir": _ipyksp.RESOURCES, "spec": _getKernelDict()}}

    def find_kernel_specs(self) -> _tp.Mapping[str, str]:
        return {_jcksp.NATIVE_KERNEL_NAME: _ipyksp.RESOURCES}

    def remove_kernel_spec(self, name):  # /NOSONAR
        raise NotImplementedError()

    def install_kernel_spec(self, source_dir, kernel_name=None, user=False, replace=None, prefix=None):  # /NOSONAR
        raise NotImplementedError()

    def install_native_kernel_spec(self, user=False):  # /NOSONAR
        raise NotImplementedError()


def _getKernelDict() -> _tp.Mapping[str, _tp.Any]:
    if _pyinst.isRunAsPyInstallerExe():
        dirContainingExes = _pl.Path(_sys.executable).parent
        ipykernelLauncherExePath = dirContainingExes / "launchIPythonKernel.exe"

        argv = [str(ipykernelLauncherExePath), "-f", "{connection_file}"]
    else:
        argv = ["python", "-m", "ipykernel_launcher", "-f", "{connection_file}"]

    return {
        "argv": argv,
        "display_name": "Python 3 (ipykernel)",
        "language": "python",
        "metadata": {"debugger": True},
    }
