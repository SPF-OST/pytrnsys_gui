# pylint: skip-file
# type: ignore

from PyQt5.QtWidgets import QUndoCommand


class CreateConnectionCommandBase(QUndoCommand):
    def __init__(self, fromPort, toPort, connParent, descr):
        super().__init__(descr)
        self.conn = None
        self.connFromPort = fromPort
        self.connToPort = toPort
        self.connParent = connParent

    def undo(self):
        super().undo()

        if self.conn in self.conn.parent.connectionList:
            self.conn.deleteConn()
