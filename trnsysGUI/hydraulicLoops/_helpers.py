import typing as _tp

from trnsysGUI import singlePipePortItem as _spi


def getFromAndToPort(connection):
    fromPort = connection.fromPort
    toPort = connection.toPort
    assert isinstance(fromPort, _spi.SinglePipePortItem)
    assert isinstance(toPort, _spi.SinglePipePortItem)
    return fromPort, toPort


T = _tp.TypeVar("T")  # pylint: disable=invalid-name


def getSingle(iterable: _tp.Iterable[T]) -> T:
    values = [*iterable]

    if not values:
        raise ValueError("Expected one element but got none.")

    if len(values) > 1:
        raise ValueError("Expected one element but got more than one.")

    return values[0]
