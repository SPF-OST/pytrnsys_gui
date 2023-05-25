from trnsysGUI.connection import singlePipeConnection as _spc, doublePipeConnection as _dpc
from trnsysGUI.segments import singlePipeSegmentItem as _spsi, doublePipeSegmentItem as _dpsi


def createSegmentItem(startNode, endNode, connection):
    if isinstance(connection, _spc.SinglePipeConnection):
        return _spsi.SinglePipeSegmentItem(startNode, endNode, connection)

    elif isinstance(connection, _dpc.DoublePipeConnection):
        return _dpsi.DoublePipeSegmentItem(startNode, endNode, connection)

    else:
        raise NotImplementedError()