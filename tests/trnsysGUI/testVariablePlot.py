# pylint: disable=too-many-lines
import pathlib as _pl
import types as _types
import typing as _tp

import matplotlib.dates as _mdates
import pandas as _pd
import pytest as _pt
import PyQt5.QtCore as _qtc
from PyQt5.QtWidgets import QMessageBox

import trnsysGUI.variablePlot as vp


class TestDetectHeaderRowIndex:
    def testHeaderOnFirstLine(
        self, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        filePath = tmp_path / "simple.prt"
        filePath.write_text("TIME\tvar1\n0.0\t1.0\n1.0\t2.0\n")

        assert (
            vp._detectHeaderRowIndex(  # pylint: disable=protected-access
                filePath
            )
            == 0
        )

    def testHeaderWithJunkRowsAbove(
        self, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        filePath = tmp_path / "junk.prt"
        filePath.write_text(
            "Label not available\tLabel not available\n"
            "TIME\tvar1\n"
            "0.0\t1.0\n"
        )

        assert (
            vp._detectHeaderRowIndex(  # pylint: disable=protected-access
                filePath
            )
            == 1
        )

    def testNoNumericRowFallsBackToZero(
        self, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        filePath = tmp_path / "noNumeric.prt"
        filePath.write_text("TIME\tvar1\nfoo\tbar\n")

        assert (
            vp._detectHeaderRowIndex(  # pylint: disable=protected-access
                filePath
            )
            == 0
        )


class TestReadVariableNames:
    def testReturnsColumnNamesExceptTime(
        self, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        filePath = tmp_path / "result.prt"
        filePath.write_text("TIME\tT1\tT2\n0.0\t10.0\t20.0\n")

        names = vp._readVariableNames(  # pylint: disable=protected-access
            filePath
        )

        assert list(names) == ["T1", "T2"]

    def testIgnoresTrailingEmptyColumnFromTrailingTab(
        self, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        filePath = tmp_path / "result.prt"
        filePath.write_text("TIME\tT1\t\n0.0\t10.0\t\n")

        names = vp._readVariableNames(  # pylint: disable=protected-access
            filePath
        )

        assert list(names) == ["T1"]

    def testReturnsEmptyForTimeOnlyFile(
        self, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        filePath = tmp_path / "result.prt"
        filePath.write_text("TIME\n0.0\n1.0\n")

        names = vp._readVariableNames(  # pylint: disable=protected-access
            filePath
        )

        assert not list(names)

    def testRaisesForMissingFile(
        self, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        with _pt.raises(OSError):
            vp._readVariableNames(  # pylint: disable=protected-access
                tmp_path / "doesNotExist.prt"
            )


class TestFindPrtFiles:
    def testFindsPrtFilesRecursivelyCaseInsensitive(
        self, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        (tmp_path / "sub").mkdir()
        prt1 = tmp_path / "a.prt"
        prt1.write_text("TIME\tvar1\n0.0\t1.0\n")
        prt2 = tmp_path / "sub" / "b.PRT"
        prt2.write_text("TIME\tvar1\n0.0\t1.0\n")
        (tmp_path / "c.txt").write_text("not a prt file")

        found = vp._findPrtFiles(tmp_path)  # pylint: disable=protected-access

        assert set(found) == {prt1, prt2}

    def testReturnsEmptyListForMissingDir(
        self, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        missingDir = tmp_path / "doesNotExist"
        assert (
            vp._findPrtFiles(missingDir)  # pylint: disable=protected-access
            == []
        )


class TestConvertHoursToDateTimes:
    def testConvertsHoursOfYearToDateTimes(self):
        hours = _pd.Series([0.0, 1.5, 5040.0, 8759.5])

        dateTimes = vp.convertHoursToDateTimes(hours, 2023)

        assert list(dateTimes) == [
            _pd.Timestamp("2023-01-01 00:00"),
            _pd.Timestamp("2023-01-01 01:30"),
            _pd.Timestamp("2023-07-30 00:00"),
            _pd.Timestamp("2023-12-31 23:30"),
        ]

    def testMultiplesOf8760HoursStartANewYear(self):
        hours = _pd.Series([8760.0, 2 * 8760.0, 2 * 8760.0 + 24.0])

        dateTimes = vp.convertHoursToDateTimes(hours, 2023)

        assert list(dateTimes) == [
            _pd.Timestamp("2024-01-01"),
            _pd.Timestamp("2025-01-01"),
            _pd.Timestamp("2025-01-02"),
        ]

    def testLeapDayIsSkipped(self):
        # TRNSYS years always have 365 days.
        hours = _pd.Series([59 * 24.0 - 1.0, 59 * 24.0, 8759.0])

        dateTimes = vp.convertHoursToDateTimes(hours, 2024)

        assert list(dateTimes) == [
            _pd.Timestamp("2024-02-28 23:00"),
            _pd.Timestamp("2024-03-01 00:00"),
            _pd.Timestamp("2024-12-31 23:00"),
        ]

    def testRoundsAwayFloatingPointNoiseInTimeSteps(self):
        hours = _pd.Series([5040.0333333333338])

        dateTimes = vp.convertHoursToDateTimes(hours, 2023)

        assert dateTimes[0] == _pd.Timestamp("2023-07-30 00:02:00")

    def testNonNumericTimesBecomeNaT(self):
        hours = _pd.Series([0.0, float("nan")])

        dateTimes = vp.convertHoursToDateTimes(hours, 2023)

        assert dateTimes[0] == _pd.Timestamp("2023-01-01")
        assert _pd.isna(dateTimes[1])


class _FakeMainWindow:
    def __init__(self, projectFolder: _pl.Path) -> None:
        self.projectFolder = str(projectFolder)


def _writePrtFile(path: _pl.Path, columns, rows) -> None:
    lines = ["\t".join(columns)]
    lines.extend("\t".join(str(value) for value in row) for row in rows)
    path.write_text("\n".join(lines) + "\n")


def _topLevelTexts(tree) -> _tp.List[str]:
    return [
        tree.topLevelItem(index).text(0)
        for index in range(tree.topLevelItemCount())
    ]


def _findFileItem(tree, fileRelPath: str):
    parentItem = tree.invisibleRootItem()
    for part in _pl.Path(fileRelPath).parts:
        matchingChild = None
        for childIndex in range(parentItem.childCount()):
            child = parentItem.child(childIndex)
            if child.text(0) == part:
                matchingChild = child
                break
        if matchingChild is None:
            raise AssertionError(
                f"No such item: {fileRelPath} (missing {part!r})"
            )
        parentItem = matchingChild
    return parentItem


def _childTexts(fileItem) -> _tp.List[str]:
    return [
        fileItem.child(childIndex).text(0)
        for childIndex in range(fileItem.childCount())
    ]


def _check(tree, fileRelPath: str, variableName: str) -> None:
    fileItem = _findFileItem(tree, fileRelPath)
    for childIndex in range(fileItem.childCount()):
        child = fileItem.child(childIndex)
        if child.text(0) == variableName:
            child.setCheckState(0, _qtc.Qt.Checked)
            return
    raise AssertionError(f"No such variable: {fileRelPath} / {variableName}")


class TestVariablePlotTab:  # pylint: disable=too-many-public-methods
    # pylint: disable=protected-access

    @_pt.fixture(autouse=True)
    def _noMessageBoxPopups(self, monkeypatch):
        monkeypatch.setattr(QMessageBox, "exec", lambda self: QMessageBox.Ok)

    def testRefreshBuildsTreeGroupedByFileWithVariablesAsChildren(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        (tmp_path / "sub").mkdir()
        _writePrtFile(
            tmp_path / "a.prt", ["TIME", "T1", "T2"], [[0.0, 10.0, 20.0]]
        )
        _writePrtFile(
            tmp_path / "sub" / "b.prt", ["TIME", "T3"], [[0.0, 30.0]]
        )

        tab = vp.VariablePlotTab(_FakeMainWindow(tmp_path))
        qtbot.addWidget(tab)

        tree = tab._variablesTree
        assert _childTexts(_findFileItem(tree, "a.prt")) == ["T1", "T2"]
        assert _childTexts(
            _findFileItem(tree, str(_pl.Path("sub") / "b.prt"))
        ) == ["T3"]

    def testFilesAreGroupedUnderTheirSimulationFolder(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        (tmp_path / "sim1").mkdir()
        (tmp_path / "sim2").mkdir()
        _writePrtFile(
            tmp_path / "sim1" / "a.prt", ["TIME", "T1"], [[0.0, 10.0]]
        )
        _writePrtFile(
            tmp_path / "sim1" / "b.prt", ["TIME", "T2"], [[0.0, 20.0]]
        )
        _writePrtFile(
            tmp_path / "sim2" / "a.prt", ["TIME", "T1"], [[0.0, 30.0]]
        )

        tab = vp.VariablePlotTab(_FakeMainWindow(tmp_path))
        qtbot.addWidget(tab)

        tree = tab._variablesTree
        # Top level shows the two simulation folders, not their `.prt`
        # files directly.
        assert sorted(_topLevelTexts(tree)) == ["sim1", "sim2"]

        sim1Item = _findFileItem(tree, "sim1")
        assert sorted(
            sim1Item.child(index).text(0)
            for index in range(sim1Item.childCount())
        ) == ["a.prt", "b.prt"]

    def testNoVariableIsCheckedByDefault(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        _writePrtFile(tmp_path / "a.prt", ["TIME", "T1"], [[0.0, 10.0]])

        tab = vp.VariablePlotTab(_FakeMainWindow(tmp_path))
        qtbot.addWidget(tab)

        assert not tab._getCheckedVariableNamesByFilePath()

    def testNoPrtFilesResultsInEmptyTree(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        tab = vp.VariablePlotTab(_FakeMainWindow(tmp_path))
        qtbot.addWidget(tab)

        assert tab._variablesTree.topLevelItemCount() == 0

    def testFileWithNoPlottableVariablesShowsPlaceholder(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        _writePrtFile(tmp_path / "timeOnly.prt", ["TIME"], [[0.0], [1.0]])

        tab = vp.VariablePlotTab(_FakeMainWindow(tmp_path))
        qtbot.addWidget(tab)

        fileItem = _findFileItem(tab._variablesTree, "timeOnly.prt")
        assert fileItem.childCount() == 1
        assert "no plottable variables" in fileItem.child(0).text(0)

    def testNewPlotWindowStartsEmptyAndBecomesActive(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        tab = vp.VariablePlotTab(_FakeMainWindow(tmp_path))
        qtbot.addWidget(tab)

        tab._onNewPlotButtonClicked()

        subWindows = tab._mdiArea.subWindowList()
        assert len(subWindows) == 1
        assert tab._mdiArea.activeSubWindow() is subWindows[0]
        assert not subWindows[0].widget()._axes.get_lines()

    def testCheckingAVariableLiveUpdatesTheActiveWindow(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        _writePrtFile(
            tmp_path / "a.prt", ["TIME", "T1"], [[0.0, 10.0], [1.0, 11.0]]
        )

        tab = vp.VariablePlotTab(_FakeMainWindow(tmp_path))
        qtbot.addWidget(tab)
        tab._onNewPlotButtonClicked()

        _check(tab._variablesTree, "a.prt", "T1")

        plotWindow = tab._mdiArea.activeSubWindow().widget()
        assert len(plotWindow._axes.get_lines()) == 1
        assert plotWindow._axes.get_lines()[0].get_label() == "a.prt: T1"
        assert dict(plotWindow.checkedVariableNamesByFilePath) == {
            tmp_path / "a.prt": ["T1"]
        }

    def testPlotsAgainstDatesStartingAtTheStartYear(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        _writePrtFile(
            tmp_path / "a.prt", ["TIME", "T1"], [[24.0, 10.0], [48.0, 11.0]]
        )

        tab = vp.VariablePlotTab(_FakeMainWindow(tmp_path))
        qtbot.addWidget(tab)
        tab._startYearSpinBox.setValue(2023)
        tab._onNewPlotButtonClicked()

        _check(tab._variablesTree, "a.prt", "T1")

        plotWindow = tab._mdiArea.activeSubWindow().widget()
        xData = list(
            _pd.to_datetime(plotWindow._axes.get_lines()[0].get_xdata())
        )
        assert xData == [
            _pd.Timestamp("2023-01-02"),
            _pd.Timestamp("2023-01-03"),
        ]

    def testChangingTheStartYearReplotsAllWindows(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        _writePrtFile(
            tmp_path / "a.prt", ["TIME", "T1"], [[0.0, 10.0], [1.0, 11.0]]
        )

        tab = vp.VariablePlotTab(_FakeMainWindow(tmp_path))
        qtbot.addWidget(tab)
        tab._startYearSpinBox.setValue(2023)
        tab._onNewPlotButtonClicked()
        _check(tab._variablesTree, "a.prt", "T1")
        tab._onNewPlotButtonClicked()

        tab._startYearSpinBox.setValue(2030)

        firstWindow = tab._mdiArea.subWindowList()[0].widget()
        secondWindow = tab._mdiArea.subWindowList()[1].widget()
        firstXData = _pd.to_datetime(
            firstWindow._axes.get_lines()[0].get_xdata()
        )
        assert firstXData[0] == _pd.Timestamp("2030-01-01")
        assert not secondWindow._axes.get_lines()

    @staticmethod
    def _createTabWithTwoPlottedWindows(
        qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        _writePrtFile(
            tmp_path / "a.prt",
            ["TIME", "T1", "T2"],
            [[0.0, 10.0, 20.0], [100.0, 11.0, 21.0]],
        )
        tab = vp.VariablePlotTab(_FakeMainWindow(tmp_path))
        qtbot.addWidget(tab)
        tab._onNewPlotButtonClicked()
        _check(tab._variablesTree, "a.prt", "T1")
        tab._onNewPlotButtonClicked()
        _check(tab._variablesTree, "a.prt", "T2")
        firstWindow, secondWindow = [
            subWindow.widget() for subWindow in tab._mdiArea.subWindowList()
        ]
        return tab, firstWindow, secondWindow

    def testZoomIsNotSyncedByDefault(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        tab, firstWindow, secondWindow = self._createTabWithTwoPlottedWindows(
            qtbot, tmp_path
        )
        secondXLimits = secondWindow.getXLimits()

        firstWindow._axes.set_xlim(firstWindow.getXLimits()[0] + 1, 19500.5)

        assert not tab._syncZoomButton.isChecked()
        assert secondWindow.getXLimits() == secondXLimits

    def testZoomingOneWindowZoomsTheOthersWhenSynced(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        tab, firstWindow, secondWindow = self._createTabWithTwoPlottedWindows(
            qtbot, tmp_path
        )
        tab._syncZoomButton.setChecked(True)

        # Simulates the user zooming with the toolbar.
        firstWindow._axes.set_xlim(19358.25, 19358.5)

        assert secondWindow.getXLimits() == (19358.25, 19358.5)
        assert firstWindow.getXLimits() == (19358.25, 19358.5)

    def testEnablingSyncAlignsOtherWindowsToTheActiveOne(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        tab, firstWindow, secondWindow = self._createTabWithTwoPlottedWindows(
            qtbot, tmp_path
        )
        firstWindow._axes.set_xlim(19358.25, 19358.5)

        # The second window is the active one.
        tab._syncZoomButton.setChecked(True)

        assert firstWindow.getXLimits() == secondWindow.getXLimits()
        assert firstWindow.getXLimits() != (19358.25, 19358.5)

    def testReplottingASyncedWindowKeepsTheSyncedRange(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        tab, firstWindow, secondWindow = self._createTabWithTwoPlottedWindows(
            qtbot, tmp_path
        )
        tab._syncZoomButton.setChecked(True)
        firstWindow._axes.set_xlim(19358.25, 19358.5)

        # The second window is active; add another variable to it.
        _check(tab._variablesTree, "a.prt", "T1")

        assert len(secondWindow._axes.get_lines()) == 2
        assert secondWindow.getXLimits() == (19358.25, 19358.5)

    def testDisablingSyncStopsPropagatingZoom(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        tab, firstWindow, secondWindow = self._createTabWithTwoPlottedWindows(
            qtbot, tmp_path
        )
        tab._syncZoomButton.setChecked(True)
        tab._syncZoomButton.setChecked(False)
        secondXLimits = secondWindow.getXLimits()

        firstWindow._axes.set_xlim(19358.25, 19358.5)

        assert secondWindow.getXLimits() == secondXLimits

    @staticmethod
    def _hoverAt(plotWindow, x: float) -> None:
        displayX, displayY = plotWindow._axes.transData.transform((x, 15.0))
        event = _types.SimpleNamespace(
            inaxes=plotWindow._axes, xdata=x, x=displayX, y=displayY
        )
        plotWindow._onHover(event)

    @staticmethod
    def _getCursorX(plotWindow) -> _tp.Optional[float]:
        cursorLine = plotWindow._cursorLine
        if not cursorLine.get_visible():
            return None
        [[(x, _), _]] = cursorLine.get_segments()
        return float(x)

    def testHoveringOneWindowShowsTheCursorInAllWindows(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        tab, firstWindow, secondWindow = self._createTabWithTwoPlottedWindows(
            qtbot, tmp_path
        )
        assert tab._syncCursorButton.isChecked()

        self._hoverAt(firstWindow, 19358.25)

        assert self._getCursorX(firstWindow) == 19358.25
        assert self._getCursorX(secondWindow) == 19358.25

    def testLeavingTheWindowHidesTheCursorInAllWindows(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        _, firstWindow, secondWindow = self._createTabWithTwoPlottedWindows(
            qtbot, tmp_path
        )
        self._hoverAt(firstWindow, 19358.25)

        firstWindow._onMouseLeft(None)

        assert self._getCursorX(firstWindow) is None
        assert self._getCursorX(secondWindow) is None

    def testDisablingCursorSyncHidesAndStopsShowingTheCursor(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        tab, firstWindow, secondWindow = self._createTabWithTwoPlottedWindows(
            qtbot, tmp_path
        )
        self._hoverAt(firstWindow, 19358.25)

        tab._syncCursorButton.setChecked(False)
        assert self._getCursorX(secondWindow) is None

        self._hoverAt(firstWindow, 19358.5)
        assert self._getCursorX(secondWindow) is None

    def testCursorLineIsNotTakenForPlottedData(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        _, firstWindow, _ = self._createTabWithTwoPlottedWindows(
            qtbot, tmp_path
        )
        xLimits = firstWindow.getXLimits()

        self._hoverAt(firstWindow, 19358.25)

        assert len(firstWindow._axes.get_lines()) == 1
        assert firstWindow.getXLimits() == xLimits

    def testActivatingAWindowShowsItsOwnCheckedVariablesInTheTree(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        _writePrtFile(
            tmp_path / "a.prt",
            ["TIME", "T1", "T2"],
            [[0.0, 10.0, 20.0], [1.0, 11.0, 21.0]],
        )

        tab = vp.VariablePlotTab(_FakeMainWindow(tmp_path))
        qtbot.addWidget(tab)

        tab._onNewPlotButtonClicked()
        _check(tab._variablesTree, "a.prt", "T1")
        firstWindow = tab._mdiArea.activeSubWindow()

        tab._onNewPlotButtonClicked()
        _check(tab._variablesTree, "a.prt", "T2")

        # Switching back to the first window must show *its* variable
        # (T1) as checked, not the second window's (T2).
        tab._mdiArea.setActiveSubWindow(firstWindow)

        assert set(
            tab._getCheckedVariableNamesByFilePath()[tmp_path / "a.prt"]
        ) == {"T1"}

    def testEditingAfterSwitchingWindowsTargetsTheNewlyActiveWindow(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        _writePrtFile(
            tmp_path / "a.prt",
            ["TIME", "T1", "T2"],
            [[0.0, 10.0, 20.0], [1.0, 11.0, 21.0]],
        )

        tab = vp.VariablePlotTab(_FakeMainWindow(tmp_path))
        qtbot.addWidget(tab)

        tab._onNewPlotButtonClicked()
        _check(tab._variablesTree, "a.prt", "T1")
        firstWindow = tab._mdiArea.activeSubWindow().widget()

        tab._onNewPlotButtonClicked()
        secondWindow = tab._mdiArea.activeSubWindow().widget()
        _check(tab._variablesTree, "a.prt", "T2")

        # Checking T2 while the second window is active must update *that*
        # window, leaving the first one exactly as it was.
        firstLabels = {
            line.get_label() for line in firstWindow._axes.get_lines()
        }
        secondLabels = {
            line.get_label() for line in secondWindow._axes.get_lines()
        }
        assert firstLabels == {"a.prt: T1"}
        assert secondLabels == {"a.prt: T2"}

    def testUncheckingTheOnlyVariableClearsTheActiveWindow(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        _writePrtFile(
            tmp_path / "a.prt", ["TIME", "T1"], [[0.0, 10.0], [1.0, 11.0]]
        )

        tab = vp.VariablePlotTab(_FakeMainWindow(tmp_path))
        qtbot.addWidget(tab)
        tab._onNewPlotButtonClicked()
        _check(tab._variablesTree, "a.prt", "T1")

        plotWindow = tab._mdiArea.activeSubWindow().widget()
        assert plotWindow._axes.get_lines()

        _findFileItem(tab._variablesTree, "a.prt").child(0).setCheckState(
            0, _qtc.Qt.Unchecked
        )

        assert not plotWindow._axes.get_lines()

    def testCheckingWithNoActiveWindowDoesNothing(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        _writePrtFile(
            tmp_path / "a.prt", ["TIME", "T1"], [[0.0, 10.0], [1.0, 11.0]]
        )

        tab = vp.VariablePlotTab(_FakeMainWindow(tmp_path))
        qtbot.addWidget(tab)

        # No window has been created/activated yet.
        _check(tab._variablesTree, "a.prt", "T1")

        assert not tab._mdiArea.subWindowList()

    def testRefreshResyncsTreeToTheActiveWindow(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        _writePrtFile(
            tmp_path / "a.prt", ["TIME", "T1"], [[0.0, 10.0], [1.0, 11.0]]
        )

        tab = vp.VariablePlotTab(_FakeMainWindow(tmp_path))
        qtbot.addWidget(tab)
        tab._onNewPlotButtonClicked()
        _check(tab._variablesTree, "a.prt", "T1")

        tab.refreshPrtFiles()

        assert set(
            tab._getCheckedVariableNamesByFilePath()[tmp_path / "a.prt"]
        ) == {"T1"}

    def testRefreshKeepsExpandedTreeNodes(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        (tmp_path / "sim1").mkdir()
        (tmp_path / "sim2").mkdir()
        _writePrtFile(
            tmp_path / "sim1" / "a.prt", ["TIME", "T1"], [[0.0, 10.0]]
        )
        _writePrtFile(
            tmp_path / "sim2" / "b.prt", ["TIME", "T2"], [[0.0, 20.0]]
        )
        tab = vp.VariablePlotTab(_FakeMainWindow(tmp_path))
        qtbot.addWidget(tab)
        _findFileItem(tab._variablesTree, "sim1").setExpanded(True)
        _findFileItem(tab._variablesTree, "sim1/a.prt").setExpanded(True)

        tab.refreshPrtFiles()

        tree = tab._variablesTree
        assert _findFileItem(tree, "sim1").isExpanded()
        assert _findFileItem(tree, "sim1/a.prt").isExpanded()
        assert not _findFileItem(tree, "sim2").isExpanded()
        assert not _findFileItem(tree, "sim2/b.prt").isExpanded()

    @staticmethod
    def _createTabPlottingT1(qtbot, projectDirPath, rows):
        _writePrtFile(projectDirPath / "a.prt", ["TIME", "T1"], rows)
        tab = vp.VariablePlotTab(_FakeMainWindow(projectDirPath))
        qtbot.addWidget(tab)
        tab._onNewPlotButtonClicked()
        _check(tab._variablesTree, "a.prt", "T1")
        return tab, tab._mdiArea.activeSubWindow().widget()

    def testRefreshReplotsDataThatWasAppendedInTheMeantime(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        tab, plotWindow = self._createTabPlottingT1(
            qtbot, tmp_path, [[0.0, 10.0], [1.0, 11.0]]
        )
        oldXMax = plotWindow.getXLimits()[1]
        _writePrtFile(
            tmp_path / "a.prt",
            ["TIME", "T1"],
            [[0.0, 10.0], [1.0, 11.0], [100.0, 12.0]],
        )

        tab.refreshPrtFiles()

        assert len(plotWindow._axes.get_lines()[0].get_xdata()) == 3
        # Not zoomed in, so the view grows to show the new data.
        assert plotWindow.getXLimits()[1] > oldXMax

    def testRefreshKeepsAZoomedInView(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        tab, plotWindow = self._createTabPlottingT1(
            qtbot, tmp_path, [[0.0, 10.0], [10.0, 11.0]]
        )
        xMin, xMax = plotWindow.getXLimits()
        zoomedXLimits = (xMin + 0.1, xMax - 0.1)
        plotWindow._axes.set_xlim(zoomedXLimits)
        _writePrtFile(
            tmp_path / "a.prt",
            ["TIME", "T1"],
            [[0.0, 10.0], [10.0, 11.0], [100.0, 12.0]],
        )

        tab.refreshPrtFiles()

        assert len(plotWindow._axes.get_lines()[0].get_xdata()) == 3
        assert plotWindow.getXLimits() == zoomedXLimits

    def testRefreshKeepsASyncedZoomInAllWindows(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        tab, firstWindow, secondWindow = self._createTabWithTwoPlottedWindows(
            qtbot, tmp_path
        )
        tab._syncZoomButton.setChecked(True)
        xMin, xMax = firstWindow.getXLimits()
        zoomedXLimits = (xMin + 0.1, xMax - 0.1)
        firstWindow._axes.set_xlim(zoomedXLimits)

        tab.refreshPrtFiles()

        assert firstWindow.getXLimits() == zoomedXLimits
        assert secondWindow.getXLimits() == zoomedXLimits

    def testRefreshDropsVariablesThatNoLongerExist(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        tab, plotWindow = self._createTabPlottingT1(
            qtbot, tmp_path, [[0.0, 10.0], [1.0, 11.0]]
        )
        _writePrtFile(tmp_path / "a.prt", ["TIME", "T2"], [[0.0, 20.0]])

        tab.refreshPrtFiles()

        assert not plotWindow._axes.get_lines()
        assert not plotWindow.checkedVariableNamesByFilePath

    def testNonNumericVariableIsSkippedWithWarning(
        self,
        qtbot,
        tmp_path,  # pylint: disable=invalid-name  # NOSONAR
        monkeypatch,
    ):
        warnings: _tp.List[str] = []
        monkeypatch.setattr(
            vp._werrors,
            "showMessageBox",
            lambda message, *args, **kwargs: warnings.append(message),
        )
        _writePrtFile(
            tmp_path / "a.prt",
            ["TIME", "T1", "Label"],
            [[0.0, 10.0, "foo"], [1.0, 11.0, "bar"]],
        )

        tab = vp.VariablePlotTab(_FakeMainWindow(tmp_path))
        qtbot.addWidget(tab)
        tab._onNewPlotButtonClicked()

        _check(tab._variablesTree, "a.prt", "T1")
        _check(tab._variablesTree, "a.prt", "Label")

        plotWindow = tab._mdiArea.activeSubWindow().widget()
        assert len(plotWindow._axes.get_lines()) == 1
        assert plotWindow._axes.get_lines()[0].get_label() == "a.prt: T1"
        assert len(warnings) == 1
        assert "a.prt: Label" in warnings[0]


class TestPlotWindow:
    # pylint: disable=protected-access

    @staticmethod
    def _makeSeries(x, y):
        return _pd.Series(x, dtype=float), _pd.Series(y, dtype=float)

    def testStartsEmpty(self, qtbot):
        window = vp._PlotWindow({})
        qtbot.addWidget(window)

        assert not window._axes.get_lines()

    def testSetSeriesUpdatesTheStoredCheckedVariables(
        self, qtbot, tmp_path  # pylint: disable=invalid-name  # NOSONAR
    ):
        time, values = self._makeSeries([0.0, 1.0], [10.0, 11.0])
        window = vp._PlotWindow({})
        qtbot.addWidget(window)

        window.setSeries(
            {tmp_path / "a.prt": ["T1"]}, [("a.prt: T1", time, values)]
        )

        assert len(window._axes.get_lines()) == 1
        assert dict(window.checkedVariableNamesByFilePath) == {
            tmp_path / "a.prt": ["T1"]
        }

    def testUserZoomEmitsXLimitsChanged(self, qtbot):
        time, values = self._makeSeries([0.0, 1.0], [10.0, 11.0])
        window = vp._PlotWindow({})
        qtbot.addWidget(window)
        window.setSeries({}, [("T1", time, values)])
        emitted = []
        window.xLimitsChanged.connect(emitted.append)

        window._axes.set_xlim(0.25, 0.75)

        assert emitted == [(0.25, 0.75)]

    def testProgrammaticChangesDoNotEmitXLimitsChanged(self, qtbot):
        time, values = self._makeSeries([0.0, 1.0], [10.0, 11.0])
        window = vp._PlotWindow({})
        qtbot.addWidget(window)
        emitted = []
        window.xLimitsChanged.connect(emitted.append)

        window.setSeries({}, [("T1", time, values)])
        window.setXLimits((0.25, 0.75))
        window.setSeries({}, [("T1", time, values)])

        assert not emitted

    @staticmethod
    def _zoomLikeTheToolbar(window, xLimits):
        # The toolbar remembers the view before the first zoom as "home"
        # (if its history is empty) and the zoomed view afterwards.
        if window._toolbar._nav_stack() is None:
            window._toolbar.push_current()
        window._axes.set_xlim(xLimits)
        window._toolbar.push_current()

    def testHomeButtonShowsEverythingAfterChangingVariables(self, qtbot):
        time = _pd.Series([0.0, 1.0], dtype=float)
        window = vp._PlotWindow({})
        qtbot.addWidget(window)
        window.setSeries({}, [("T1", time, _pd.Series([10.0, 11.0]))])
        self._zoomLikeTheToolbar(window, (0.2, 0.4))

        window.setSeries(
            {},
            [
                ("T1", time, _pd.Series([10.0, 11.0])),
                ("T2", time, _pd.Series([0.0, 100.0])),
            ],
        )
        fullLimits = window._getLimits()
        self._zoomLikeTheToolbar(window, (0.6, 0.8))
        window._toolbar.home()

        assert window._getLimits() == fullLimits
        _, (yMin, yMax) = fullLimits
        assert yMin < 0.0 and yMax > 100.0

    def testHomeButtonShowsEverythingAfterARefreshKeptTheZoom(self, qtbot):
        window = vp._PlotWindow({})
        qtbot.addWidget(window)
        window.setSeries(
            {},
            [("T1", *self._makeSeries([0.0, 1.0], [10.0, 11.0]))],
        )
        self._zoomLikeTheToolbar(window, (0.2, 0.4))

        window.refreshSeries(
            {},
            [("T1", *self._makeSeries([0.0, 1.0, 5.0], [10.0, 11.0, 50.0]))],
        )
        assert window.getXLimits() == (0.2, 0.4)
        window._toolbar.home()

        (xMin, xMax), (yMin, yMax) = window._getLimits()
        assert xMin < 0.0 and xMax > 5.0
        assert yMin < 10.0 and yMax > 50.0

    def testToolbarIsWiredToCanvas(self, qtbot):
        window = vp._PlotWindow({})
        qtbot.addWidget(window)

        assert window._toolbar.canvas is window._canvas

    def testHoveringNearADataPointShowsItsValue(self, qtbot):
        time, values = self._makeSeries([0.0, 1.0], [10.0, 11.0])
        window = vp._PlotWindow({})
        qtbot.addWidget(window)
        window.setSeries({}, [("T1", time, values)])

        displayX, displayY = window._axes.transData.transform((1.0, 11.0))
        event = _types.SimpleNamespace(
            inaxes=window._axes, xdata=1.0, x=displayX, y=displayY
        )
        window._onHover(event)

        assert window._hoverAnnotation.get_visible()
        assert "T1" in window._hoverAnnotation.get_text()

    def testHoveringNearADateTimeDataPointShowsItsDate(self, qtbot):
        time = _pd.Series(
            _pd.to_datetime(["2023-07-30 00:00", "2023-07-30 01:00"])
        )
        values = _pd.Series([10.0, 11.0])
        window = vp._PlotWindow({})
        qtbot.addWidget(window)
        window.setSeries({}, [("T1", time, values)])

        xNumber = _mdates.date2num(_pd.Timestamp("2023-07-30 01:00"))
        displayX, displayY = window._axes.transData.transform((xNumber, 11.0))
        event = _types.SimpleNamespace(
            inaxes=window._axes, xdata=xNumber, x=displayX, y=displayY
        )
        window._onHover(event)

        assert window._hoverAnnotation.get_visible()
        assert "2023-07-30 01:00" in window._hoverAnnotation.get_text()

    def testHoveringFarFromAnyDataPointHidesTheTooltip(self, qtbot):
        time, values = self._makeSeries([0.0, 1.0], [10.0, 11.0])
        window = vp._PlotWindow({})
        qtbot.addWidget(window)
        window.setSeries({}, [("T1", time, values)])

        displayX, displayY = window._axes.transData.transform((1.0, 11.0))
        event = _types.SimpleNamespace(
            inaxes=window._axes,
            xdata=1.0,
            x=displayX + 1000,
            y=displayY + 1000,
        )
        window._onHover(event)

        assert not window._hoverAnnotation.get_visible()

    def testHoveringOnAFlatLineBetweenDistantDataPointsShowsItsValue(
        self, qtbot
    ):
        time, values = self._makeSeries([0.0, 10.0], [5.0, 5.0])
        window = vp._PlotWindow({})
        qtbot.addWidget(window)
        window.setSeries({}, [("T1", time, values)])

        displayX, displayY = window._axes.transData.transform((5.0, 5.0))
        event = _types.SimpleNamespace(
            inaxes=window._axes, xdata=5.0, x=displayX, y=displayY + 3
        )
        window._onHover(event)

        assert window._hoverAnnotation.get_visible()
        assert "value = 5" in window._hoverAnnotation.get_text()

    def testHoveringOnASteepLineBetweenDistantDataPointsShowsTheTooltip(
        self, qtbot
    ):
        time, values = self._makeSeries([0.0, 1.0], [0.0, 1000.0])
        window = vp._PlotWindow({})
        qtbot.addWidget(window)
        window.setSeries({}, [("T1", time, values)])

        displayX, displayY = window._axes.transData.transform((0.5, 500.0))
        event = _types.SimpleNamespace(
            inaxes=window._axes, xdata=0.5, x=displayX, y=displayY
        )
        window._onHover(event)

        assert window._hoverAnnotation.get_visible()

    def testHoveringOutsideTheAxesHidesTheTooltip(self, qtbot):
        time, values = self._makeSeries([0.0, 1.0], [10.0, 11.0])
        window = vp._PlotWindow({})
        qtbot.addWidget(window)
        window.setSeries({}, [("T1", time, values)])

        event = _types.SimpleNamespace(inaxes=None, xdata=None, x=0, y=0)
        window._onHover(event)

        assert not window._hoverAnnotation.get_visible()
