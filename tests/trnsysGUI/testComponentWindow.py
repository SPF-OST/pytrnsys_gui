# pylint: disable=protected-access
# pylint: disable=invalid-name  # `tmp_path` fixture
import pathlib as _pl
import shutil as _sh

import PyQt5.QtWidgets as _qtw
import pytest as _pt

import pytrnsys.utils.log as _ulog
import trnsysGUI.componentWindow.window as _cw
import trnsysGUI.mainWindow as _mw
import trnsysGUI.project as _prj

_EXAMPLE_DIR_PATH = (
    _pl.Path(__file__).parents[2] / "data" / "examples" / "solar_dhw_GUI"
)

_RUN_CONFIG = """\
string PROJECT$ "ddck"
PROJECT$ generic/head
PROJECT$ Collector/type1 # the collector
PROJECT$ generic/end
"""


@_pt.fixture(name="mainWindow")
def _mainWindow(tmp_path, qtbot, monkeypatch) -> _mw.MainWindow:
    projectDirPath = tmp_path / "solar_dhw_GUI"
    (projectDirPath / "ddck" / "Collector").mkdir(parents=True)
    (projectDirPath / "ddck" / "Collector" / "type1.ddck").write_text("")
    _sh.copy(_EXAMPLE_DIR_PATH / "solar_dhw_GUI.json", projectDirPath)
    (projectDirPath / "run.config").write_text(_RUN_CONFIG)

    monkeypatch.setattr(
        _qtw.QMessageBox, "warning", lambda *_, **__: _qtw.QMessageBox.Ok
    )

    logger = _ulog.getOrCreateCustomLogger("root", "DEBUG")
    project = _prj.LoadProject(projectDirPath / "solar_dhw_GUI.json")
    mainWindow = _mw.MainWindow(logger, project)
    mainWindow.showBoxOnClose = False  # no "save?" question on teardown
    qtbot.addWidget(mainWindow)
    return mainWindow


def _getItem(mainWindow, typeName: str):
    return next(
        o for o in mainWindow.editor.trnsysObj if type(o).__name__ == typeName
    )


def _createWindow(mainWindow, item, qtbot) -> _cw.ComponentWindow:
    editor = mainWindow.editor
    window = _cw.ComponentWindow(
        item,
        _pl.Path(editor.projectFolder),
        editor._createRenameHelper(),
        editor=editor,
        libraryDirPath=_pl.Path(editor.projectFolder),
    )
    qtbot.addWidget(window)
    return window


@_pt.mark.parametrize(
    "typeName, expectedTabs",
    [
        ("Collector", ["General", "ddcks"]),
        ("Pump", ["General", "Mass flow"]),
        ("TVentil", ["General", "Valve"]),
        ("StorageTank", ["General", "Tank", "ddcks"]),
        ("TeePiece", ["General"]),
    ],
)
def testTabsDependOnComponent(mainWindow, qtbot, typeName, expectedTabs):
    window = _createWindow(mainWindow, _getItem(mainWindow, typeName), qtbot)

    assert window.tabTitles == expectedTabs


def testRenameMovesDdckFolderAndConfigLines(mainWindow, qtbot):
    collector = _getItem(mainWindow, "Collector")
    projectDirPath = _pl.Path(mainWindow.editor.projectFolder)
    window = _createWindow(mainWindow, collector, qtbot)

    window._nameLineEdit.setText("Coll")
    window.accept()

    assert collector.displayName == "Coll"
    assert (projectDirPath / "ddck" / "Coll" / "type1.ddck").is_file()
    assert not (projectDirPath / "ddck" / "Collector").exists()
    assert (projectDirPath / "run.config").read_text() == _RUN_CONFIG.replace(
        "Collector/type1", "Coll/type1"
    )


def testCancelRevertsFlips(mainWindow, qtbot):
    collector = _getItem(mainWindow, "Collector")
    flippedH = collector.flippedH
    window = _createWindow(mainWindow, collector, qtbot)

    window._flipHCheckBox.setChecked(not flippedH)
    assert collector.flippedH != flippedH  # preview

    window.reject()

    assert collector.flippedH == flippedH


def testMassFlowAppliedOnOkOnly(mainWindow, qtbot):
    pump = _getItem(mainWindow, "Pump")
    oldMassFlow = pump.massFlowRateInKgPerH

    window = _createWindow(mainWindow, pump, qtbot)
    window._pages[0]._lineEdit.setText("123.5")
    window.reject()
    assert pump.massFlowRateInKgPerH == oldMassFlow

    window = _createWindow(mainWindow, pump, qtbot)
    window._pages[0]._lineEdit.setText("123.5")
    window.accept()
    assert pump.massFlowRateInKgPerH == 123.5


def testValve(mainWindow, qtbot):
    valve = _getItem(mainWindow, "TVentil")
    window = _createWindow(mainWindow, valve, qtbot)
    page = window._pages[0]

    page._temperingCheckBox.setChecked(False)
    page._positionSpinBox.setValue(0.3)
    window.accept()

    assert not valve.isTempering
    assert valve.positionForMassFlowSolver == 0.3
    assert valve.posLabel.toPlainText() == "0.3"


def testInvalidNameKeepsWindowOpen(mainWindow, qtbot):
    collector = _getItem(mainWindow, "Collector")
    otherName = _getItem(mainWindow, "Pump").displayName
    window = _createWindow(mainWindow, collector, qtbot)
    window.show()

    window._nameLineEdit.setText(otherName)
    window.accept()

    assert window.isVisible()
    assert collector.displayName == "Collector"


def testHeatExchangerHasOnlyName(mainWindow, qtbot):
    heatExchanger = _getItem(mainWindow, "StorageTank").heatExchangers[0]
    window = _createWindow(mainWindow, heatExchanger, qtbot)

    window._nameLineEdit.setText("NewHx")
    window.accept()

    assert window.tabTitles == ["General"]
    assert heatExchanger.displayName == "NewHx"
