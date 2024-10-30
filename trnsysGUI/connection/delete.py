import typing as _tp

import PyQt5.QtWidgets as _qtw


def deleteGraphicsItem(item: _qtw.QGraphicsItem) -> None:
    scene = item.scene()
    item.setParentItem(None)  # type: ignore[arg-type]
    if scene:
        scene.removeItem(item)


def deleteChildGraphicsItems(
    item: _qtw.QGraphicsItem,
    exclude: _tp.Optional[_tp.Sequence[_qtw.QGraphicsItem]] = None,
) -> None:
    if not exclude:
        exclude = []

    children = list(i for i in item.childItems() if i not in exclude)
    for child in children:
        deleteGraphicsItem(child)
