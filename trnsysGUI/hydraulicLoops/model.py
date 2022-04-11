from __future__ import annotations

__all__ = ["Fluid", "HydraulicLoop", "HydraulicLoops", "Fluids"]

import abc as _abc
import itertools as _it
import typing as _tp

import trnsysGUI.common as _com

from . import _serialization as _ser

if _tp.TYPE_CHECKING:
    import trnsysGUI.connection.singlePipeConnection as _spc  # type: ignore[name-defined]

Fluid = _ser.Fluid
Variable = _ser.Variable


class Name(_abc.ABC):
    def __init__(self, value: str):
        self.value = value

    @property
    @_abc.abstractmethod
    def isUserDefined(self) -> bool:
        raise NotImplementedError()


class UserDefinedName(Name):
    @property
    def isUserDefined(self) -> bool:
        return True


class AutomaticallyGeneratedName(Name):
    @property
    def isUserDefined(self) -> bool:
        return False


class HydraulicLoop:
    def __init__(
        self,
        name: Name,
        fluid: _ser.Fluid,
        useLoopWideDefaults: bool,
        connections: _tp.Sequence[_spc.SinglePipeConnection],  # type: ignore[name-defined]
    ) -> None:
        self.name = name
        self.fluid = fluid
        self.connections: _tp.List[_spc.SinglePipeConnection] = [*connections]  # type: ignore[name-defined]
        self.useLoopWideDefaults = useLoopWideDefaults

    def addConnection(self, connection: _spc.SinglePipeConnection) -> None:  # type: ignore[name-defined]
        if self.containsConnection(connection):
            raise ValueError(f"Connection '{connection.displayName}' already part of hydraulic loop '{self.name}'.")

        self.connections.append(connection)

    def removeConnection(self, connection: _spc.SinglePipeConnection) -> None:  # type: ignore[name-defined]
        if not self.containsConnection(connection):
            raise ValueError(f"Connection '{connection.displayName}' does not belong to hydraulic loop {self.name}.")

        self.connections.remove(connection)

    def containsConnection(self, connection: _spc.SinglePipeConnection):  # type: ignore[name-defined]
        return connection in self.connections


class HydraulicLoops:
    def __init__(self, hydraulicLoops: _tp.Sequence[HydraulicLoop]) -> None:
        duplicateNames = _getDuplicates(l.name.value for l in hydraulicLoops)
        if duplicateNames:
            raise ValueError(
                f"Hydraulic loop names must be unique (the following names were duplicated: {','.join(duplicateNames)})."
            )

        self.hydraulicLoops = list(hydraulicLoops)

    @classmethod
    def createFromJson(
        cls,
        sequence: _tp.Sequence[_tp.Dict],
        connections: _tp.Sequence[_spc.SinglePipeConnection],  # type: ignore[name-defined]
        fluids: "Fluids",
    ) -> "HydraulicLoops":
        serializedLoops = [_ser.HydraulicLoop.from_dict(o) for o in sequence]

        connectionsByTrnsysId = {c.trnsysId: c for c in connections}

        loops = []
        for serializedLoop in serializedLoops:
            loop = cls._createLoop(serializedLoop, connectionsByTrnsysId, fluids)
            loops.append(loop)

        return HydraulicLoops(loops)

    @classmethod
    def _createLoop(
        cls,
        serializedLoop: _ser.HydraulicLoop,
        connectionsByTrnsysId: _tp.Mapping[int, _spc.SinglePipeConnection],  # type: ignore[name-defined]
        fluids: "Fluids",
    ) -> HydraulicLoop:
        name = cls._createName(serializedLoop)

        fluid = fluids.getFluid(serializedLoop.fluidName)
        assert fluid, f"Unknown fluid {serializedLoop.fluidName}"

        useLoopWideDefaults = serializedLoop.useLoopWideDefaults

        connections = [connectionsByTrnsysId[i] for i in serializedLoop.connectionsTrnsysId]

        loop = HydraulicLoop(name, fluid, useLoopWideDefaults, connections)
        return loop

    def toJson(self) -> _tp.Sequence[_tp.Dict]:
        result = []
        for loop in self.hydraulicLoops:
            connectionTrnsysIds = [c.trnsysId for c in loop.connections]
            serializedLoop = _ser.HydraulicLoop(
                loop.name.value, loop.name.isUserDefined, loop.fluid.name, loop.useLoopWideDefaults, connectionTrnsysIds
            )
            json = serializedLoop.to_dict()
            result.append(json)

        return result

    @staticmethod
    def _createName(serializedLoop: _ser.HydraulicLoop) -> Name:
        isUserDefinedName = serializedLoop.hasUserDefinedName
        nameValue = serializedLoop.name
        name = UserDefinedName(nameValue) if isUserDefinedName else AutomaticallyGeneratedName(nameValue)
        return name

    def getLoopForExistingConnection(
        self, connection: _spc.SinglePipeConnection  # type: ignore[name-defined]
    ) -> HydraulicLoop:
        loops = {l for l in self.hydraulicLoops if connection in l.connections}
        loop = _com.getSingle(loops)
        return loop

    def getLoop(self, name: str) -> _tp.Optional[HydraulicLoop]:
        loop = _getSingleOrNone(l for l in self.hydraulicLoops if l.name.value == name)
        return loop

    def addLoop(self, loop: HydraulicLoop) -> None:
        if self.getLoop(loop.name.value):
            raise ValueError(f"Loop with name '{loop.name.value}' already exists.")

        self.hydraulicLoops.append(loop)

    def removeLoop(self, loop: HydraulicLoop) -> None:
        self.hydraulicLoops.remove(loop)

    def clear(self):
        self.hydraulicLoops = []

    def generateName(self) -> AutomaticallyGeneratedName:
        for i in range(1, 100000):
            candidateName = f"loop{i}"
            if not self.getLoop(candidateName):
                generatedName = candidateName
                return AutomaticallyGeneratedName(generatedName)

        raise AssertionError(f"Failed to generate new name after {i} tries.")


