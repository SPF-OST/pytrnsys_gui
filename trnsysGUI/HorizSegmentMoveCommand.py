# pylint: skip-file
# type: ignore

from PyQt5.QtWidgets import QUndoCommand


class HorizSegmentMoveCommand(QUndoCommand):
    def __init__(self, segment, oldX, descr):
        super(HorizSegmentMoveCommand, self).__init__(descr)
        self.oldX = oldX
        self.newX = segment.startNode.parent.scenePos().x()
        self.seg = segment

    def redo(self):
        try:
            self.seg.startNode.parent.scenePos().y()
            self.seg.endNode.parent.scenePos().y()
        except AttributeError:
            pass
        else:
            self.seg.startNode.parent.setPos(self.newX, self.seg.startNode.parent.scenePos().y())
            self.seg.endNode.parent.setPos(self.newX, self.seg.endNode.parent.scenePos().y())

    def undo(self):
        try:
            self.seg.startNode.parent.scenePos().y()
            self.seg.endNode.parent.scenePos().y()
        except AttributeError:
            pass
        else:
            self.seg.startNode.parent.setPos(self.oldX, self.seg.startNode.parent.scenePos().y())
            self.seg.endNode.parent.setPos(self.oldX, self.seg.endNode.parent.scenePos().y())
