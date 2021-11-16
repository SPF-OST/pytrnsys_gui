# pylint: skip-file
# type: ignore

from PyQt5.QtWidgets import QUndoCommand

from trnsysGUI.DoublePipePortItem import DoublePipePortItem
from trnsysGUI.SinglePipePortItem import SinglePipePortItem
from trnsysGUI.connection.doublePipeConnection import DoublePipeConnection
from trnsysGUI.connection.singlePipeConnection import SinglePipeConnection


class CreateConnectionCommand(QUndoCommand):
    def __init__(self, fromPort, toPort, connParent, descr):
        super().__init__(descr)
        self.conn = None
        self.connFromPort = fromPort
        self.connToPort = toPort
        self.connParent = connParent

    def redo(self):
        if isinstance(self.connFromPort, SinglePipePortItem):
            self.conn = SinglePipeConnection(self.connFromPort, self.connToPort, self.connParent)
        if isinstance(self.connFromPort, DoublePipePortItem):
            self.conn = DoublePipeConnection(self.connFromPort, self.connToPort, self.connParent)

    def undo(self):
        if self.conn in self.conn.parent.connectionList:
            self.conn.deleteConn()
