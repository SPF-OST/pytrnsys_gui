"""Bridges where pipes cross without being connected.

A horizontal pipe that crosses a vertical pipe in the middle of both (not at a tee, a corner or a
port) is drawn with a small arc jumping over the vertical pipe, so a crossing can't be mistaken for
a junction. The bridges are an extra drawing layer on top of the pipes: the pipes themselves and
the saved diagram are not changed. They are recomputed shortly after anything in the diagram changes.
"""

from __future__ import annotations

import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

if _tp.TYPE_CHECKING:
    import trnsysGUI.diagram.Editor as _ed

_BRIDGE_RADIUS = 6.0
_MIN_DISTANCE_FROM_LINE_END = _BRIDGE_RADIUS + 2.0
_RECOMPUTE_DELAY_IN_MS = 150


class _Line(_tp.NamedTuple):
    owner: _qtw.QGraphicsItem  # the pipe (or tee piece) the line belongs to
    start: _qtc.QPointF
    end: _qtc.QPointF
    pen: _qtg.QPen
    # how far from its ends a crossing must be; tee legs are short, so crossings close to a port count
    minDistanceFromEnd: float = _MIN_DISTANCE_FROM_LINE_END


class _Crossing(_tp.NamedTuple):
    point: _qtc.QPointF
    hopPen: _qtg.QPen  # pipe that jumps (bridge)
    otherPen: _qtg.QPen  # pipe that passes underneath, or ends there
    isHopHorizontal: bool
    # None: the other pipe passes through; -1 / +1: it only comes from that side and ends here
    otherSide: _tp.Optional[int]


class PipeCrossingsOverlay(_qtw.QGraphicsItem):
    def __init__(self, editor: _ed.Editor) -> None:  # type: ignore[name-defined]
        super().__init__()
        self._editor = editor
        self._crossings: list[_Crossing] = []
        self._signature: tuple = ()
        self._isEnabled = True
        self.setZValue(0.5)  # above the pipes, below the components
        self.setAcceptedMouseButtons(_qtc.Qt.NoButton)
        self.setAcceptHoverEvents(False)

        self._timer = _qtc.QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(_RECOMPUTE_DELAY_IN_MS)
        self._timer.timeout.connect(self.recompute)

    def setBridgesEnabled(self, isEnabled: bool) -> None:
        self._isEnabled = isEnabled
        self.recompute()

    def scheduleRecompute(self, *_) -> None:
        self._timer.start()

    def recompute(self) -> None:
        crossings = _findCrossings(self._editor) if self._isEnabled else []
        signature = tuple(
            (
                round(c.point.x(), 1),
                round(c.point.y(), 1),
                c.hopPen.color().name(),
                c.hopPen.widthF(),
                c.otherPen.color().name(),
                c.otherPen.widthF(),
                c.isHopHorizontal,
                c.otherSide,
            )
            for c in crossings
        )
        if signature == self._signature:
            return  # nothing changed: no repaint (avoids an endless update loop)
        self.prepareGeometryChange()
        self._crossings = crossings
        self._signature = signature
        self.update()

    def boundingRect(self) -> _qtc.QRectF:
        rect = _qtc.QRectF()
        margin = _BRIDGE_RADIUS + 6
        for crossing in self._crossings:
            p = crossing.point
            rect = rect.united(_qtc.QRectF(p.x() - margin, p.y() - margin, 2 * margin, 2 * margin))
        return rect

    def paint(self, painter: _qtg.QPainter, option, widget=None) -> None:  # pylint: disable=unused-argument
        background = _getBackgroundColor(self.scene())
        painter.setRenderHint(_qtg.QPainter.Antialiasing)
        r = _BRIDGE_RADIUS
        for crossing in self._crossings:
            p = crossing.point
            hopWidth = max(crossing.hopPen.widthF(), 1.0)
            otherWidth = max(crossing.otherPen.widthF(), 1.0)
            gapThickness = hopWidth + 2
            reach = gapThickness / 2 + otherWidth / 2  # how far the other pipe is redrawn into the gap

            # 1. gap in the jumping pipe
            if crossing.isHopHorizontal:
                gap = _qtc.QRectF(p.x() - r, p.y() - gapThickness / 2, 2 * r, gapThickness)
            else:
                gap = _qtc.QRectF(p.x() - gapThickness / 2, p.y() - r, gapThickness, 2 * r)
            painter.fillRect(gap, background)

            # 2. the other pipe underneath: through the gap, or only up to its end
            otherPen = _qtg.QPen(crossing.otherPen)
            otherPen.setStyle(_qtc.Qt.SolidLine)
            painter.setPen(otherPen)
            low = -reach if crossing.otherSide in (None, -1) else 0.0
            high = reach if crossing.otherSide in (None, 1) else 0.0
            if crossing.isHopHorizontal:  # the other pipe is vertical
                painter.drawLine(_qtc.QPointF(p.x(), p.y() + low), _qtc.QPointF(p.x(), p.y() + high))
            else:
                painter.drawLine(_qtc.QPointF(p.x() + low, p.y()), _qtc.QPointF(p.x() + high, p.y()))

            # 3. the bridge: upper half circle for horizontal pipes, right half circle for vertical ones
            hopPen = _qtg.QPen(crossing.hopPen)
            hopPen.setStyle(_qtc.Qt.SolidLine)
            hopPen.setCapStyle(_qtc.Qt.FlatCap)
            painter.setPen(hopPen)
            arcRect = _qtc.QRectF(p.x() - r, p.y() - r, 2 * r, 2 * r)
            if crossing.isHopHorizontal:
                painter.drawArc(arcRect, 0, 180 * 16)
            else:
                painter.drawArc(arcRect, -90 * 16, 180 * 16)


