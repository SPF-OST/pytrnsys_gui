# pylint: disable=too-many-lines
from __future__ import annotations

import contextlib as _contextlib
import datetime as _dt
import itertools as _it
import logging as _log
import math as _math
import pathlib as _pl
import typing as _tp

import numpy as _np
import PyQt5.QtCore as _qtc
import PyQt5.QtWidgets as _qtw
import pandas as _pd
import matplotlib.collections as _mcoll
import matplotlib.dates as _mdates
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as _FigureCanvas,
    NavigationToolbar2QT as _NavigationToolbar,
)
from matplotlib.figure import Figure as _Figure

import trnsysGUI.images as _img
import trnsysGUI.warningsAndErrors as _werrors

_LOGGER = _log.getLogger("root")

_FILE_PATH_ROLE = _qtc.Qt.UserRole

_PlotSeries = _tp.Tuple[str, _pd.Series, _pd.Series]

_XLimits = _tp.Tuple[float, float]
_YLimits = _tp.Tuple[float, float]

_ItemPath = _tp.Tuple[str, ...]


class VariablePlotTab(
    _qtw.QWidget
):  # pylint: disable=too-many-instance-attributes
    """
    A tab that lists every `.prt` result file found anywhere in the current
    project's directory in a tree that mirrors the directory structure they
    were found in - typically one expandable node per simulation (run)
    folder, containing its `.prt` files, each of which in turn expands into
    its variables. Clicking "New plot window" opens an (initially empty)
    plot window inside this tab's MDI area; whichever plot window is
    currently active owns the tree's checkboxes - checking or unchecking a
    variable immediately updates that window's plot, and clicking a
    different (or newly created) window makes the tree show that window's
    own variables instead. Several plot windows can be kept around side by
    side, maximized, minimized, tiled, etc. to compare them.
    """

    def __init__(self, mainWindow: _tp.Any) -> None:
        super().__init__()

        self._mainWindow = mainWindow
        self._dataFramesByFilePath: _tp.Dict[_pl.Path, _pd.DataFrame] = {}
        self._plotWindowCount = 0
        self._syncedXLimits: _tp.Optional[_XLimits] = None

        self._refreshButton = _qtw.QPushButton(
            _img.PLOT_REFRESH_SVG.icon(), "Refresh files"
        )
        self._refreshButton.clicked.connect(self.refreshPrtFiles)

        self._startYearSpinBox = _createStartYearSpinBox(
            self._onStartYearChanged
        )

        self._variablesTree = _qtw.QTreeWidget()
        self._variablesTree.setHeaderHidden(True)
        self._variablesTree.itemChanged.connect(self._onItemChanged)

        self._plotButton = _qtw.QPushButton(
            _img.PLOT_NEW_WINDOW_SVG.icon(), "New plot window"
        )
        self._plotButton.clicked.connect(self._onNewPlotButtonClicked)

        self._mdiArea = _qtw.QMdiArea()
        self._mdiArea.subWindowActivated.connect(
            self._onActiveSubWindowChanged
        )
        self._tileButton = _qtw.QPushButton(_img.PLOT_TILE_SVG.icon(), "Tile")
        self._tileButton.clicked.connect(self._mdiArea.tileSubWindows)
        self._cascadeButton = _qtw.QPushButton(
            _img.PLOT_CASCADE_SVG.icon(), "Cascade"
        )
        self._cascadeButton.clicked.connect(self._mdiArea.cascadeSubWindows)
        self._syncZoomButton = _qtw.QPushButton(
            _img.PLOT_SYNC_ZOOM_SVG.icon(), "Sync zoom"
        )
        self._syncZoomButton.setCheckable(True)
        self._syncZoomButton.setToolTip(
            "When enabled, zooming or panning the time axis of one plot "
            "applies the same time range to all other plots"
        )
        self._syncZoomButton.toggled.connect(self._onSyncZoomToggled)
        self._syncCursorButton = _createSyncCursorButton(
            lambda _: self._showCursorX(None)
        )

        headerRowLayout = _qtw.QHBoxLayout()
        headerRowLayout.addWidget(_qtw.QLabel("Variables:"))
        headerRowLayout.addStretch(1)
        headerRowLayout.addWidget(self._refreshButton)

        treeLayout = _qtw.QVBoxLayout()
        treeLayout.addLayout(headerRowLayout)
        treeLayout.addWidget(self._variablesTree)
        treeLayout.addWidget(self._plotButton)
        treePane = _qtw.QWidget()
        treePane.setLayout(treeLayout)

        mdiLayout = _qtw.QVBoxLayout()
        mdiLayout.addLayout(self._createMdiHeaderRowLayout())
        mdiLayout.addWidget(self._mdiArea)
        mdiPane = _qtw.QWidget()
        mdiPane.setLayout(mdiLayout)

        splitter = _qtw.QSplitter()
        splitter.addWidget(treePane)
        splitter.addWidget(mdiPane)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout = _qtw.QVBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)

        self.refreshPrtFiles()

    def _createMdiHeaderRowLayout(self) -> _qtw.QHBoxLayout:
        mdiHeaderRowLayout = _qtw.QHBoxLayout()
        mdiHeaderRowLayout.addWidget(_qtw.QLabel("Plots:"))
        mdiHeaderRowLayout.addStretch(1)
        mdiHeaderRowLayout.addWidget(_qtw.QLabel("Start year:"))
        mdiHeaderRowLayout.addWidget(self._startYearSpinBox)
        mdiHeaderRowLayout.addWidget(self._syncZoomButton)
        mdiHeaderRowLayout.addWidget(self._syncCursorButton)
        mdiHeaderRowLayout.addWidget(self._tileButton)
        mdiHeaderRowLayout.addWidget(self._cascadeButton)
        return mdiHeaderRowLayout

    def refreshPrtFiles(self) -> None:
        """
        Rescans the project directory for `.prt` files and re-reads the
        data of every open plot window - e.g. to follow a simulation that's
        still running. The tree's expanded nodes and scroll position, as
        well as any plot window's zoomed-in view, are kept.
        """
        projectDirPath = _pl.Path(self._mainWindow.projectFolder)
        prtFilePaths = _findPrtFiles(projectDirPath)

        self._dataFramesByFilePath.clear()

        expandedItemPaths = self._getExpandedItemPaths()
        scrollBar = self._variablesTree.verticalScrollBar()
        scrollPosition = scrollBar.value()

        self._variablesTree.blockSignals(True)
        self._variablesTree.clear()
        folderItemsByParts: _tp.Dict[
            _tp.Tuple[str, ...], _qtw.QTreeWidgetItem
        ] = {}
        for filePath in prtFilePaths:
            relativeParts = filePath.relative_to(projectDirPath).parts
            parentItem = self._getOrCreateFolderItem(
                folderItemsByParts, relativeParts[:-1]
            )
            self._addFileNode(filePath, relativeParts[-1], parentItem)
        self._expandItems(expandedItemPaths)
        scrollBar.setValue(scrollPosition)

        try:
            self._refreshPlotWindows()
        except Exception as error:  # pylint: disable=broad-except
            # See `_onItemChanged`: don't let exceptions escape a Qt slot.
            _LOGGER.error("Could not refresh plot windows: %s", error)
            _werrors.showMessageBox(f"Could not refresh plot windows: {error}")

        self._syncTreeToCheckedVariables(
            self._getActivePlotWindowCheckedVariables()
        )
        self._variablesTree.blockSignals(False)

    def _getExpandedItemPaths(self) -> _tp.Set[_ItemPath]:
        return {
            itemPath
            for item, itemPath in self._iterItemsWithPaths()
            if item.isExpanded()
        }

    def _expandItems(self, itemPaths: _tp.Set[_ItemPath]) -> None:
        for item, itemPath in self._iterItemsWithPaths():
            if itemPath in itemPaths:
                item.setExpanded(True)

    def _iterItemsWithPaths(
        self,
        parentItem: _tp.Optional[_qtw.QTreeWidgetItem] = None,
        parentPath: _ItemPath = (),
    ) -> _tp.Iterator[_tp.Tuple[_qtw.QTreeWidgetItem, _ItemPath]]:
        """
        Walks the tree recursively, yielding every item together with the
        texts of it and its ancestors, which identify it across refreshes.
        """
        if parentItem is None:
            parentItem = self._variablesTree.invisibleRootItem()
        for childIndex in range(parentItem.childCount()):
            childItem = parentItem.child(childIndex)
            assert childItem is not None
            childPath = (*parentPath, childItem.text(0))
            yield childItem, childPath
            yield from self._iterItemsWithPaths(childItem, childPath)

    def _refreshPlotWindows(self) -> None:
        availableVariableNamesByFilePath = {
            filePath: {
                childItem.text(0)
                for childIndex in range(fileItem.childCount())
                if (childItem := fileItem.child(childIndex)) is not None
                and childItem.flags() & _qtc.Qt.ItemIsUserCheckable
            }
            for fileItem, filePath in self._iterFileItems()
        }

        for subWindow in self._mdiArea.subWindowList():
            plotWindow = _getPlotWindow(subWindow)
            # Files or variables might have disappeared in the meantime
            # (e.g. a simulation folder that got deleted and re-created).
            checkedVariableNamesByFilePath = {
                filePath: availableVariableNames
                for filePath, variableNames in (
                    plotWindow.checkedVariableNamesByFilePath.items()
                )
                if (
                    availableVariableNames := [
                        variableName
                        for variableName in variableNames
                        if variableName
                        in availableVariableNamesByFilePath.get(filePath, ())
                    ]
                )
            }
            plottableSeries = self._computePlottableSeries(
                checkedVariableNamesByFilePath
            )
            plotWindow.refreshSeries(
                checkedVariableNamesByFilePath, plottableSeries
            )

        if self._syncZoomButton.isChecked():
            self._onSyncZoomToggled(True)

    def _getOrCreateFolderItem(
        self,
        folderItemsByParts: _tp.Dict[
            _tp.Tuple[str, ...], _qtw.QTreeWidgetItem
        ],
        parts: _tp.Tuple[str, ...],
    ) -> _qtw.QTreeWidgetItem:
        if not parts:
            return self._variablesTree.invisibleRootItem()

        existingItem = folderItemsByParts.get(parts)
        if existingItem is not None:
            return existingItem

        parentItem = self._getOrCreateFolderItem(
            folderItemsByParts, parts[:-1]
        )
        folderItem = _qtw.QTreeWidgetItem(parentItem, [parts[-1]])
        folderItemsByParts[parts] = folderItem
        return folderItem

    def _addFileNode(
        self,
        filePath: _pl.Path,
        fileName: str,
        parentItem: _qtw.QTreeWidgetItem,
    ) -> None:
        fileItem = _qtw.QTreeWidgetItem(parentItem, [fileName])
        fileItem.setData(0, _FILE_PATH_ROLE, filePath)

        try:
            variableNames = _readVariableNames(filePath)
        except (ValueError, OSError) as error:
            _LOGGER.error("Could not read `%s`: %s", filePath, error)
            _qtw.QTreeWidgetItem(
                fileItem, [f"(could not read this file: {error})"]
            )
            return

        if not variableNames:
            _qtw.QTreeWidgetItem(fileItem, ["(no plottable variables)"])
            return

        for variableName in variableNames:
            variableItem = _qtw.QTreeWidgetItem(fileItem, [variableName])
            variableItem.setFlags(
                variableItem.flags() | _qtc.Qt.ItemIsUserCheckable
            )
            variableItem.setCheckState(0, _qtc.Qt.Unchecked)

    def _getCheckedVariableNamesByFilePath(
        self,
    ) -> _tp.Dict[_pl.Path, _tp.List[str]]:
        checkedVariableNamesByFilePath: _tp.Dict[_pl.Path, _tp.List[str]] = {}
        for fileItem, filePath in self._iterFileItems():
            checkedVariableNames = []
            for childIndex in range(fileItem.childCount()):
                childItem = fileItem.child(childIndex)
                assert childItem is not None
                if childItem.checkState(0) == _qtc.Qt.Checked:
                    checkedVariableNames.append(childItem.text(0))
            if checkedVariableNames:
                checkedVariableNamesByFilePath[filePath] = checkedVariableNames

        return checkedVariableNamesByFilePath

    def _iterFileItems(
        self, item: _tp.Optional[_qtw.QTreeWidgetItem] = None
    ) -> _tp.Iterator[_tp.Tuple[_qtw.QTreeWidgetItem, _pl.Path]]:
        """
        Walks the tree recursively, yielding every `.prt`-file node (i.e.
        every node that has a file path attached to it) together with its
        file path - regardless of how deeply it's nested under simulation
        (sub)folder nodes.
        """
        parentItem = (
            item
            if item is not None
            else self._variablesTree.invisibleRootItem()
        )
        for childIndex in range(parentItem.childCount()):
            childItem = parentItem.child(childIndex)
            assert childItem is not None

            filePath = childItem.data(0, _FILE_PATH_ROLE)
            if filePath is not None:
                yield childItem, filePath
            else:
                yield from self._iterFileItems(childItem)

    def _onNewPlotButtonClicked(self) -> None:
        self._plotWindowCount += 1
        plotWindow = _PlotWindow({})
        plotWindow.xLimitsChanged.connect(
            lambda xLimits: self._onPlotWindowXLimitsChanged(
                plotWindow, xLimits
            )
        )
        plotWindow.cursorXChanged.connect(self._onPlotWindowCursorXChanged)
        subWindow = self._mdiArea.addSubWindow(plotWindow)
        subWindow.setWindowTitle(f"Plot {self._plotWindowCount}")
        subWindow.show()
        # Explicitly activate it - `addSubWindow`/`show` alone don't
        # reliably fire `subWindowActivated` (e.g. for the very first
        # subwindow), which is what drives syncing the tree to it below.
        self._mdiArea.setActiveSubWindow(subWindow)

    def _onActiveSubWindowChanged(
        self, subWindow: _tp.Optional[_qtw.QMdiSubWindow]
    ) -> None:
        del subWindow
        self._variablesTree.blockSignals(True)
        self._syncTreeToCheckedVariables(
            self._getActivePlotWindowCheckedVariables()
        )
        self._variablesTree.blockSignals(False)

    def _getActivePlotWindowCheckedVariables(
        self,
    ) -> _tp.Dict[_pl.Path, _tp.Sequence[str]]:
        subWindow = self._mdiArea.activeSubWindow()
        if subWindow is None:
            return {}
        return _getPlotWindow(subWindow).checkedVariableNamesByFilePath

    def _syncTreeToCheckedVariables(
        self,
        checkedVariableNamesByFilePath: _tp.Mapping[
            _pl.Path, _tp.Sequence[str]
        ],
    ) -> None:
        for fileItem, filePath in self._iterFileItems():
            checkedVariableNames = set(
                checkedVariableNamesByFilePath.get(filePath, ())
            )
            for childIndex in range(fileItem.childCount()):
                childItem = fileItem.child(childIndex)
                assert childItem is not None
                isChecked = childItem.text(0) in checkedVariableNames
                childItem.setCheckState(
                    0, _qtc.Qt.Checked if isChecked else _qtc.Qt.Unchecked
                )

    def _onItemChanged(self, item: _qtw.QTreeWidgetItem, column: int) -> None:
        del column
        if not item.flags() & _qtc.Qt.ItemIsUserCheckable:
            # Only variable (leaf) items are checkable; ignore changes on
            # simulation-folder or `.prt`-file nodes.
            return

        try:
            self._updateActivePlotWindow()
        except Exception as error:  # pylint: disable=broad-except
            # Never let an exception escape a Qt slot here: PyQt5 aborts
            # the whole application (not just this dialog) on an unhandled
            # exception raised inside a slot.
            _LOGGER.error("Could not update plot window: %s", error)
            _werrors.showMessageBox(f"Could not update plot window: {error}")

    def _updateActivePlotWindow(self) -> None:
        subWindow = self._mdiArea.activeSubWindow()
        if subWindow is None:
            return

        self._updatePlotWindow(
            _getPlotWindow(subWindow),
            self._getCheckedVariableNamesByFilePath(),
        )

    def _onStartYearChanged(self, startYear: int) -> None:
        del startYear
        try:
            for subWindow in self._mdiArea.subWindowList():
                plotWindow = _getPlotWindow(subWindow)
                self._updatePlotWindow(
                    plotWindow, plotWindow.checkedVariableNamesByFilePath
                )
        except Exception as error:  # pylint: disable=broad-except
            # See `_onItemChanged`: don't let exceptions escape a Qt slot.
            _LOGGER.error("Could not update plot windows: %s", error)
            _werrors.showMessageBox(f"Could not update plot windows: {error}")

    def _updatePlotWindow(
        self,
        plotWindow: "_PlotWindow",
        checkedVariableNamesByFilePath: _tp.Mapping[
            _pl.Path, _tp.Sequence[str]
        ],
    ) -> None:
        plottableSeries = self._computePlottableSeries(
            checkedVariableNamesByFilePath
        )
        plotWindow.setSeries(checkedVariableNamesByFilePath, plottableSeries)

        if not self._syncZoomButton.isChecked() or not plotWindow.hasData():
            return
        if self._syncedXLimits is None:
            self._propagateXLimits(plotWindow, plotWindow.getXLimits())
        else:
            plotWindow.setXLimits(self._syncedXLimits)

    def _onSyncZoomToggled(self, isChecked: bool) -> None:
        self._syncedXLimits = None
        if not isChecked:
            return

        # Start out from the active window's time range if it shows
        # anything, otherwise from the first window that does.
        activeSubWindow = self._mdiArea.activeSubWindow()
        subWindows = self._mdiArea.subWindowList()
        if activeSubWindow is not None:
            subWindows = [activeSubWindow, *subWindows]
        for subWindow in subWindows:
            plotWindow = _getPlotWindow(subWindow)
            if plotWindow.hasData():
                self._propagateXLimits(plotWindow, plotWindow.getXLimits())
                return

    def _onPlotWindowXLimitsChanged(
        self, sourcePlotWindow: "_PlotWindow", xLimits: _XLimits
    ) -> None:
        if self._syncZoomButton.isChecked():
            self._propagateXLimits(sourcePlotWindow, xLimits)

    def _propagateXLimits(
        self, sourcePlotWindow: "_PlotWindow", xLimits: _XLimits
    ) -> None:
        self._syncedXLimits = xLimits
        for subWindow in self._mdiArea.subWindowList():
            plotWindow = _getPlotWindow(subWindow)
            if plotWindow is not sourcePlotWindow and plotWindow.hasData():
                plotWindow.setXLimits(xLimits)

    def _onPlotWindowCursorXChanged(self, x: _tp.Optional[float]) -> None:
        if self._syncCursorButton.isChecked():
            self._showCursorX(x)

    def _showCursorX(self, x: _tp.Optional[float]) -> None:
        for subWindow in self._mdiArea.subWindowList():
            _getPlotWindow(subWindow).setCursorX(x)

    def _computePlottableSeries(
        self,
        checkedVariableNamesByFilePath: _tp.Mapping[
            _pl.Path, _tp.Sequence[str]
        ],
    ) -> _tp.Sequence[_PlotSeries]:
        projectDirPath = _pl.Path(self._mainWindow.projectFolder)

        plottableSeries: _tp.List[_PlotSeries] = []
        unplottableLabels = []
        for filePath, variableNames in checkedVariableNamesByFilePath.items():
            fileLabel = str(filePath.relative_to(projectDirPath))
            dataFrame = self._getOrLoadDataFrame(filePath)
            timeColumnName = dataFrame.columns[0]
            hours = _pd.to_numeric(dataFrame[timeColumnName], errors="coerce")
            time = convertHoursToDateTimes(
                hours, self._startYearSpinBox.value()
            )

            for variableName in variableNames:
                label = f"{fileLabel}: {variableName}"
                values = _pd.to_numeric(
                    dataFrame[variableName], errors="coerce"
                )
                # Some `.prt` files are TRNSYS summary reports rather than
                # uniform time series (e.g. they mix in text rows like
                # "Maximum Instantaneous Values"), so a checked variable
                # might not actually contain plottable numeric data.
                if time.notna().sum() == 0 or values.notna().sum() == 0:
                    unplottableLabels.append(label)
                else:
                    plottableSeries.append((label, time, values))

        if unplottableLabels:
            _werrors.showMessageBox(
                "The following variables don't contain numeric data "
                "that can be plotted against time: "
                f"{', '.join(unplottableLabels)}"
            )

        return plottableSeries

    def _getOrLoadDataFrame(self, filePath: _pl.Path) -> _pd.DataFrame:
        dataFrame = self._dataFramesByFilePath.get(filePath)
        if dataFrame is None:
            headerRowIndex = _detectHeaderRowIndex(filePath)
            dataFrame = _pd.read_csv(
                filePath, sep="\t", header=headerRowIndex
            ).rename(columns=lambda name: name.strip())
            self._dataFramesByFilePath[filePath] = dataFrame
        return dataFrame


