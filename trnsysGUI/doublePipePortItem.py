from __future__ import annotations

import typing as _tp

import trnsysGUI.PortItemBase as _pi

if _tp.TYPE_CHECKING:
    import trnsysGUI.connection.doublePipeConnection as _dpc


class DoublePipePortItem(_pi.PortItemBase):
    def getConnection(self) -> _dpc.DoublePipeConnection:
        connection = super().getConnection()
        return _tp.cast("_dpc.DoublePipeConnection", connection)

    def _highlightInternallyConnectedPortItems(self):
        pass

    def _unhighlightInternallyConnectedPortItems(self):
        pass
