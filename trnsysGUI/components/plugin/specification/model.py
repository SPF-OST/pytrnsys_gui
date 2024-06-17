import collections.abc as _cabc
import typing as _tp

import pydantic as _pc

PortType = _tp.Literal["standard", "hot", "cold"]


class Port(_pc.BaseModel):
    name: str | None = None
    position: tuple[int, int]
    type: PortType = "standard"


class Connection(_pc.BaseModel):
    name: str
    input: Port
    output: Port


class Specification(_pc.BaseModel):
    defaultName: str
    description: str
    connections: _cabc.Sequence[Connection]
    size: tuple[int, int]
