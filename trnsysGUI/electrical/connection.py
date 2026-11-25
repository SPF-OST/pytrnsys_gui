from __future__ import annotations

import collections.abc as _cabc
import math as _math
import re as _re
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

import trnsysGUI.BlockItem as _bi
import trnsysGUI.electrical.terminals as _et

_STUB_LENGTH = 12
_NO_POWER_TEXT = (
    "-- kW"  # power label before the flow visualizer has loaded results
)
_NO_POWER_KW = (
    1e-4  # below this the flow visualizer shows a connection without power
)
_VALID_NAME = _re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


class ElectricalConnection(
    _qtw.QGraphicsPathItem
):  # pylint: disable=too-many-instance-attributes
    """Electrical connection between two terminals. Its power `Pel<Name>` [kW] is positive in the direction of
    the arrow (from `fromTerminal` to `toTerminal`) and may be negative (e.g. battery charging/discharging).
    """

    def __init__(
        self,
        name: str,
        fromTerminal: _et.ElectricalTerminalItem,
        toTerminal: _et.ElectricalTerminalItem,
    ) -> None:
        super().__init__()
        self.name = name
        self.fromTerminal = fromTerminal
        self.toTerminal = toTerminal

        self.setZValue(0.6)
        self.setFlag(self.ItemIsSelectable, True)
        self.setCursor(_qtg.QCursor(_qtc.Qt.PointingHandCursor))

        self.label = _qtw.QGraphicsSimpleTextItem(name, self)
        self.label.setBrush(_qtg.QBrush(_et.GREEN.darker(150)))
        font = self.label.font()
        font.setPointSizeF(7)
        self.label.setFont(font)
        self.label.setVisible(False)

        # power shown by the flow visualizer (None: normal drawing)
        self.powerLabel = _qtw.QGraphicsSimpleTextItem(_NO_POWER_TEXT, self)
        self.powerLabel.setBrush(_qtg.QBrush(_et.GREEN.darker(150)))
        self.powerLabel.setFont(font)
        self.powerLabel.setVisible(False)
        self._power: float | None = None
        self._powerWidth = 1.8

        self._arrow = _qtg.QPolygonF()
        self._reversedArrow = _qtg.QPolygonF()
        self._labelAnchor = (_qtc.QPointF(), True)

    @property
    def editor(self):
        return self.fromTerminal.editor

    @property
    def variableName(self) -> str:
        return getVariableName(self.name)

    def attach(self) -> None:
        self.fromTerminal.connections.append(self)
        self.toTerminal.connections.append(self)
        self.editor.electricalConnections.append(self)
        self.editor.diagramScene.addItem(self)
        self.updatePath()

    def delete(self) -> None:
        for terminal in (self.fromTerminal, self.toTerminal):
            if self in terminal.connections:
                terminal.connections.remove(self)
        if self in self.editor.electricalConnections:
            self.editor.electricalConnections.remove(self)
        if self.scene() is not None:
            self.scene().removeItem(self)

    def rename(self, newName: str) -> None:
        self.name = newName
        self.label.setText(newName)
        self._updateToolTip()

    def reverse(self) -> None:
        self.fromTerminal, self.toTerminal = self.toTerminal, self.fromTerminal
        self.updatePath()

    def _updateToolTip(self) -> None:
        self.setToolTip(
            f"{self.name}: {self.fromTerminal.qualifiedName} -> {self.toTerminal.qualifiedName}\n"
            f"{self.variableName} [kW], positive in the direction of the arrow"
        )

    # --- geometry ------------------------------------------------------------------
    def updatePath(self) -> None:
        points = _route(self.fromTerminal, self.toTerminal)

        path = _qtg.QPainterPath(points[0])
        for point in points[1:]:
            path.lineTo(point)
        self.setPath(path)

        self._arrow = _getArrowAtLongestSegment(points)
        self._reversedArrow = _getArrowAtLongestSegment(points[::-1])
        longest = max(
            zip(points, points[1:]), key=lambda s: _length(s[1] - s[0])
        )
        middle = (longest[0] + longest[1]) / 2
        self.label.setPos(middle + _qtc.QPointF(4, -12))
        self._labelAnchor = (middle, _isHorizontal(longest[1] - longest[0]))
        self._placePowerLabel()
        self._updateToolTip()

    def boundingRect(self) -> _qtc.QRectF:
        return (
            super()
            .boundingRect()
            .united(self._arrow.boundingRect())
            .adjusted(-12, -12, 12, 12)
        )

    def shape(self) -> _qtg.QPainterPath:
        stroker = _qtg.QPainterPathStroker()
        stroker.setWidth(8)
        return stroker.createStroke(self.path())

    # --- flow visualizer ------------------------------------------------------------------
    def setPower(self, power: float, width: float) -> None:
        """Show the power [kW] of a time step: line width from its magnitude, arrow in the direction
        the power actually flows (reversed if negative), no arrow and a dashed line without power.
        """
        self._power = power
        self._powerWidth = width
        self.powerLabel.setText(f"{abs(power):.2f} kW")
        self._placePowerLabel()
        self.update()

    def _placePowerLabel(self) -> None:
        """Next to the middle of the longest segment, clear of the (possibly thick) line."""
        middle, isHorizontal = self._labelAnchor
        textRect = self.powerLabel.boundingRect()
        clearance = self._powerWidth / 2 + 2
        if isHorizontal:
            offset = _qtc.QPointF(-textRect.width() / 2, clearance)
        else:
            offset = _qtc.QPointF(clearance, -textRect.height() / 2)
        self.powerLabel.setPos(middle + offset)

    def clearPower(self) -> None:
        self._power = None
        self.powerLabel.setText(_NO_POWER_TEXT)
        self.powerLabel.setVisible(False)
        self._placePowerLabel()
        self.update()

    def paint(
        self, painter, option, widget=None
    ):  # pylint: disable=unused-argument
        painter.setRenderHint(_qtg.QPainter.Antialiasing)
        arrow = self._arrow
        pen = _qtg.QPen(_et.GREEN, 3.0 if self.isSelected() else 1.8)
        if self._power is not None:
            pen.setWidthF(self._powerWidth)
            if abs(self._power) < _NO_POWER_KW:
                pen.setStyle(_qtc.Qt.DashLine)
                arrow = _qtg.QPolygonF()
            elif self._power < 0:
                arrow = self._reversedArrow
            arrow = _scaledAboutCenter(arrow, max(1.0, self._powerWidth / 3))
        painter.setPen(pen)
        painter.setBrush(_qtc.Qt.NoBrush)
        painter.drawPath(self.path())
        painter.setPen(_qtg.QPen(_et.GREEN, 1))
        painter.setBrush(_qtg.QBrush(_et.GREEN))
        painter.drawPolygon(arrow)

    # --- interaction ------------------------------------------------------------------
    def mouseDoubleClickEvent(
        self, event
    ):  # pylint: disable=invalid-name,unused-argument
        self.askForNewName()

    def contextMenuEvent(self, event):  # pylint: disable=invalid-name
        # same entries as the context menu of the pipes
        menu = _qtw.QMenu()
        menu.addAction("Rename...").triggered.connect(self.askForNewName)
        menu.addAction("Delete this connection").triggered.connect(self.delete)
        menu.addAction("Reverse direction").triggered.connect(self.reverse)
        menu.addAction("Toggle name").triggered.connect(self.toggleName)
        menu.addAction("Toggle electric power").triggered.connect(
            self.togglePower
        )
        menu.exec_(event.screenPos())

    def toggleName(self) -> None:
        self.label.setVisible(not self.label.isVisible())

    def togglePower(self) -> None:
        """Show or hide the power of the time step shown by the flow visualizer ("-- kW" without results)."""
        self.powerLabel.setVisible(not self.powerLabel.isVisible())

    def askForNewName(self) -> None:
        newName, ok = _qtw.QInputDialog.getText(
            self.editor,
            "Rename electrical connection",
            "Name:",
            text=self.name,
        )
        if not ok or newName == self.name:
            return
        problem = getProblemWithName(
            newName, self.editor.electricalConnections
        )
        if problem:
            _qtw.QMessageBox.warning(None, "Invalid name", problem)
            return
        self.rename(newName)

    # --- serialization ------------------------------------------------------------------
    def toDict(self) -> dict[str, _tp.Any]:
        return {
            "name": self.name,
            "from": _terminalToDict(self.fromTerminal),
            "to": _terminalToDict(self.toTerminal),
        }


