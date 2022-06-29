from __future__ import annotations

import typing as _tp

import trnsysGUI.PortItemBase as _pi

if _tp.TYPE_CHECKING:
    import trnsysGUI.BlockItem as _bi
    import trnsysGUI.connection.singlePipeConnection as _spc

GetInternallyConnectedPortItems = _tp.Callable[["SinglePipePortItem"], _tp.Sequence["SinglePipePortItem"]]
Side = _tp.Literal[0, 2]


class SinglePipePortItem(_pi.PortItemBase):
    def __init__(
        self,
        name: str,
        side: Side,
        parent: _bi.BlockItem,
        getInternallyConnectedPortItems: GetInternallyConnectedPortItems,
    ) -> None:
        super().__init__(name, side, parent)

        self.getInternallyConnectedPortItems = getInternallyConnectedPortItems

    def getConnection(self) -> _spc.SinglePipeConnection:
        connection = super().getConnection()
        return _tp.cast("_spc.SinglePipeConnection", connection)

    def _highlightInternallyConnectedPortItems(self):
        for portItem in self.getInternallyConnectedPortItems(self):
            portItem.innerCircle.setBrush(self.ashColorB)

    def _unhighlightInternallyConnectedPortItems(self):
        for portItem in self.getInternallyConnectedPortItems(self):
            portItem.innerCircle.setBrush(self.visibleColor)
