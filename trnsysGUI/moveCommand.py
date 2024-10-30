import PyQt5.QtCore as _qtc
import PyQt5.QtWidgets as _qtw


class MoveCommand(_qtw.QUndoCommand):
    def __init__(
        self,
        graphicsItem: _qtw.QGraphicsItem,
        *,
        oldScenePos: _qtc.QPointF,
        newScenePos: _qtc.QPointF,
        descr: str
    ) -> None:
        super().__init__(descr)
        self._oldScenePos = oldScenePos
        self._newScenePos = newScenePos
        self._item = graphicsItem

    def redo(self) -> None:
        self._setScenePos(self._newScenePos)

    def undo(self) -> None:
        self._setScenePos(self._oldScenePos)

    def _setScenePos(self, scenePos: _qtc.QPointF) -> None:
        offset = self._item.scenePos() - self._item.pos()
        newPos = scenePos - offset
        self._item.setPos(newPos)
