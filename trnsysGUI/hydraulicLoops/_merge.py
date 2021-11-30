from __future__ import annotations

import typing as _tp

import PyQt5.QtWidgets as _qtw

import trnsysGUI.connection.singlePipeConnection as _spc
import trnsysGUI.singlePipePortItem as _spi
from . import _mergeLoopsDialog as _md
from . import model as _model

if _tp.TYPE_CHECKING:
    import trnsysGUI.connection.createSinglePipeConnectionCommand as _cspc


def merge(
    fromPort: _spi.SinglePipePortItem,  # type: ignore[name-defined]
    toPort: _spi.SinglePipePortItem,  # type: ignore[name-defined]
    hydraulicLoops: _model.HydraulicLoops,
    defaultFluid: _model.Fluid,
    createConnectionCommand: _cspc.CreateSinglePipeConnectionCommand,  # type: ignore[name-defined]
) -> _tp.Optional["UndoCommand"]:
    merger = _Merger(hydraulicLoops, defaultFluid)

    return merger.createUndoCommand(fromPort, toPort, createConnectionCommand)


class _Merger:
    def __init__(self, hydraulicLoops: _model.HydraulicLoops, defaultFluid: _model.Fluid) -> None:
        self._hydraulicLoops = hydraulicLoops
        self.defaultFluid = defaultFluid

    def createUndoCommand(
        self,
        fromPort: _spi.SinglePipePortItem,  # type: ignore[name-defined]
        toPort: _spi.SinglePipePortItem,  # type: ignore[name-defined]
        createConnectionCommand: _cspc.CreateSinglePipeConnectionCommand,  # type: ignore[name-defined]
    ) -> _tp.Optional["UndoCommand"]:
        fromLoop = self._hydraulicLoops.getLoopForPortItem(fromPort)
        toLoop = self._hydraulicLoops.getLoopForPortItem(toPort)

        if not fromLoop and not toLoop:
            name = self._hydraulicLoops.generateName()
            return _CreateUndoCommand(name, self.defaultFluid, self._hydraulicLoops, createConnectionCommand)

        if fromLoop and not toLoop:
            return _ExtendUndoCommand(fromLoop, createConnectionCommand)

        if not fromLoop and toLoop:
            return _ExtendUndoCommand(toLoop, createConnectionCommand)

        # The following line is needed to make mypy happy
        assert fromLoop and toLoop

        mergedNameAndFluid = self._getMergedNameAndFluidOrNone(fromLoop, toLoop)
        if not mergedNameAndFluid:
            return None
        mergedName, mergedFluid = mergedNameAndFluid

        return _MergeUndoCommandCommand(
            fromLoop, toLoop, mergedName, mergedFluid, self._hydraulicLoops, createConnectionCommand
        )

    def _getMergedNameAndFluidOrNone(
        self, loop1: _model.HydraulicLoop, loop2: _model.HydraulicLoop
    ) -> _tp.Optional[_tp.Tuple[_model.Name, _model.Fluid]]:
        mergedName = self._getMergedNameOrNone(loop1.name, loop2.name)
        areSameFluids = loop1.fluid != loop2.fluid

        if areSameFluids and mergedName:
            return mergedName, loop1.fluid

        cancellable = _md.MergeLoopsDialog.showDialogAndGetResult(loop1, loop2)
        if cancellable == "cancelled":
            return None

        mergeResult = cancellable
        return mergeResult.name, mergeResult.fluid  # pylint: disable=no-member

    def _getMergedNameOrNone(self, name1: _model.Name, name2: _model.Name) -> _tp.Optional[_model.Name]:
        if name1.isUserDefined and not name2.isUserDefined:
            return name1

        if not name1.isUserDefined and name2.isUserDefined:
            return name2

        if not name1.isUserDefined and not name2.isUserDefined:
            return self._hydraulicLoops.generateName()

        return None


class UndoCommand(_qtw.QUndoCommand):
    def __init__(
        self, label: str, createConnectionCommand: _cspc.CreateSinglePipeConnectionCommand  # type: ignore[name-defined]
    ) -> None:
        super().__init__(label, createConnectionCommand)
        self._createConnectionCommand = createConnectionCommand

    def _getConnection(self) -> _tp.Optional[_spc.SinglePipeConnection]:  # type: ignore[name-defined]
        connection = self._createConnectionCommand.conn
        assert connection
        return connection


