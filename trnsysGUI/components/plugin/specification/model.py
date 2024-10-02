import collections.abc as _cabc
import typing as _tp

import pydantic as _pc

PortType = _tp.Literal["standard", "hot", "cold"]


def _nameMustBeCapitalized(what: str, name: str | None) -> str | None:
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
    def nameMustBeCapitalized(cls, name: str | None) -> str | None:
        return _nameMustBeCapitalized(cls.__name__, name)


class Connection(_pc.BaseModel):
    name: str | None = None
    input: Port
    output: Port

    @_pc.field_validator("name")
    @classmethod
    def _nameMustBeCapitalized(cls, name: str | None) -> str | None:
        return _nameMustBeCapitalized(cls.__name__, name)


class TeePiece(_pc.BaseModel):
    name: str | None = None
    input: Port
    output0: Port
    output1: Port

    @_pc.field_validator("name")
    @classmethod
    def _nameMustBeCapitalized(cls, name: str | None) -> str | None:
        return _nameMustBeCapitalized(cls.__name__, name)


class Specification(_pc.BaseModel):
    defaultName: str
    description: str
    connections: _cabc.Sequence[Connection] | None = None
    teePieces: _cabc.Sequence[TeePiece] | None = _pc.Field(alias="tee-pieces", default=None)
    size: tuple[int, int]

    @_pc.model_validator(mode="after")
    def _oneConnectionOrTeePieceMustBeGiven(self) -> _tp.Self:
        if not self.connections and not self.teePieces:
            raise ValueError("At least one connection or T-piece must be specified.")

        return self

    @_pc.model_validator(mode="after")
    def _connectionOrTeePieceCanOmitNameOnlyIfSingle(self) -> _tp.Self:
        connections = self.connections or []
        teePieces = self.teePieces or []

        connectionsAndTeePieces = [*connections, *teePieces]
        hasWithoutName = any(tc for tc in connectionsAndTeePieces if not tc.name)
        nTeePiecesAndConnections = len(connectionsAndTeePieces)

        if hasWithoutName and nTeePiecesAndConnections > 1:
            return ValueError(
                "A connection or tee piece can only not have a name if there is only a single tee piece or single connection."
            )
