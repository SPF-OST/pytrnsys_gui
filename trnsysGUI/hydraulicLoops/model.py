from __future__ import annotations

__all__ = ["Fluid", "HydraulicLoop", "HydraulicLoops", "Fluids"]

import abc as _abc
import itertools as _it
import typing as _tp

import trnsysGUI.PortItem as _pi  # type: ignore[name-defined]
from . import _search
from . import _serialization as _ser

if _tp.TYPE_CHECKING:
    import trnsysGUI.Connection as _conn  # type: ignore[name-defined]

Fluid = _ser.Fluid


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
        self, name: Name,
            fluid: _ser.Fluid,
            connections: _tp.Sequence[_conn.Connection]  # type: ignore[name-defined]
    ) -> None:
        self.name = name
        self.fluid = fluid
        self.connections: _tp.List[_conn.Connection] = [*connections]  # type: ignore[name-defined]

    def addConnection(self, connection: _conn.Connection) -> None:  # type: ignore[name-defined]
        if self.containsConnection(connection):
            raise ValueError(f"Connection '{connection.displayName}' already part of hydraulic loop '{self.name}'.")

        self.connections.append(connection)

    def removeConnection(self, connection: _conn.Connection) -> None:  # type: ignore[name-defined]
        if not self.containsConnection(connection):
            raise ValueError(f"Connection '{connection.displayName}' does not belong to hydraulic loop {self.name}.")

    def containsConnection(self, connection: _conn.Connection):  # type: ignore[name-defined]
        return connection in self.connections


class HydraulicLoops:
    def __init__(self, hydraulicLoops: _tp.Sequence[HydraulicLoop]) -> None:
        duplicateNames = _getDuplicates(l.name.value for l in hydraulicLoops)
        if duplicateNames:
            raise ValueError(
                f"Hydraulic loop names must be unique (the following names were duplicated: {','.join(duplicateNames)})."
            )

        self.hydraulicLoops = [*hydraulicLoops]

    @classmethod
    def createFromJson(
            cls,
            sequence: _tp.Sequence[_tp.Dict],
            connections: _tp.Sequence[_conn.Connection], # type: ignore[name-defined]
            fluids: "Fluids"
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
        connectionsByTrnsysId: _tp.Mapping[int, _conn.Connection],  # type: ignore[name-defined]
        fluids: "Fluids",
    ) -> HydraulicLoop:
        name = cls._createName(serializedLoop)

        fluid = fluids.getFluid(serializedLoop.fluidName)
        assert fluid, f"Unknown fluid {serializedLoop.fluidName}"

        connections = [connectionsByTrnsysId[i] for i in serializedLoop.connectionsTrnsysId]

        loop = HydraulicLoop(name, fluid, connections)
        return loop

    @staticmethod
    def _createName(serializedLoop: _ser.HydraulicLoop) -> Name:
        isUserDefinedName = serializedLoop.hasUserDefinedName
        nameValue = serializedLoop.name
        name = UserDefinedName(nameValue) if isUserDefinedName else AutomaticallyGeneratedName(nameValue)
        return name

    def getLoopForPortItem(self, portItem: _pi.PortItem) -> _tp.Optional[HydraulicLoop]:  # type: ignore[name-defined]
        connections = _search.getReachableConnections(portItem)
        loops = {self._getLoopForConnection(c) for c in connections}
        loop = _getSingleOrNone(loops)
        return loop

    def getLoop(self, name: str) -> _tp.Optional[HydraulicLoop]:
        loop = _getSingleOrNone(l for l in self.hydraulicLoops if l.name == name)
        return loop

    def addLoop(self, loop: HydraulicLoop) -> None:
        if self.getLoop(loop.name.value):
            raise ValueError(f"Loop with name '{loop.name.value}' already exists.")

        self.hydraulicLoops.append(loop)

    def removeLoop(self, loop: HydraulicLoop) -> None:
        self.hydraulicLoops.remove(loop)

    def generateName(self) -> AutomaticallyGeneratedName:
        for i in range(1, 100000):
            candidateName = f"loop{i}"
            if not self.getLoop(candidateName):
                generatedName = candidateName
                return AutomaticallyGeneratedName(generatedName)

        raise AssertionError(f"Failed to generate new name after {i} tries.")

    def _getLoopForConnection(self, connection: _conn.Connection) -> HydraulicLoop:  # type: ignore[name-defined]
        loops = {l for l in self.hydraulicLoops if connection in l.connections}
        loop = _getSingle(loops)
        return loop


class Fluids:
    WATER = _ser.Fluid("water", specificHeatCapacityInJPerKgK=418.45, densityInKgPerM3=997)
    BRINE = _ser.Fluid("brine", specificHeatCapacityInJPerKgK=2360, densityInKgPerM3=1113.2)

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

        haveBrine = any(f.name == self.BRINE for f in fluidList)
        if not haveBrine:
            fluidList.append(self.BRINE)

        self.fluids = sorted(fluidList, key=lambda f: f.name)

    @staticmethod
    def createFromJson(sequence: _tp.Sequence[_tp.Dict]) -> "Fluids":
        fluids = [_ser.Fluid.from_dict(o) for o in sequence]
        return Fluids(fluids)

    def getFluid(self, name: str) -> _tp.Optional[_ser.Fluid]:
        fluid = _getSingleOrNone(f for f in self.fluids if f.name == name)
        return fluid


_TValue = _tp.TypeVar("_TValue", covariant=True)


class _SupportsLessThan(_tp.Protocol):
    def __lt__(self, __other: _tp.Any) -> bool:
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


def _getSingle(values: _tp.Iterable[_TValue]) -> _TValue:
    value = _getSingleOrNone(values)
    assert value is not None, "Expected a single value but got none."
    return value
