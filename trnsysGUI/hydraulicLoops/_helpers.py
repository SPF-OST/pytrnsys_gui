from trnsysGUI import singlePipePortItem as _spi


def getFromAndToPort(connection):
    fromPort = connection.fromPort
    toPort = connection.toPort
    assert isinstance(fromPort, _spi.SinglePipePortItem)
    assert isinstance(toPort, _spi.SinglePipePortItem)
    return fromPort, toPort
