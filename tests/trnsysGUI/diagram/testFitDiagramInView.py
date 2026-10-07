import pathlib as _pl
import shutil as _sh

import PyQt5.QtWidgets as _qtw
import pytest as _pt

import pytrnsys.utils.log as _ulog

import trnsysGUI.mainWindow as _mw
import trnsysGUI.project as _prj

_EXAMPLES_DIR_PATH = _pl.Path(__file__).parents[3] / "data" / "examples"

_PROJECT_NAMES = ["solar_dhw_GUI", "SolarIceMfh"]


@_pt.mark.parametrize("projectName", _PROJECT_NAMES)
def testDiagramIsFittedIntoViewWhenOpened(
    projectName: str,
    tmp_path: _pl.Path,  # pylint: disable=invalid-name  # NOSONAR
    qtbot,
    monkeypatch,
) -> None:
    mainWindow = _showMainWindow(projectName, tmp_path, qtbot, monkeypatch)
    view = mainWindow.editor.diagramView

    qtbot.waitUntil(lambda: _isDiagramFittedIntoView(view))


@_pt.mark.parametrize("projectName", _PROJECT_NAMES)
def testZoomToFitAfterZoomingIn(
    projectName: str,
    tmp_path: _pl.Path,  # pylint: disable=invalid-name  # NOSONAR
    qtbot,
    monkeypatch,
) -> None:
    mainWindow = _showMainWindow(projectName, tmp_path, qtbot, monkeypatch)
    view = mainWindow.editor.diagramView
    qtbot.waitUntil(lambda: _isDiagramFittedIntoView(view))

    for _ in range(5):
        mainWindow.setZoomIn()
    assert not _isDiagramFittedIntoView(view)

    mainWindow.setZoomToFit()

    assert _isDiagramFittedIntoView(view)


def _showMainWindow(
    projectName: str, tmpPath: _pl.Path, qtbot, monkeypatch
) -> _mw.MainWindow:  # type: ignore[name-defined]
    projectDirPath = tmpPath / projectName
    (projectDirPath / "ddck").mkdir(parents=True)
    jsonFileName = f"{projectName}.json"
    _sh.copy(_EXAMPLES_DIR_PATH / projectName / jsonFileName, projectDirPath)

    monkeypatch.setattr(
        _qtw.QMessageBox,
        _qtw.QMessageBox.warning.__name__,  # pylint: disable=no-member
        lambda *_, **__: _qtw.QMessageBox.Ok,
    )

    logger = _ulog.getOrCreateCustomLogger("root", "INFO")  # type: ignore[attr-defined]
    project = _prj.LoadProject(projectDirPath / jsonFileName)
    mainWindow = _mw.MainWindow(logger, project)  # type: ignore[attr-defined]
    qtbot.addWidget(mainWindow)
    mainWindow.showBoxOnClose = False

    mainWindow.resize(1200, 800)
    mainWindow.show()
    qtbot.waitExposed(mainWindow)

    return mainWindow


def _isDiagramFittedIntoView(view: _qtw.QGraphicsView) -> bool:
    diagramRect = view.getDiagramSceneRect()  # type: ignore[attr-defined]
    visibleRect = view.mapToScene(view.viewport().rect()).boundingRect()

    isFullyVisible = visibleRect.contains(diagramRect)

    widthFraction = diagramRect.width() / visibleRect.width()
    heightFraction = diagramRect.height() / visibleRect.height()
    fillsView = max(widthFraction, heightFraction) > 0.85

    return isFullyVisible and fillsView