def getVariableName(connectionName: str) -> str:
    return f"Pel{connectionName[0].upper()}{connectionName[1:]}"


def getProblemWithName(
    name: str, connections: _cabc.Sequence[ElectricalConnection]
) -> str | None:
    if not _VALID_NAME.match(name):
        return "The name must start with a letter and contain only letters, digits and `_`."
    if any(c.name == name for c in connections):
        return f"There is already an electrical connection called `{name}`."
    return None


def connect(
    terminal1: _et.ElectricalTerminalItem,
    terminal2: _et.ElectricalTerminalItem,
) -> ElectricalConnection | None:
    """Connect two terminals. The arrow points from the terminal that delivers power (`out`) to the one that
    receives it (`in`); with two bidirectional terminals it follows the drawing direction.
    """
    if terminal1.blockItem is terminal2.blockItem:
        return None

    # one connection per terminal, so that `@pel(T)` names exactly one variable
    occupied = [
        t.qualifiedName for t in (terminal1, terminal2) if t.connections
    ]
    if occupied:
        _qtw.QMessageBox.information(
            None,
            "Terminal already connected",
            f"{' and '.join(occupied)} already has an electrical connection. "
            "Each terminal takes one connection: use a node (EBNODE) to join several.",
        )
        return None

    fromTerminal, toTerminal = terminal1, terminal2
    if terminal1.direction == "in" or terminal2.direction == "out":
        fromTerminal, toTerminal = terminal2, terminal1

    editor = terminal1.editor
    name = _getUniqueDefaultName(
        fromTerminal, toTerminal, editor.electricalConnections
    )

    connection = ElectricalConnection(name, fromTerminal, toTerminal)
    connection.attach()
    return connection


