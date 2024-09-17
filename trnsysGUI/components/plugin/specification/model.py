import collections.abc as _cabc
import typing as _tp

import pydantic as _pc

PortType = _tp.Literal["standard", "hot", "cold"]


def _nameMustBeCapitalized(what: _tp.Literal["Connection", "Port"], name: str | None) -> str | None:
    if name is None:
        return None
    
    if name != name.capitalize():
        raise ValueError(f"{what} names must be capitalized.")

    return name


class Port(_pc.BaseModel):
    name: str | None = None
    position: tuple[int, int]
    type: PortType = "standard"

    @_pc.field_validator("name")
    @classmethod
    def nameMustBeCapitalized(cls, name: str | None) -> str:
        return _nameMustBeCapitalized("Port", name)


class Connection(_pc.BaseModel):
    name: str
    input: Port
    output: Port

    @_pc.field_validator("name")
    @classmethod
    def nameMustBeCapitalized(cls, name: str) -> str:
        return _nameMustBeCapitalized("Connection", name)


class Specification(_pc.BaseModel):
    defaultName: str
    description: str
    connections: _cabc.Sequence[Connection]
    size: tuple[int, int]
