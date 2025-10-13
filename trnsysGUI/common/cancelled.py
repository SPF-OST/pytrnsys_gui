import typing as _tp


class Cancelled:
    pass


CANCELLED = Cancelled()

type MaybeCancelled[T] = T | Cancelled


def isCancelled[
    T  # pylint: disable=redefined-outer-name
](maybeCancelled: MaybeCancelled[T],) -> _tp.TypeGuard[Cancelled]:
    if maybeCancelled == CANCELLED:
        return True

    if isinstance(maybeCancelled, Cancelled):
        raise AssertionError(
            f"Don't instantiate {Cancelled} but use the variable `CANCELLED' instead."
        )

    return False


def value[
    T  # pylint: disable=redefined-outer-name
](maybeCancelled: MaybeCancelled[T]) -> T:
    if isCancelled(maybeCancelled):
        raise ValueError("Value was cancelled.")

    return _tp.cast(T, maybeCancelled)
