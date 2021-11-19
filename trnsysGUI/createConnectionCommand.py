from PyQt5.QtWidgets import QUndoCommand

from trnsysGUI.Connection import Connection  # type: ignore[name-defined, attr-defined]


class CreateConnectionCommand(QUndoCommand):
    def __init__(self, fromPort, toPort, connectionParent):
        super().__init__("Create connection")
        self.connection = None
        self._fromPort = fromPort
        self._toPort = toPort
        self._connectionParent = connectionParent

    def redo(self):
        self.connection = Connection(self._fromPort, self._toPort, self._connectionParent)

        super().redo()

    def undo(self):
        super().undo()

        self.connection.deleteConn()
        self.connection = None
