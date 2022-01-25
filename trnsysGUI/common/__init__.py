import typing as _tp

_T = _tp.TypeVar("_T")


def getSingle(iterable: _tp.Iterable[_T]) -> _T:
    """The `iterable` will be fully exhausted."""

    value = getSingleOrNone(iterable)

    if not value:
        raise ValueError("Expected one element but got none.")

    return value


def getSingleOrNone(iterable: _tp.Iterable[_T]) -> _tp.Optional[_T]:
    """The `iterable` will be fully exhausted."""

    values = [*iterable]

    if not values:
        return None

    if len(values) > 1:
        raise ValueError("Expected one element but got more than one.")

    return values[0]
