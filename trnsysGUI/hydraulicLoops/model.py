import typing as _tp
import itertools as _it

import trnsysGUI.Connection as _conn

from . import serialization as _ser


class HydraulicLoop:
    def __init__(self, name: str, fluid: _ser.Fluid, connections: _tp.Sequence[_conn.Connection]) -> None:
        self.name = name
        self.fluid = fluid
        self.connections = [*connections]

    def addConnection(self, connection: _conn.Connection) -> None:
        if self.containsConnection(connection):
            raise ValueError(f"Connection '{connection.displayName}' already part of hydraulic loop '{self.name}'.")

        self.connections.append(connection)

    def removeConnection(self, connection: _conn.Connection) -> None:
        if not self.containsConnection(connection):
            raise ValueError(f"Connection '{connection.displayName}' does not belong to hydraulic loop {self.name}.")

    def containsConnection(self, connection: _conn.Connection):
        return connection in self.connections


class HydraulicLoops:
    def __init__(self, hydraulicLoops: _tp.Sequence[HydraulicLoop]) -> None:
        duplicateNames = _getDuplicates(l.name for l in hydraulicLoops)
        if duplicateNames:
            raise ValueError(
                f"Hydraulic loop names must be unique (the following names were duplicated: {','.join(duplicateNames)})."
            )

        self.hydraulicLoops = [*hydraulicLoops]

    @staticmethod
    def createFromJson(self, sequence: _tp.Sequence[_tp.Dict]) -> "HydraulicLoops":
        hydraulicLoops = [_ser.HydraulicLoop.from_dict(o) for o in sequence]
        return HydraulicLoops(hydraulicLoops)

    def addLoop(self, loop: HydraulicLoop) -> None:
        if self.getLoop(loop.name):
            raise ValueError(f"There already exists a loop with name '{loop.name}'.")

        self.hydraulicLoops.append(loop)

    def removeLoop(self, loop: HydraulicLoop) -> None:
        if not self.getLoop(loop.name):
            raise ValueError(f"Unknown loop: '{loop.name}'.")

    def getLoop(self, name: str) -> _tp.Optional[HydraulicLoop]:
        return _getUnique(name, self.hydraulicLoops, lambda l: l.name)


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
        return _getUnique(name, self.fluids, lambda f: f.name)


_TValue = _tp.TypeVar("_TValue", covariant=True)
_TKey = _tp.TypeVar("_TKey", covariant=True)
_Projection = _tp.Callable[[_TValue], _TKey]


def _getDuplicates(values: _tp.Iterable[_TValue]) -> _tp.Sequence[_TValue]:
    sortedValues = sorted(values)
    groupedValues = _it.groupby(sortedValues)
    duplicateValues = [k for k, g in groupedValues if len(*g) > 1]
    return duplicateValues


def _getUnique(key: _TKey, values: _tp.Sequence[_TValue], projection: _Projection) -> _tp.Optional[_TValue]:
    matchingValues = [v for v in values if projection(v) == key]
    if not matchingValues:
        return None

    assert matchingValues == 1

    return matchingValues[0]
