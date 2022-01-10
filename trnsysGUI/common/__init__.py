import typing as _tp

_T = _tp.TypeVar("_T")


def singleOrNone(iterable: _tp.Iterable[_T]) -> _tp.Optional[_T]:
    """The `iterable` will be fully exhausted."""
    lst = list(iterable)

    length = len(lst)

    if length == 0:
        return None

    if length == 1:
        return lst[0]

    raise ValueError("`iterable` contains more than one item", iterable)