def _createStartYearSpinBox(
    onValueChanged: _tp.Callable[[int], None]
) -> _qtw.QSpinBox:
    spinBox = _qtw.QSpinBox()
    spinBox.setRange(1, 9999)
    spinBox.setValue(_dt.date.today().year)
    spinBox.setToolTip(
        "Calendar year that TIME = 0 (midnight of January 1st) "
        "corresponds to"
    )
    spinBox.valueChanged.connect(onValueChanged)
    return spinBox


def _createSyncCursorButton(
    onToggled: _tp.Callable[[bool], None]
) -> _qtw.QPushButton:
    button = _qtw.QPushButton(_img.PLOT_SYNC_CURSOR_SVG.icon(), "Sync cursor")
    button.setCheckable(True)
    button.setChecked(True)
    button.setToolTip(
        "When enabled, hovering over one plot shows a vertical line at "
        "the same time in all plots"
    )
    button.toggled.connect(onToggled)
    return button


def _getPlotWindow(subWindow: _qtw.QMdiSubWindow) -> "_PlotWindow":
    widget = subWindow.widget()
    assert isinstance(widget, _PlotWindow)
    return widget


# How close (in pixels) the cursor has to be to a data point for it to show
# up in that plot window's hover tooltip.
_HOVER_PIXEL_RADIUS = 15