def _getBackgroundColor(scene: _tp.Optional[_qtw.QGraphicsScene]) -> _qtg.QColor:
    if scene is not None:
        brush = scene.backgroundBrush()
        if brush.style() == _qtc.Qt.SolidPattern:
            return brush.color()
    return _qtg.QColor(_qtc.Qt.white)


def _getPipeLines(editor: _ed.Editor) -> list[_Line]:  # type: ignore[name-defined]
    """Straight runs of all pipes. Consecutive pieces of the same pipe that continue in the same
    direction (a corner point on a straight line) are merged, so that a crossing exactly at such a
    point is still found."""
    lines = []
    for connection in editor.connectionList:
        # one list per drawn line of the pipe: 1 for single pipes, 2 (cold/hot) for double pipes
        piecesPerLine: dict[int, list[_Line]] = {}
        for segment in connection.segments:
            if not segment.isVisible():
                continue
            lineItems = [
                child
                for child in segment.childItems()
                if isinstance(child, _qtw.QGraphicsLineItem) and child.isVisible()
            ]
            for index, lineItem in enumerate(lineItems):
                line = lineItem.line()
                if line.isNull():
                    continue
                piecesPerLine.setdefault(index, []).append(
                    _Line(
                        connection,  # owner: crossings of a pipe with itself are ignored
                        lineItem.mapToScene(line.p1()),
                        lineItem.mapToScene(line.p2()),
                        lineItem.pen(),
                    )
                )
        for pieces in piecesPerLine.values():
            lines.extend(_mergeStraightContinuations(pieces))
    lines.extend(_getTeePieceLines(editor))
    return lines


_TEE_PEN_WIDTH = 4.0
_TEE_MIN_DISTANCE_FROM_END = 2.0


def _getTeePieceLines(editor: _ed.Editor) -> list[_Line]:  # type: ignore[name-defined]
    """The legs of the tee pieces, so that a pipe running over a tee it is not connected to is
    bridged as well (it would look like a junction with four pipes)."""
    lines = []
    for item in editor.trnsysObj:
        if "TeePiece" not in type(item).__name__:
            continue
        ports = [*getattr(item, "inputs", []), *getattr(item, "outputs", [])]
        points = [port.scenePos() for port in ports]
        if len(points) != 3:
            continue
        pen = _qtg.QPen(_qtc.Qt.black, _TEE_PEN_WIDTH)
        for i in range(3):
            for j in range(i + 1, 3):
                a, b = points[i], points[j]
                if abs(a.x() - b.x()) < 0.5 or abs(a.y() - b.y()) < 0.5:  # the straight-through leg
                    branch = points[3 - i - j]
                    center = _qtc.QPointF((a.x() + b.x()) / 2, (a.y() + b.y()) / 2)
                    lines.append(_Line(item, a, b, pen, _TEE_MIN_DISTANCE_FROM_END))
                    lines.append(_Line(item, center, branch, pen, _TEE_MIN_DISTANCE_FROM_END))
                    break
            else:
                continue
            break
    return lines


