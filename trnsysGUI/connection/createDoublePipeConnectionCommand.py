# pylint: skip-file
# type: ignore

from trnsysGUI.connection.createConnectionCommandBase import CreateConnectionCommandBase
from trnsysGUI.connection.doublePipeConnection import DoublePipeConnection


class CreateDoublePipeConnectionCommand(CreateConnectionCommandBase):
    def __init__(self, fromPort, toPort, connParent, descr):
        super().__init__(fromPort, toPort, connParent, descr)

    def redo(self):
        self.conn = DoublePipeConnection(self.connFromPort, self.connToPort, self.connParent)

        super().redo()
