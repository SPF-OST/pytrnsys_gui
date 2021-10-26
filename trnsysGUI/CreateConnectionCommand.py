# pylint: skip-file
# type: ignore

from PyQt5.QtWidgets import QUndoCommand

from trnsysGUI.Connection import Connection


class CreateConnectionCommand(QUndoCommand):
    def __init__(self, fromPort, toPort, segmentItemFactory, connParent, descr):
        super().__init__(descr)
        self.conn = None
        self.connFromPort = fromPort
        self.connToPort = toPort
        self.segmentItemFactory = segmentItemFactory
        self.connParent = connParent

    def redo(self):
        self.conn = Connection(self.connFromPort, self.connToPort, self.segmentItemFactory, self.connParent)

    def undo(self):
        if self.conn in self.conn.parent.connectionList:
            self.conn.deleteConn()
