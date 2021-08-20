# pylint: skip-file
# type: ignore

from PyQt5.QtWidgets import QUndoCommand


class MoveCommand(QUndoCommand):
    def __init__(self, diagramItem, oldPos, descr):
        super(MoveCommand, self).__init__(descr)
        self.oldPos = oldPos
        self.newPos = diagramItem.scenePos()
        self.item = diagramItem

    def redo(self):
        self.item.setPos(self.newPos)

    def undo(self):
        self.item.setPos(self.oldPos)

    # mergeWith does not get execute, as opposed to the Qt reference
    # def mergeWith(self, mc):
    #     print("in mergeWith")
    #     item = mc.item
    #
    #     if self.item != item:
    #         return False
    #
    #     self.newPos = item.scenePos()
    #
    #     return True