class Fluids:
    WATER = _ser.Fluid("water", specificHeatCapacityInJPerKgK=Variable("CPWAT_SI"), densityInKgPerM3=Variable("RHOWAT"))
    BRINE = _ser.Fluid("brine", specificHeatCapacityInJPerKgK=Variable("CPBRI_SI"), densityInKgPerM3=Variable("RHOBRI"))

    def __init__(self, fluids: _tp.Sequence[_ser.Fluid]) -> None:
        duplicateNames = _getDuplicates(f.name for f in fluids)
        if duplicateNames:
            raise ValueError(
                f"Fluid names must be unique (the following names were duplicated: {','.join(duplicateNames)})."
            )

        fluidList = [*fluids]

        haveWater = any(f.name == self.WATER.name for f in fluidList)
        if not haveWater:
            fluidList.append(self.WATER)

        haveBrine = any(f.name == self.BRINE.name for f in fluidList)
        if not haveBrine:
            fluidList.append(self.BRINE)

        self.fluids = sorted(fluidList, key=lambda f: f.name)

    @staticmethod
    def createFromJson(sequence: _tp.Sequence[_tp.Dict]) -> "Fluids":
        fluids = [_ser.Fluid.from_dict(o) for o in sequence]
        return Fluids(fluids)

    def toJson(self) -> _tp.Sequence[_tp.Dict]:
        result = [f.to_dict() for f in self.fluids]
        return result

    def getFluid(self, name: str) -> _tp.Optional[_ser.Fluid]:
        fluid = _getSingleOrNone(f for f in self.fluids if f.name == name)
        return fluid


_TValue = _tp.TypeVar("_TValue", covariant=True)


class _SupportsLessThan(_tp.Protocol):
    def __lt__(self, other: _tp.Any) -> bool:
        ...


_SupportsLessThanT = _tp.TypeVar("_SupportsLessThanT", bound=_SupportsLessThan)


def _getDuplicates(values: _tp.Iterable[_SupportsLessThanT]) -> _tp.Sequence[_SupportsLessThanT]:
    sortedValues = sorted(values)
    groupedValues = _it.groupby(sortedValues)
    duplicateValues = [k for k, g in groupedValues if len(list(g)) > 1]
    return duplicateValues


def _getSingleOrNone(values: _tp.Iterable[_TValue]) -> _tp.Optional[_TValue]:
    valuesList = [*values]
    if not valuesList:
        return None

    numberOfValues = len(valuesList)
    assert numberOfValues == 1, f"Expected 0 or 1 value, but got {numberOfValues}."

    return valuesList[0]