def _isSamePoint(a: _qtc.QPointF, b: _qtc.QPointF) -> bool:
    return abs(a.x() - b.x()) < 0.5 and abs(a.y() - b.y()) < 0.5


def _mergeStraightContinuations(pieces: list[_Line]) -> list[_Line]:
    merged: list[_Line] = []
    for piece in pieces:
        if merged:
            last = merged[-1]
            continuesHorizontally = _isHorizontal(last) and _isHorizontal(piece) and abs(last.start.y() - piece.start.y()) < 0.5
            continuesVertically = _isVertical(last) and _isVertical(piece) and abs(last.start.x() - piece.start.x()) < 0.5
            if (continuesHorizontally or continuesVertically) and _isSamePoint(last.end, piece.start):
                merged[-1] = _Line(last.owner, last.start, piece.end, last.pen)
                continue
        merged.append(piece)
    return merged


def _isHorizontal(line: _Line) -> bool:
    return abs(line.start.y() - line.end.y()) < 0.01 and abs(line.start.x() - line.end.x()) > 0.01


def _isVertical(line: _Line) -> bool:
    return abs(line.start.x() - line.end.x()) < 0.01 and abs(line.start.y() - line.end.y()) > 0.01


def _isStrictlyInside(value: float, a: float, b: float, margin: float = _MIN_DISTANCE_FROM_LINE_END) -> bool:
    low, high = min(a, b), max(a, b)
    return low + margin < value < high - margin


_END_ON_LINE_TOLERANCE = 2.0  # a pipe end this close to another pipe counts as lying on it


def _getEndSide(value: float, a: float, b: float) -> _tp.Optional[int]:
    """If value is (within the tolerance) an end of [a, b]: the side the line comes from (-1 / +1)."""
    low, high = min(a, b), max(a, b)
    if abs(value - low) <= _END_ON_LINE_TOLERANCE:
        return 1  # the line goes from here towards larger values
    if abs(value - high) <= _END_ON_LINE_TOLERANCE:
        return -1
    return None


def _findCrossings(editor: _ed.Editor) -> list[_Crossing]:  # type: ignore[name-defined]
    """Two cases, between different pipes:
    - real crossing: both pipes go straight through the point -> the horizontal pipe jumps;
    - false junction: one pipe ends exactly on another pipe that goes straight through (looks like
      a tee, but nothing is connected; real junctions always are tee pieces, where all pipes end)
      -> the pipe going through jumps over the end of the other one."""
    lines = _getPipeLines(editor)
    horizontals = [line for line in lines if _isHorizontal(line)]
    verticals = [line for line in lines if _isVertical(line)]
    crossings = []
    for horizontal in horizontals:
        y = horizontal.start.y()
        hx0, hx1 = horizontal.start.x(), horizontal.end.x()
        for vertical in verticals:
            if vertical.owner is horizontal.owner:
                continue  # crossings of a pipe with itself (and the two lines of a double pipe)
            x = vertical.start.x()
            vy0, vy1 = vertical.start.y(), vertical.end.y()
            horizontalGoesThrough = _isStrictlyInside(x, hx0, hx1, horizontal.minDistanceFromEnd)
            verticalGoesThrough = _isStrictlyInside(y, vy0, vy1, vertical.minDistanceFromEnd)
            point = _qtc.QPointF(x, y)
            if horizontalGoesThrough and verticalGoesThrough:
                crossings.append(_Crossing(point, horizontal.pen, vertical.pen, True, None))
            elif horizontalGoesThrough:
                side = _getEndSide(y, vy0, vy1)  # the vertical pipe ends on the horizontal one
                if side is not None:
                    crossings.append(_Crossing(point, horizontal.pen, vertical.pen, True, side))
            elif verticalGoesThrough:
                side = _getEndSide(x, hx0, hx1)  # the horizontal pipe ends on the vertical one
                if side is not None:
                    crossings.append(_Crossing(point, vertical.pen, horizontal.pen, False, side))
    return _withoutDuplicates(crossings)


def _withoutDuplicates(crossings: list[_Crossing]) -> list[_Crossing]:
    """The same spot can be found twice (e.g. via a pipe and via the tee piece it ends at)."""
    unique: list[_Crossing] = []
    for crossing in crossings:
        if not any(_isSamePoint(crossing.point, other.point) or (
            abs(crossing.point.x() - other.point.x()) < 3 and abs(crossing.point.y() - other.point.y()) < 3
        ) for other in unique):
            unique.append(crossing)
    return unique