class _PlotWindow(
    _qtw.QWidget
):  # pylint: disable=too-many-instance-attributes
    """
    A single, self-contained plot (figure + navigation toolbar + a hover
    tooltip showing the nearest data point's value), meant to be shown as
    one of possibly several MDI subwindows within a `VariablePlotTab` so
    that different variable selections can be compared side by side.

    Whichever `_PlotWindow` is the active MDI subwindow owns the tab's tree
    checkboxes, so its content changes live as variables are checked or
    unchecked - `checkedVariableNamesByFilePath` remembers that window's
    own selection so the tree can be resynced to it whenever it becomes
    active again (e.g. after clicking on a different window and back).

    `xLimitsChanged` is emitted whenever the user zooms or pans the time
    axis (but not when the limits are set programmatically via
    `setSeries` or `setXLimits`), so that the tab can keep the time axes of
    several windows in sync. Likewise, `cursorXChanged` is emitted with
    the time under the mouse cursor (or `None` once it leaves the plot), so
    that the tab can show it as a vertical line in every window via
    `setCursorX`.
    """

    xLimitsChanged = _qtc.pyqtSignal(tuple)
    cursorXChanged = _qtc.pyqtSignal(object)

    def __init__(
        self,
        checkedVariableNamesByFilePath: _tp.Mapping[
            _pl.Path, _tp.Sequence[str]
        ],
    ) -> None:
        super().__init__()

        self.checkedVariableNamesByFilePath: _tp.Dict[
            _pl.Path, _tp.Sequence[str]
        ] = dict(checkedVariableNamesByFilePath)

        self._isEmittingXLimitsChanges = True
        self._lastEmittedCursorX: _tp.Optional[float] = None
        self._autoscaledLimits: _tp.Optional[_tp.Tuple[_XLimits, _YLimits]] = (
            None
        )

        self._figure = _Figure()
        self._axes = self._figure.add_subplot(111)
        self._connectXLimitsCallback()
        self._canvas = _FigureCanvas(self._figure)
        self._canvas.mpl_connect("motion_notify_event", self._onHover)
        self._canvas.mpl_connect("figure_leave_event", self._onMouseLeft)
        self._hoverAnnotation = self._createHoverAnnotation()
        self._cursorLine = self._createCursorLine()

        self._toolbar = _NavigationToolbar(self._canvas, self)

        layout = _qtw.QVBoxLayout()
        layout.addWidget(self._toolbar)
        layout.addWidget(self._canvas)
        self.setLayout(layout)

    def setSeries(
        self,
        checkedVariableNamesByFilePath: _tp.Mapping[
            _pl.Path, _tp.Sequence[str]
        ],
        series: _tp.Sequence[_PlotSeries],
    ) -> None:
        self.checkedVariableNamesByFilePath = dict(
            checkedVariableNamesByFilePath
        )

        with self._xLimitsChangesSilenced():
            self._plotSeries(series)

    def refreshSeries(
        self,
        checkedVariableNamesByFilePath: _tp.Mapping[
            _pl.Path, _tp.Sequence[str]
        ],
        series: _tp.Sequence[_PlotSeries],
    ) -> None:
        """
        Like `setSeries`, but meant for re-plotting (possibly grown) data
        of the same variables: whichever axis the user zoomed or panned
        keeps its limits, the others are rescaled to fit the new data.
        """
        xLimits, yLimits = self._getLimits()
        isXZoomed = isYZoomed = False
        if self._autoscaledLimits is not None and self.hasData():
            autoscaledXLimits, autoscaledYLimits = self._autoscaledLimits
            isXZoomed = xLimits != autoscaledXLimits
            isYZoomed = yLimits != autoscaledYLimits

        self.setSeries(checkedVariableNamesByFilePath, series)

        if not self.hasData() or not (isXZoomed or isYZoomed):
            return
        with self._xLimitsChangesSilenced():
            if isXZoomed:
                self._axes.set_xlim(xLimits)
            if isYZoomed:
                self._axes.set_ylim(yLimits)
            self._canvas.draw_idle()

    def hasData(self) -> bool:
        return bool(self._axes.get_lines())

    def getXLimits(self) -> _XLimits:
        xLimits, _ = self._getLimits()
        return xLimits

    def setXLimits(self, xLimits: _XLimits) -> None:
        with self._xLimitsChangesSilenced():
            self._axes.set_xlim(xLimits)
            self._canvas.draw_idle()

    @_contextlib.contextmanager
    def _xLimitsChangesSilenced(self) -> _tp.Iterator[None]:
        wasEmitting = self._isEmittingXLimitsChanges
        self._isEmittingXLimitsChanges = False
        try:
            yield
        finally:
            self._isEmittingXLimitsChanges = wasEmitting

    def _connectXLimitsCallback(self) -> None:
        self._axes.callbacks.connect("xlim_changed", self._onXLimitsChanged)

    def _onXLimitsChanged(self, axes: _tp.Any) -> None:
        if self._isEmittingXLimitsChanges:
            xMin, xMax = axes.get_xlim()
            self.xLimitsChanged.emit((float(xMin), float(xMax)))

    def _plotSeries(self, series: _tp.Sequence[_PlotSeries]) -> None:
        self._resetAxes()
        for label, time, values in series:
            self._axes.plot(time, values, label=label)

        if series:
            if _isDateTimeData(series[0][1]):
                locator = _mdates.AutoDateLocator()
                self._axes.xaxis.set_major_locator(locator)
                self._axes.xaxis.set_major_formatter(
                    _mdates.ConciseDateFormatter(locator)
                )
            else:
                self._axes.set_xlabel("TIME")
            if len(series) == 1:
                label = series[0][0]
                self._axes.set_ylabel(label)
                self._axes.set_title(label)
            else:
                self._axes.legend()
        self._figure.tight_layout()
        self._canvas.draw()
        # Remembered to later tell whether the user has zoomed or panned.
        self._autoscaledLimits = self._getLimits()
        # The toolbar's navigation history still holds the views of the
        # previous plot, and its "home" button returns to the first of
        # them - so start a new history with the full view as "home".
        self._toolbar.update()
        self._toolbar.push_current()

    def _getLimits(self) -> _tp.Tuple[_XLimits, _YLimits]:
        with self._xLimitsChangesSilenced():
            xMin, xMax = self._axes.get_xlim()
            yMin, yMax = self._axes.get_ylim()
        return (float(xMin), float(xMax)), (float(yMin), float(yMax))

    def _resetAxes(self) -> None:
        # `Axes.clear()` wipes every artist, including our hover
        # annotation, so it has to be recreated on every reset.
        self._axes.clear()
        self._hoverAnnotation = self._createHoverAnnotation()
        self._cursorLine = self._createCursorLine()
        # ... and it also replaces the axes' callback registry.
        self._connectXLimitsCallback()

    def _createHoverAnnotation(self) -> _tp.Any:
        annotation = self._axes.annotate(
            "",
            xy=(0, 0),
            xytext=(15, 15),
            textcoords="offset points",
            bbox={"boxstyle": "round", "fc": "w"},
            arrowprops={"arrowstyle": "->"},
        )
        annotation.set_visible(False)
        return annotation

    def _createCursorLine(self) -> _tp.Any:
        # A collection rather than a `Line2D` (e.g. from `axvline`), so that
        # it's neither taken for plotted data (see `hasData`), nor affects
        # the axes' autoscaling. It spans the full height of the axes.
        cursorLine = _mcoll.LineCollection(
            [[(0, 0), (0, 1)]],
            transform=self._axes.get_xaxis_transform(),
            colors="grey",
            linestyles="--",
            linewidths=0.8,
            label="_cursor",
        )
        cursorLine.set_visible(False)
        self._axes.add_collection(cursorLine, autolim=False)
        return cursorLine

    def setCursorX(self, x: _tp.Optional[float]) -> None:
        isVisible = x is not None and self.hasData()
        if not isVisible and not self._cursorLine.get_visible():
            return
        if isVisible:
            self._cursorLine.set_segments([[(x, 0), (x, 1)]])
        self._cursorLine.set_visible(isVisible)
        self._canvas.draw_idle()

    def _emitCursorX(self, x: _tp.Optional[float]) -> None:
        if x != self._lastEmittedCursorX:
            self._lastEmittedCursorX = x
            self.cursorXChanged.emit(x)

    def _onMouseLeft(self, event: _tp.Any) -> None:
        del event
        self._hideHoverAnnotation()
        self._emitCursorX(None)

    def _onHover(self, event: _tp.Any) -> None:
        if event.inaxes is not self._axes or event.xdata is None:
            self._hideHoverAnnotation()
            self._emitCursorX(None)
            return

        self._emitCursorX(float(event.xdata))

        nearestPoint = self._findNearestPoint(event)
        if nearestPoint is None:
            self._hideHoverAnnotation()
            return

        label, x, y, isDateTime = nearestPoint
        self._hoverAnnotation.xy = (x, y)
        timeText = (
            _mdates.num2date(x).strftime("%Y-%m-%d %H:%M")
            if isDateTime
            else f"TIME = {x:g}"
        )
        self._hoverAnnotation.set_text(f"{label}\n{timeText}\nvalue = {y:g}")
        self._hoverAnnotation.set_visible(True)
        self._canvas.draw_idle()

    def _hideHoverAnnotation(self) -> None:
        if self._hoverAnnotation.get_visible():
            self._hoverAnnotation.set_visible(False)
            self._canvas.draw_idle()

    def _findNearestPoint(
        self, event: _tp.Any
    ) -> _tp.Optional[_tp.Tuple[str, float, float, bool]]:
        """
        Measures the distance to the drawn lines, not just to their data
        points - otherwise hovering over a flat or steep stretch between
        points far apart (e.g. when zoomed in) wouldn't show anything. The
        closest data point is shown if it's within reach, otherwise the
        (interpolated) point on the line under the cursor.
        """
        cursor = _np.array([event.x, event.y], dtype=float)

        closestDistance: _tp.Optional[float] = None
        closestPoint: _tp.Optional[_tp.Tuple[str, float, float, bool]] = None
        for line in self._axes.get_lines():
            nearest = self._findNearestPointOnLine(line, cursor)
            if nearest is None:
                continue
            distance, point = nearest
            if closestDistance is None or distance < closestDistance:
                closestDistance = distance
                closestPoint = point

        if closestDistance is None or closestPoint is None:
            return None
        if closestDistance > _HOVER_PIXEL_RADIUS:
            return None
        return closestPoint

    def _findNearestPointOnLine(
        self, line: _tp.Any, cursor: _np.ndarray
    ) -> _tp.Optional[_tp.Tuple[float, _tp.Tuple[str, float, float, bool]]]:
        xData, yData, isDateTime = _getLineDataCoordinates(line)
        if xData.size == 0:
            return None

        indices = self._getIndicesNearCursor(xData, cursor)
        xData, yData = xData[indices], yData[indices]
        displayPoints = self._axes.transData.transform(
            _np.column_stack((xData, yData))
        )
        nearest = _getNearestPointOnPolyline(displayPoints, cursor)
        if nearest is None:
            return None
        distance, vertexIndex, pointOnLine = nearest

        vertexDistance = _math.hypot(*(displayPoints[vertexIndex] - cursor))
        if vertexDistance <= _HOVER_PIXEL_RADIUS:
            point = (float(xData[vertexIndex]), float(yData[vertexIndex]))
        else:
            point = self._toDataCoordinates(pointOnLine)
        return distance, (str(line.get_label()), *point, isDateTime)

    def _toDataCoordinates(
        self, displayPoint: _np.ndarray
    ) -> _tp.Tuple[float, float]:
        dataX, dataY = self._axes.transData.inverted().transform(displayPoint)
        return float(dataX), float(dataY)

    def _getIndicesNearCursor(
        self, xData: _np.ndarray, cursor: _np.ndarray
    ) -> slice:
        # Only the (x-sorted) points whose segments can come within reach
        # of the cursor, to keep hovering cheap even for long series.
        toData = self._axes.transData.inverted()
        leftX, _ = toData.transform(cursor - (_HOVER_PIXEL_RADIUS, 0))
        rightX, _ = toData.transform(cursor + (_HOVER_PIXEL_RADIUS, 0))
        lowX, highX = sorted((leftX, rightX))

        # One more point on each side, so that segments merely passing
        # through the window (with both ends outside of it) are included.
        startIndex = max(int(xData.searchsorted(lowX)) - 1, 0)
        endIndex = min(
            int(xData.searchsorted(highX, side="right")) + 1, xData.size
        )
        return slice(startIndex, endIndex)


