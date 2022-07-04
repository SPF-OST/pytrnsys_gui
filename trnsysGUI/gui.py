import sys as _sys

import PyQt5.QtWidgets as _qtw

import pytrnsys.utils.log as _log
import pytrnsys.utils.result as _res
import trnsysGUI.arguments as _args
import trnsysGUI.errors as _err
import trnsysGUI.setup as _setup


def main():
    arguments = _args.getArgsOrExit()

    logger = _log.setup_custom_logger("root", arguments.logLevel)

    result = _setup.setup()
    errorMessage = _res.error(result).message if _res.isError(result) else None
    if errorMessage:
        logger.error(errorMessage)

    app = _qtw.QApplication(_sys.argv)
    app.setApplicationName("Diagram Creator")

    if errorMessage:
        _err.showErrorMessageBox(errorMessage, title="Missing requirements")
        return

    import trnsysGUI.common.cancelled as _ccl  # pylint: disable=import-outside-toplevel
    import trnsysGUI.mainWindow as _mw  # pylint: disable=import-outside-toplevel
    import trnsysGUI.project as _prj  # pylint: disable=import-outside-toplevel
    import trnsysGUI.tracing as trc  # pylint: disable=import-outside-toplevel

    maybeCancelled = _prj.getProject()
    if _ccl.isCancelled(maybeCancelled):
        return
    project = _ccl.value(maybeCancelled)

    form = _mw.MainWindow(logger, project)
    form.showMaximized()
    form.show()
    form.ensureSettingsExist()
    form.loadTrnsysPath()

    tracer = trc.createTracer(arguments.shallTrace)
    tracer.run(app.exec)


if __name__ == "__main__":
    main()
