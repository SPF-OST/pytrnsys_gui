# pylint: skip-file
# type: ignore

from PyQt5.QtWidgets import QUndoCommand
from trnsysGUI.Connection import Connection


class DeleteConnectionCommand(QUndoCommand):
    def __init__(self, conn, descr):
        super().__init__(descr)
        self.conn = conn
        self.connFromPort = self.conn.fromPort
        self.connToPort = self.conn.toPort
        self.connParent = self.conn.parent

    def redo(self):
        self.conn.deleteConn()
        self.conn = None

    def undo(self):
        self.conn = Connection(self.connFromPort, self.connToPort, self.connParent)