def _getLineDataCoordinates(
    line: _tp.Any,
) -> _tp.Tuple[_np.ndarray, _np.ndarray, bool]:
    xData = _np.asarray(line.get_xdata())
    isDateTime = _isDateTimeData(xData)
    if isDateTime:
        # Date axes use matplotlib's float "date numbers" as data
        # coordinates (which is also what `event.xdata` is in).
        xData = _np.asarray(_mdates.date2num(xData))
    yData = _np.asarray(line.get_ydata(), dtype=float)
    return xData.astype(float), yData, isDateTime


def _getNearestPointOnPolyline(
    points: _np.ndarray, target: _np.ndarray
) -> _tp.Optional[_tp.Tuple[float, int, _np.ndarray]]:
    """
    Returns the distance from `target` to the polyline through `points`
    (an N x 2 array), the index of the point closest to where that
    minimum distance is attained, and the location on the polyline where
    it is attained. Segments with non-finite ends (gaps in the drawn line)
    are ignored. Returns `None` if there's nothing to measure against.
    """
    if len(points) == 0:
        return None
    if len(points) == 1:
        if not _np.all(_np.isfinite(points[0])):
            return None
        return float(_math.hypot(*(points[0] - target))), 0, points[0]

    starts = points[:-1]
    deltas = points[1:] - starts
    lengthsSquared = _np.sum(deltas**2, axis=1)
    with _np.errstate(divide="ignore", invalid="ignore"):
        fractions = (
            _np.sum((target - starts) * deltas, axis=1) / lengthsSquared
        )
    fractions = _np.clip(_np.nan_to_num(fractions, nan=0.0), 0.0, 1.0)
    projections = starts + fractions[:, _np.newaxis] * deltas
    distances = _np.hypot(*(projections - target).T)
    distances[~_np.all(_np.isfinite(projections), axis=1)] = _np.inf
    distances[~_np.all(_np.isfinite(points[1:]), axis=1)] = _np.inf

    segmentIndex = int(_np.argmin(distances))
    distance = float(distances[segmentIndex])
    if not _math.isfinite(distance):
        return None
    vertexIndex = segmentIndex + int(fractions[segmentIndex] > 0.5)
    return distance, vertexIndex, projections[segmentIndex]


