from __future__ import annotations

from PyQt5 import QtWidgets as _qtw


def deleteGraphicsItem(item: _qtw.QGraphicsItem) -> None:
    scene = item.scene()
    item.setParentItem(None)  # type: ignore[arg-type]
    if scene:
        scene.removeItem(item)


def deleteChildGraphicsItems(item: _qtw.QGraphicsItem) -> None:
    children = list(item.childItems())
    for child in children:
        deleteGraphicsItem(child)
