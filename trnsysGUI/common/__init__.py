import typing as _tp

T = _tp.TypeVar("T")  # pylint: disable=invalid-name


def getSingle(iterable: _tp.Iterable[T]) -> T:
    values = [*iterable]

    if not values:
        raise ValueError("Expected one element but got none.")

    if len(values) > 1:
        raise ValueError("Expected one element but got more than one.")

    return values[0]
