import trnsysGUI.segments.singlePipeSegmentItem as _spsi
import trnsysGUI.segments.doublePipeSegmentItem as _dpsi


def createSegmentItem(startNode, endNode, connection, connectionType):
    if connectionType == "SinglePipeConnection":
        return _spsi.SinglePipeSegmentItem(startNode, endNode, connection)

    if connectionType == "DoublePipeConnection":
        return _dpsi.DoublePipeSegmentItem(startNode, endNode, connection)

    raise NotImplementedError()