def _getUniqueDefaultName(
    fromTerminal: _et.ElectricalTerminalItem,
    toTerminal: _et.ElectricalTerminalItem,
    connections: _cabc.Sequence[ElectricalConnection],
) -> str:
    baseName = f"{fromTerminal.blockItem.displayName}_{toTerminal.blockItem.displayName}"
    baseName = _re.sub(r"[^A-Za-z0-9_]", "", baseName)
    existingNames = {c.name for c in connections}
    name = baseName
    suffix = 2
    while name in existingNames:
        name = f"{baseName}_{suffix}"
        suffix += 1
    return name


def _terminalToDict(
    terminal: _et.ElectricalTerminalItem,
) -> dict[str, _tp.Any]:
    return {"blockId": terminal.blockItem.trnsysId, "terminal": terminal.name}


def decodeConnections(
    editor, serializedConnections: _cabc.Sequence[_cabc.Mapping[str, _tp.Any]]
) -> None:
    terminalsById = {
        (blockItem.trnsysId, terminal.name): terminal
        for blockItem in editor.trnsysObj
        if isinstance(blockItem, _bi.BlockItem)
        for terminal in _et.getTerminals(blockItem)
    }

    for serializedConnection in serializedConnections:
        fromKey = (
            serializedConnection["from"]["blockId"],
            serializedConnection["from"]["terminal"],
        )
        toKey = (
            serializedConnection["to"]["blockId"],
            serializedConnection["to"]["terminal"],
        )
        fromTerminal = terminalsById.get(fromKey)
        toTerminal = terminalsById.get(toKey)
        if not fromTerminal or not toTerminal:
            editor.logger.warning(
                "Electrical connection `%s` skipped: one of its terminals no longer exists.",
                serializedConnection["name"],
            )
            continue

        connection = ElectricalConnection(
            serializedConnection["name"], fromTerminal, toTerminal
        )
        connection.attach()


def deleteAll(editor) -> None:
    for connection in list(editor.electricalConnections):
        connection.delete()


# --- routing ------------------------------------------------------------------------------
def _route(
    fromTerminal: _et.ElectricalTerminalItem,
    toTerminal: _et.ElectricalTerminalItem,
) -> list[_qtc.QPointF]:
    """Orthogonal route: a short stub out of each terminal, joined by one or two elbows."""
    start, end = fromTerminal.scenePos(), toTerminal.scenePos()
    startNormal, endNormal = (
        fromTerminal.getOutwardNormal(),
        toTerminal.getOutwardNormal(),
    )
    a = start + startNormal * _STUB_LENGTH
    b = end + endNormal * _STUB_LENGTH

    startIsHorizontal = abs(startNormal.x()) > abs(startNormal.y())
    endIsHorizontal = abs(endNormal.x()) > abs(endNormal.y())

    if startIsHorizontal and endIsHorizontal:
        middleX = (a.x() + b.x()) / 2
        elbows = [_qtc.QPointF(middleX, a.y()), _qtc.QPointF(middleX, b.y())]
    elif not startIsHorizontal and not endIsHorizontal:
        middleY = (a.y() + b.y()) / 2
        elbows = [_qtc.QPointF(a.x(), middleY), _qtc.QPointF(b.x(), middleY)]
    elif startIsHorizontal:
        elbows = [_qtc.QPointF(b.x(), a.y())]
    else:
        elbows = [_qtc.QPointF(a.x(), b.y())]

    points = [start, a, *elbows, b, end]
    return _withoutRepeatedPoints(points)


def _withoutRepeatedPoints(points: list[_qtc.QPointF]) -> list[_qtc.QPointF]:
    result = [points[0]]
    for point in points[1:]:
        if _length(point - result[-1]) > 1e-6:
            result.append(point)
    return result if len(result) > 1 else points[:2]


def _isHorizontal(vector: _qtc.QPointF) -> bool:
    return abs(vector.x()) >= abs(vector.y())


def _length(vector: _qtc.QPointF) -> float:
    return _math.hypot(vector.x(), vector.y())


def _scaledAboutCenter(
    polygon: _qtg.QPolygonF, factor: float
) -> _qtg.QPolygonF:
    if polygon.isEmpty() or factor == 1.0:
        return polygon
    center = polygon.boundingRect().center()
    transform = (
        _qtg.QTransform()
        .translate(center.x(), center.y())
        .scale(factor, factor)
        .translate(-center.x(), -center.y())
    )
    return transform.map(polygon)


def _getArrowAtLongestSegment(points: list[_qtc.QPointF]) -> _qtg.QPolygonF:
    start, end = max(
        zip(points, points[1:]), key=lambda s: _length(s[1] - s[0])
    )
    length = _length(end - start)
    if length < 1e-6:
        return _qtg.QPolygonF()
    direction = (end - start) / length
    normal = _qtc.QPointF(-direction.y(), direction.x())
    tip = (start + end) / 2 + direction * 5
    base = tip - direction * 9
    return _qtg.QPolygonF([tip, base + normal * 4, base - normal * 4])