def _isDateTimeData(data: _tp.Any) -> bool:
    return bool(_np.issubdtype(_np.asarray(data).dtype, _np.datetime64))


_HOURS_PER_DAY = 24
_HOURS_PER_YEAR = 365 * _HOURS_PER_DAY
# Hours from January 1st, 00:00 to March 1st, 00:00 in a non-leap year.
_HOURS_BEFORE_MARCH = (31 + 28) * _HOURS_PER_DAY


def convertHoursToDateTimes(hours: _pd.Series, startYear: int) -> _pd.Series:
    """
    Converts TRNSYS simulation times (hours since midnight of January 1st of
    the first simulated year) to calendar date times, taking `startYear` as
    that first year.

    TRNSYS always uses 365-day years (it has no notion of leap years), so
    every multiple of 8760 hours is mapped onto January 1st of the following
    year, and February 29th is skipped in leap years so that, e.g., 1416 h
    (the start of March in TRNSYS) is always March 1st.
    """
    yearOffsets = _np.floor(hours / _HOURS_PER_YEAR)
    hoursIntoYear = hours - yearOffsets * _HOURS_PER_YEAR

    years = startYear + yearOffsets
    isLeapYear = ((years % 4 == 0) & (years % 100 != 0)) | (years % 400 == 0)
    isAfterLeapDay = isLeapYear & (hoursIntoYear >= _HOURS_BEFORE_MARCH)
    hoursIntoYear = hoursIntoYear + isAfterLeapDay * _HOURS_PER_DAY

    isValid = hours.notna()
    yearStarts = _pd.Series(_pd.NaT, index=hours.index, dtype="datetime64[ns]")
    yearStarts[isValid] = _pd.to_datetime(
        _pd.DataFrame(
            {"year": years[isValid].astype(int), "month": 1, "day": 1}
        )
    )
    offsets = _pd.to_timedelta(hoursIntoYear, unit="h")
    return (yearStarts + offsets).dt.round("s")


