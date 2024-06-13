import collections.abc
import collections.abc as _cabc

import pydantic as _pc

Ports = collections.abc.Mapping[str, tuple[int, int]]


class Connection(_pc.BaseModel):
    name: str
    ports: Ports


class Specification(_pc.BaseModel):
    name: str
    description: str
    connections: _cabc.Sequence[Connection]
    size: tuple[int, int]
