import typing as _tp


class Cancelled:
    pass


CANCELLED = Cancelled()
_T = _tp.TypeVar("_T")
MaybeCancelled = _tp.Union[_T, Cancelled]


def isCancelled(maybeCancelled: MaybeCancelled[_T]) -> bool:
    if maybeCancelled == CANCELLED:
        return True

    if isinstance(maybeCancelled, Cancelled):
        raise AssertionError(f"Don't instantiate {Cancelled} but use the variable `CANCELLED' instead.")

    return False


def value(maybeCancelled: MaybeCancelled[_T]) -> _T:
    if isCancelled(maybeCancelled):
        raise ValueError("Value was cancelled.")

    return _tp.cast(_T, maybeCancelled)