class _CreateUndoCommand(UndoCommand):
    def __init__(
        self,
        name: _model.AutomaticallyGeneratedName,
        fluid: _model.Fluid,
        hydraulicLoops: _model.HydraulicLoops,
        createConnectionCommand,
        shallDeleteOnRedo: bool = False,
    ) -> None:
        label = "Create loop" if shallDeleteOnRedo else "Delete loop"
        super().__init__(label, createConnectionCommand)

        self._name = name
        self._fluid = fluid
        self._hydraulicLoops = hydraulicLoops
        self._shallDeleteOnRedo = shallDeleteOnRedo

    def redo(self) -> None:
        if self._shallDeleteOnRedo:
            self._deleteLoop()
        else:
            self._createLoop()

    def undo(self) -> None:
        if self._shallDeleteOnRedo:
            self._createLoop()
        else:
            self._deleteLoop()

    def _createLoop(self) -> None:
        connections = [self._getConnection()]
        loop = _model.HydraulicLoop(self._name, self._fluid, connections)
        self._hydraulicLoops.addLoop(loop)

    def _deleteLoop(self):
        loop = self._hydraulicLoops.getLoop(self._name.value)
        self._hydraulicLoops.removeLoop(loop)


class _ExtendUndoCommand(UndoCommand):
    def __init__(
        self,
        loop: _model.HydraulicLoop,
        createConnectionCommand: _cspc.CreateSinglePipeConnectionCommand,  # type: ignore[name-defined]
        shallRemoveFromLoopOnRedo: bool = False,
    ) -> None:
        label = "Shrink hydraulic loop" if shallRemoveFromLoopOnRedo else "Extend hydraulic loop"
        super().__init__(label, createConnectionCommand)
        self._shallRemoveFromLoopOnRedo = shallRemoveFromLoopOnRedo
        self._loop = loop

    def redo(self) -> None:
        if self._shallRemoveFromLoopOnRedo:
            self._removeFromLoop()
        else:
            self._addToLoop()

        super().redo()

    def _addToLoop(self) -> None:
        connection = self._getConnection()
        self._loop.addConnection(connection)

    def undo(self) -> None:
        super().undo()

        if self._shallRemoveFromLoopOnRedo:
            self._addToLoop()
        else:
            self._removeFromLoop()

    def _removeFromLoop(self) -> None:
        connection = self._getConnection()
        self._loop.removeConnection(connection)


class _MergeUndoCommandCommand(UndoCommand):
    def __init__(  # pylint: disable=too-many-arguments
        self,
        loop1: _model.HydraulicLoop,
        loop2: _model.HydraulicLoop,
        mergedName: _model.Name,
        mergedFluid: _model.Fluid,
        hydraulicLoops: _model.HydraulicLoops,
        createConnectionCommand: _cspc.CreateSinglePipeConnectionCommand,  # type: ignore[name-defined]
        shallSplitOnRedo: bool = False,
    ) -> None:
        label = "Split hydraulic loop" if shallSplitOnRedo else "Merge hydraulic loops"
        super().__init__(label, createConnectionCommand)

        self._loop1 = loop1
        self._loop2 = loop2

        self._mergedName = mergedName
        self._mergedFluid = mergedFluid

        self._hydraulicLoops = hydraulicLoops

        self._shallSplitOnRedo = shallSplitOnRedo

    def redo(self) -> None:
        if self._shallSplitOnRedo:
            self._splitMergedLoop()
        else:
            self._mergeLoops()

        super().redo()

    def undo(self) -> None:
        super().undo()

        if self._shallSplitOnRedo:
            self._mergeLoops()
        else:
            self._splitMergedLoop()

    def _mergeLoops(self) -> None:
        connection = self._getConnection()
        mergedConnections = [*self._loop1.connections, *self._loop2.connections, connection]
        mergedConnections.sort(key=lambda c: c.displayName)
        mergedLoop = _model.HydraulicLoop(self._mergedName, self._mergedFluid, mergedConnections)
        self._hydraulicLoops.removeLoop(self._loop1)
        self._hydraulicLoops.removeLoop(self._loop2)
        self._hydraulicLoops.addLoop(mergedLoop)

    def _splitMergedLoop(self) -> None:
        mergedLoop = self._hydraulicLoops.getLoop(self._mergedName.value)
        assert mergedLoop, f"Could not find loop {self._mergedName.value}."
        self._hydraulicLoops.removeLoop(mergedLoop)
        self._hydraulicLoops.addLoop(self._loop1)
        self._hydraulicLoops.addLoop(self._loop2)
