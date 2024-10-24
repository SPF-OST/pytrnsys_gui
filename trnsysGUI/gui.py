import logging as _log
import pathlib as _pl
import sys as _sys

import PyQt5.QtWidgets as _qtw

import pytrnsys.utils.log as _ulog
import pytrnsys.utils.result as _res
import trnsysGUI.arguments as _args
import trnsysGUI.setup as _setup
import trnsysGUI.warningsAndErrors as _werrors


def main():
    arguments = _args.getArgsOrExit()

    logFilePath = _getLogFilePath()
    logger = _ulog.getOrCreateCustomLogger("root", arguments.logLevel, logFilePath)

    _registerExceptionHook(logger)

    result = _setup.setup()
    errorMessage = _res.error(result).message if _res.isError(result) else None
    if errorMessage:
        logger.error(errorMessage)

    app = _qtw.QApplication(_sys.argv)
    app.setApplicationName("Diagram Creator")

    if errorMessage:
        _werrors.showMessageBox(errorMessage, title="Missing requirements")
        return

    import trnsysGUI.common.cancelled as _ccl  # pylint: disable=import-outside-toplevel
    import trnsysGUI.project as _prj  # pylint: disable=import-outside-toplevel

    maybeCancelled = _prj.getProject()
    if _ccl.isCancelled(maybeCancelled):
        return
    project = _ccl.value(maybeCancelled)

    import trnsysGUI.mainWindow as _mw  # pylint: disable=import-outside-toplevel

    mainWindow = _mw.MainWindow(logger, project)
    mainWindow.start()

    def _shutdownMainWindowIfRunning() -> None:
        if mainWindow.isRunning():
            mainWindow.shutdown()

    app.aboutToQuit.connect(_shutdownMainWindowIfRunning)

    try:
        mainWindow.showMaximized()
        mainWindow.ensureSettingsExist()
        mainWindow.loadTrnsysPath()

        import trnsysGUI.tracing as trc  # pylint: disable=import-outside-toplevel
        tracer = trc.createTracer(arguments.shallTrace)
        tracer.run(app.exec)
    finally:
        _shutdownMainWindowIfRunning()


def _getLogFilePath():
    return _pl.Path("pytrnsys-gui.log").absolute()


def _registerExceptionHook(logger: _log.Logger) -> None:
    def exceptionHook(exceptionType, value, traceback):
        logger.critical("Uncaught exception", exc_info=(exceptionType, value, traceback))

        for handler in logger.handlers:
            handler.flush()

        _sys.exit(-1)

    _sys.excepthook = exceptionHook


if __name__ == "__main__":
    main()