_MAX_HEADER_DETECTION_ROWS = 20


def _detectHeaderRowIndex(filePath: _pl.Path) -> int:
    """
    TRNSYS `.prt` files typically have the variable names on the row
    immediately above the first row of numeric data - some files have that
    row right at the top, others have one or more useless rows above it
    (e.g. a row of repeated "Label not available" cells). This scans the
    first few rows to find the first one that's entirely numeric, and
    returns the index of the row above it, so `pandas.read_csv`'s `header`
    argument can pick the right row and skip any junk above it.
    """
    with open(filePath, encoding="utf-8", errors="replace") as prtFile:
        for rowIndex, line in enumerate(prtFile):
            if rowIndex >= _MAX_HEADER_DETECTION_ROWS:
                break

            cells = [cell.strip() for cell in line.split("\t")]
            nonEmptyCells = [cell for cell in cells if cell]
            if not nonEmptyCells:
                continue

            if _isNumericRow(nonEmptyCells):
                return max(rowIndex - 1, 0)

    return 0


def _isNumericRow(cells: _tp.Sequence[str]) -> bool:
    for cell in cells:
        try:
            float(cell)
        except ValueError:
            return False
    return True


def _readVariableNames(filePath: _pl.Path) -> _tp.Sequence[str]:
    """
    Returns the names of the plottable variables in `filePath` (i.e. its
    header row's column names, excluding the leading `TIME` column), without
    having to load the whole file into a `DataFrame` - `refreshPrtFiles`
    calls this for every `.prt` file found in the project directory, which
    can be a lot of (potentially large) files.
    """
    headerRowIndex = _detectHeaderRowIndex(filePath)
    with open(filePath, encoding="utf-8", errors="replace") as prtFile:
        headerLines = list(
            _it.islice(prtFile, headerRowIndex, headerRowIndex + 1)
        )

    if not headerLines:
        return []

    columnNames = [name.strip() for name in headerLines[0].split("\t")]
    nonEmptyColumnNames = [name for name in columnNames if name]
    return nonEmptyColumnNames[1:]


def _findPrtFiles(projectDirPath: _pl.Path) -> _tp.Sequence[_pl.Path]:
    if not projectDirPath.is_dir():
        return []

    return sorted(
        p
        for p in projectDirPath.rglob("*")
        if p.is_file() and p.suffix.lower() == ".prt"
    )
