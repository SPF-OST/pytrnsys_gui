import sys as _sys


def isRunAsPyInstallerExe() -> bool:
    isRunAsPyinstallerExe = getattr(_sys, "frozen", False) and hasattr(_sys, "_MEIPASS")
    return isRunAsPyinstallerExe
