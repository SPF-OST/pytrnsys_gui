from __future__ import annotations

import collections.abc as _cabc
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

import trnsysGUI.components.plugin.specification.model as _smodel

if _tp.TYPE_CHECKING:
    import trnsysGUI.BlockItem as _bi
    import trnsysGUI.electrical.connection as _econn

GREEN = _qtg.QColor(26, 158, 58)

TerminalSpec = _smodel.ElectricalTerminal

# Terminals of the built-in components (plugin components define them in their `spec.yaml`, under
# `electrical-terminals`). Positions are in the coordinates of the component, i.e. on its edge.
_BUILT_IN_TERMINALS: _cabc.Mapping[str, _cabc.Sequence[TerminalSpec]] = {
    "HP": [TerminalSpec(name="El", position=(80, 120), direction="in")],
    "HPTwoHx": [TerminalSpec(name="El", position=(80, 120), direction="in")],
    "HPDoubleDual": [
        TerminalSpec(name="El", position=(80, 120), direction="in")
    ],
    "HPDual": [TerminalSpec(name="El", position=(80, 120), direction="in")],
    "AirSourceHP": [
        TerminalSpec(name="El", position=(80, 120), direction="in")
    ],
    "PV": [TerminalSpec(name="El", position=(80, 100), direction="out")],
    "powerBlock": [
        TerminalSpec(name="El", position=(180, 160), direction="out")
    ],
}


def getTerminalSpecs(blockItem: _bi.BlockItem) -> _cabc.Sequence[TerminalSpec]:
    pluginSpecs = getattr(blockItem, "electricalTerminalSpecs", None)
    if pluginSpecs:
        return pluginSpecs
    return _BUILT_IN_TERMINALS.get(blockItem.name, ())


def addTerminals(blockItem: _bi.BlockItem) -> None:
    blockItem.electricalTerminals = [  # type: ignore[attr-defined]
        ElectricalTerminalItem(spec, blockItem)
        for spec in getTerminalSpecs(blockItem)
    ]


def getTerminals(
    blockItem: _qtw.QGraphicsItem,
) -> list[ElectricalTerminalItem]:
    return getattr(blockItem, "electricalTerminals", [])


class ElectricalTerminalItem(_qtw.QGraphicsEllipseItem):
    """Green empty dot on the edge of a component. Drag from one terminal to another to connect them."""

    RADIUS = 3.5

    def __init__(self, spec: TerminalSpec, blockItem: _bi.BlockItem) -> None:
        radius = self.RADIUS
        super().__init__(-radius, -radius, 2 * radius, 2 * radius, blockItem)

        self.name = spec.name
        self.direction = spec.direction
        self.blockItem = blockItem
        self.connections: list[_econn.ElectricalConnection] = []

        self.setPos(*spec.position)
        self.setPen(_qtg.QPen(GREEN, 1.3))
        self.setBrush(_qtg.QBrush(_qtc.Qt.white))
        self.setFlag(self.ItemSendsScenePositionChanges, True)
        self.setAcceptHoverEvents(True)
        self.setCursor(_qtg.QCursor(_qtc.Qt.CrossCursor))
        self._updateToolTip()

        self._dragLine: _qtw.QGraphicsLineItem | None = None

    @property
    def editor(self):
        return self.blockItem.editor

    @property
    def qualifiedName(self) -> str:
        return f"{self.blockItem.displayName}.{self.name}"

    def _updateToolTip(self) -> None:
        directions = {
            "in": "receives power",
            "out": "delivers power",
            "bi": "both directions",
        }
        self.setToolTip(
            f"Electrical terminal {self.name} ({directions[self.direction]})"
        )

    def getOutwardNormal(self) -> _qtc.QPointF:
        """Unit vector in scene coordinates pointing away from the component."""
        x, y = self.pos().x(), self.pos().y()
        w, h = self.blockItem.w, self.blockItem.h
        distancesAndNormals = [
            (x, (-1, 0)),
            (w - x, (1, 0)),
            (y, (0, -1)),
            (h - y, (0, 1)),
        ]
        _, (nx, ny) = min(distancesAndNormals, key=lambda dn: dn[0])
        start = self.blockItem.mapToScene(_qtc.QPointF(x, y))
        end = self.blockItem.mapToScene(_qtc.QPointF(x + nx, y + ny))
        return end - start

    # pylint: disable=invalid-name
    def itemChange(self, change, value):
        if change == self.ItemScenePositionHasChanged:
            for connection in self.connections:
                connection.updatePath()
        elif change == self.ItemSceneChange and value is None:
            # the component is removed from the diagram: its connections go with it
            for connection in list(self.connections):
                connection.delete()
        return super().itemChange(change, value)

    def hoverEnterEvent(self, event):
        self.setBrush(_qtg.QBrush(GREEN.lighter(170)))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(_qtg.QBrush(_qtc.Qt.white))
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() != _qtc.Qt.LeftButton or self.editor.isFrozen:
            event.ignore()
            return

        start = self.scenePos()
        self._dragLine = _qtw.QGraphicsLineItem(_qtc.QLineF(start, start))
        pen = _qtg.QPen(GREEN, 2, _qtc.Qt.DashLine)
        self._dragLine.setPen(pen)
        self.scene().addItem(self._dragLine)
        event.accept()

    def mouseMoveEvent(self, event):
        if self._dragLine:
            self._dragLine.setLine(
                _qtc.QLineF(self.scenePos(), event.scenePos())
            )

    def mouseReleaseEvent(self, event):
        if not self._dragLine:
            return

        self.scene().removeItem(self._dragLine)
        self._dragLine = None

        target = self._findTerminalAt(event.scenePos())
        if target:
            import trnsysGUI.electrical.connection as _econn  # pylint: disable=import-outside-toplevel

            _econn.connect(self, target)

    def _findTerminalAt(
        self, scenePos: _qtc.QPointF
    ) -> ElectricalTerminalItem | None:
        searchRect = _qtc.QRectF(
            scenePos - _qtc.QPointF(5, 5), _qtc.QSizeF(10, 10)
        )
        for item in self.scene().items(searchRect):
            if (
                isinstance(item, ElectricalTerminalItem)
                and item.blockItem is not self.blockItem
            ):
                return item
        return None
