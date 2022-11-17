import dataclasses as _dc
import os as _os
import random as _rnd
import shutil as _sh
import typing as _tp

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMenu, QMessageBox, QTreeView

import trnsysGUI.connection.names as _cnames
import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.names as _mnames
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.storageTank.model as _model
import trnsysGUI.storageTank.side as _sd
import trnsysGUI.temperatures as _temps
from trnsysGUI import idGenerator as _id
from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.MyQFileSystemModel import MyQFileSystemModel  # type: ignore[attr-defined]
from trnsysGUI.MyQTreeView import MyQTreeView  # type: ignore[attr-defined]
from trnsysGUI.directPortPair import DirectPortPair
from trnsysGUI.heatExchanger import HeatExchanger  # type: ignore[attr-defined]
from trnsysGUI.singlePipePortItem import SinglePipePortItem
from trnsysGUI.storageTank.ConfigureStorageDialog import ConfigureStorageDialog
from trnsysGUI.type1924.createType1924 import Type1924_TesPlugFlow  # type: ignore[attr-defined]
import trnsysGUI.hydraulicLoops.model as _hlm
import trnsysGUI.hydraulicLoops.names as _lnames

InOut = _tp.Literal["In", "Out"]
_T_co = _tp.TypeVar("_T_co", covariant=True)


@_dc.dataclass
class PortIds:
    inputId: int
    outputId: int


class StorageTank(BlockItem, _ip.HasInternalPiping):
    # pylint: disable=too-many-instance-attributes,too-many-public-methods
    HEAT_EXCHANGER_WIDTH = 40

    def __init__(self, trnsysType, parent, **kwargs) -> None:
        super().__init__(trnsysType, parent, **kwargs)

        self.parent = parent

        self._hydraulicLoops: _tp.Optional[_hlm.HydraulicLoops] = None

        self._idGenerator: _id.IdGenerator = self.parent.parent().idGen
        self.dckFilePath = ""

        self.directPortPairs: _tp.List[DirectPortPair] = []

        self.heatExchangers: _tp.List[HeatExchanger] = []

        self.nTes = self.parent.parent().idGen.getStoragenTes()
        self.storageType = self.parent.parent().idGen.getStorageType()

        self.changeSize()

        self.path = None
        self.addTree()

    def setHydraulicLoops(self, hydraulicLoops: _hlm.HydraulicLoops) -> None:
        self._hydraulicLoops = hydraulicLoops

    def getDisplayName(self) -> str:
        return self.displayName

    def hasDdckPlaceHolders(self) -> bool:
        return False

    @property
    def leftDirectPortPairsPortItems(self):
        return self._getDirectPortPairPortItems(_sd.Side.LEFT)

    @property
    def rightDirectPortPairsPortItems(self):
        return self._getDirectPortPairPortItems(_sd.Side.RIGHT)

    def _getDirectPortPairPortItems(self, side: _sd.Side):
        return [p for dpp in self.directPortPairs if dpp.side == side for p in [dpp.fromPort, dpp.toPort]]

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.STORAGE_TANK_SVG

    # Setter functions
    def setParent(self, p):
        self.logger.debug("Setting parent of Storage Tank (and its hx)")
        self.parent = p

        if self not in self.parent.parent().trnsysObj:
            self.parent.parent().trnsysObj.append(self)

        for heatExchanger in self.heatExchangers:
            heatExchanger.parent = self

    def addDirectPortPair(  # pylint: disable=too-many-arguments
        self,
        trnsysId: int,
        side: _sd.Side,
        relativeInputHeight: float,
        relativeOutputHeight: float,
        storageTankHeight: float,
        portIds: _tp.Optional[PortIds] = None,
    ):
        inputPort = self._createPort("i", relativeInputHeight, storageTankHeight, side)
        outputPort = self._createPort("o", relativeOutputHeight, storageTankHeight, side)

        randomInt = int(_rnd.uniform(20, 200))
        randomColor = QColor(randomInt, randomInt, randomInt)
        self._setPortColor(inputPort, randomColor)
        self._setPortColor(outputPort, randomColor)

        if portIds:
            inputPort.id = portIds.inputId
            outputPort.id = portIds.outputId

        directPortPair = DirectPortPair(trnsysId, inputPort, outputPort, relativeInputHeight, relativeOutputHeight, side)

        self.directPortPairs.append(directPortPair)

        self.inputs = [*self.inputs, directPortPair.fromPort]
        self.outputs = [*self.outputs, directPortPair.toPort]

    def _createPort(
        self, name: str, relativeHeight: float, storageTankHeight: float, side: _sd.Side
    ) -> SinglePipePortItem:
        sideNr = side.toSideNr()
        portItem = _cspi.createSinglePipePortItem(name, sideNr, self)
        portItem.setZValue(100)
        xPos = 0 if side == _sd.Side.LEFT else self.w
        yPos = storageTankHeight - relativeHeight * storageTankHeight
        portItem.setPos(xPos, yPos)
        portItem.side = sideNr
        return portItem

    @staticmethod
    def _setPortColor(portItem: SinglePipePortItem, color: QColor) -> None:
        portItem.innerCircle.setBrush(color)
        portItem.visibleColor = color

    def addHeatExchanger(self, name, trnsysId, side, relativeInputHeight, relativeOutputHeight):
        heatExchanger = HeatExchanger(
            trnsysId=trnsysId,
            sideNr=side.toSideNr(),
            width=self.HEAT_EXCHANGER_WIDTH,
            relativeInputHeight=relativeInputHeight,
            relativeOutputHeight=relativeOutputHeight,
            storageTankWidth=self.w,
            storageTankHeight=self.h,
            parent=self,
            name=name,
        )
        return heatExchanger

    def updateImage(self):
        super().updateImage()
        self.label.setPos(self.label.pos().x(), self.h)

    def updatePortItemPositionsAfterTankSizeChange(self, deltaH, deltaW):
        for portItem in self.inputs + self.outputs:
            oldRelativeHeight = portItem.pos().y() / self.h
            if portItem.side == 0:
                portItem.setPos(portItem.pos().x(), oldRelativeHeight * (self.h + deltaH))
            else:
                portItem.setPos(portItem.pos().x() + deltaW, oldRelativeHeight * (self.h + deltaH))

    def updateHeatExchangersAfterTankSizeChange(self):
        for heatExchanger in self.heatExchangers:
            heatExchanger.setTankSize(self.w, self.h)

    def encode(self):
        if not self.isVisible():
            raise RuntimeError("Cannot encode an invisible storage tank.")

        heatExchangerModels = self._getHeatExchangerModelsForEncode()
        portPairModels = self._getDirectPortPairModelsForEncode()
        position = float(self.pos().x()), float(self.pos().y())

        storageTankModel = _model.StorageTank(
            self.flippedH,
            self.flippedV,
            self.name,
            self.displayName,
            self.id,
            self.trnsysId,
            self.h,
            position,
            heatExchangerModels,
            portPairModels,
        )

        dictName = "Block-"
        return dictName, storageTankModel.to_dict()

    def _getDirectPortPairModelsForEncode(self):
        portPairModels = []
        for directPort in self.directPortPairs:
            side = _sd.Side.createFromSideNr(directPort.fromPort.side)

            inputPortModel = _model.Port(directPort.fromPort.id, directPort.relativeInputHeight)

            outputPortModel = _model.Port(directPort.toPort.id, directPort.relativeOutputHeight)

            portPairModel = _model.PortPair(side, directPort.trnsysId, inputPortModel, outputPortModel)

            directPortPairModel = _model.DirectPortPair(portPairModel)

            portPairModels.append(directPortPairModel)

        return portPairModels

    def _getHeatExchangerModelsForEncode(self):
        heatExchangerModels = []
        for heatExchanger in self.heatExchangers:
            side = _sd.Side.createFromSideNr(heatExchanger.sSide)

            inputPort = _model.Port(
                heatExchanger.port1.id,
                heatExchanger.relativeInputHeight,
            )

            outputPort = _model.Port(
                heatExchanger.port2.id,
                heatExchanger.relativeOutputHeight,
            )

            portPair = _model.PortPair(side, heatExchanger.trnsysId, inputPort, outputPort)

            heatExchangerModel = _model.HeatExchanger(
                portPair, heatExchanger.displayName, heatExchanger.w, self.id, heatExchanger.id
            )

            heatExchangerModels.append(heatExchangerModel)

        return heatExchangerModels

    def decode(self, i, resBlockList):
        offsetX = 0
        offsetY = 0
        self._decodeInternal(i, offsetX, offsetY, resBlockList, shallSetNamesAndIDs=True)

    def _decodeInternal(  # pylint: disable=too-many-arguments
        self,
        i,
        offsetX,
        offsetY,
        resBlockList,
        shallSetNamesAndIDs: bool,
    ):
        self.logger.debug("Loading a Storage in Decoder")

        model = _model.StorageTank.from_dict(i)

        self.flippedH = model.isHorizontallyFlipped

        if shallSetNamesAndIDs:
            self.displayName = model.BlockDisplayName

        self.changeSize()
        self.h = model.height
        self.updateImage()

        self.setPos(model.position[0] + offsetX, model.position[1] + offsetY)

        if shallSetNamesAndIDs:
            self.trnsysId = model.trnsysId
            self.id = model.id

        for heatExchangerModel in model.heatExchangers:
            self._decodeHeatExchanger(heatExchangerModel, shallSetNamesAndIDs)

        for portPairModel in model.directPortPairs:
            self._decodeDirectPortPair(portPairModel)

        resBlockList.append(self)

    def _decodeDirectPortPair(
        self,
        portPairModel: _model.DirectPortPair,
    ) -> None:
        portPair = portPairModel.portPair

        portIds = PortIds(portPair.inputPort.id, portPair.outputPort.id)

        self.addDirectPortPair(
            portPair.trnsysId,
            portPair.side,
            portPair.inputPort.relativeHeight,
            portPair.outputPort.relativeHeight,
            storageTankHeight=self.h,
            portIds=portIds,
        )

    def _decodeHeatExchanger(self, heatExchangerModel: _model.HeatExchanger, shallSetNamesAndIDs: bool):
        portPair = heatExchangerModel.portPair

        nameSuffix = "" if shallSetNamesAndIDs else "New"
        name = heatExchangerModel.name + nameSuffix

        heatExchanger = self.addHeatExchanger(
            name, portPair.trnsysId, portPair.side, portPair.inputPort.relativeHeight, portPair.outputPort.relativeHeight
        )

        if shallSetNamesAndIDs:
            heatExchanger.setId(heatExchangerModel.id)

        heatExchanger.port1.id = portPair.inputPort.id
        heatExchanger.port2.id = portPair.outputPort.id

    def decodePaste(  # pylint: disable=too-many-arguments
        self, i, offset_x, offset_y, resConnList, resBlockList, **kwargs
    ):
        self._decodeInternal(i, offset_x, offset_y, resBlockList, shallSetNamesAndIDs=False)

    def assignIDsToUninitializedValuesAfterJsonFormatMigration(
        self, generator: _id.IdGenerator
    ) -> None:  # type: ignore[attr-defined]
        for heatExchanger in self.heatExchangers:
            if heatExchanger.trnsysId == generator.UNINITIALIZED_ID:
                heatExchanger.trnsysId = generator.getTrnsysID()

        for directPortPair in self.directPortPairs:
            if directPortPair.trnsysId == generator.UNINITIALIZED_ID:
                directPortPair.trnsysId = generator.getTrnsysID()

    def _getHeatExchangerForPortItem(self, portItem: SinglePipePortItem) -> _tp.Optional[HeatExchanger]:
        heatExchanger = self._getSingleOrNone(hx for hx in self.heatExchangers if portItem in [hx.port1, hx.port2])

        return heatExchanger

    def _getDirectPortPairForPortItemOrNone(self, portItem: SinglePipePortItem) -> _tp.Optional[DirectPortPair]:
        directPortPair = self._getSingleOrNone(
            dpp for dpp in self.directPortPairs if portItem in [dpp.fromPort, dpp.toPort]
        )

        return directPortPair

    @staticmethod
    def _getSingleOrNone(iterable: _tp.Iterable[_T_co]) -> _tp.Optional[_T_co]:
        sequence = list(iterable)

        if not sequence:
            return None

        if len(sequence) > 1:
            raise ValueError("More than one value in iterable.")

        return sequence[0]

    # Misc
    def contextMenuEvent(self, event):
        menu = QMenu()

        launchNotepadAction = menu.addAction("Launch NotePad++")
        launchNotepadAction.triggered.connect(self.launchNotepadFile)

        rotateRightIcon = _img.ROTATE_TO_RIGHT_PNG.icon()
        rotateRightAction = menu.addAction(rotateRightIcon, "Rotate Block clockwise")
        rotateRightAction.triggered.connect(self.rotateBlockCW)

        rotateLeftIcon = _img.ROTATE_LEFT_PNG.icon()
        rotateLeftIcon = menu.addAction(rotateLeftIcon, "Rotate Block counter-clockwise")
        rotateLeftIcon.triggered.connect(self.rotateBlockCCW)

        resetRotationAction = menu.addAction("Reset Rotation")
        resetRotationAction.triggered.connect(self.resetRotation)

        printRotationAction = menu.addAction("Print Rotation")
        printRotationAction.triggered.connect(self.printRotation)

        deleteBlockAction = menu.addAction("Delete this Block")
        deleteBlockAction.triggered.connect(self.deleteBlockCom)

        exportDdckAction = menu.addAction("Export ddck")
        exportDdckAction.triggered.connect(self.exportDck)

        menu.exec(event.screenPos())

    def mouseDoubleClickEvent(self, event):
        ConfigureStorageDialog(self, self.scene().parent())

    def getInternalPiping(self) -> _ip.InternalPiping:
        heatExchangerNodes = [hx.modelPipe for hx in self.heatExchangers]
        heatExchangerPortItems = {
            mpi: gpi
            for hx in self.heatExchangers
            for mpi, gpi in [(hx.modelPipe.fromPort, hx.port1), (hx.modelPipe.toPort, hx.port2)]
        }

        portPairNodes = [pp.modelPipe for pp in self.directPortPairs]
        portPairsPortItems = {
            mpi: gpi
            for pp in self.directPortPairs
            for mpi, gpi in [(pp.modelPipe.fromPort, pp.fromPort), (pp.modelPipe.toPort, pp.toPort)]
        }

        nodes = [*heatExchangerNodes, *portPairNodes]
        modelPortItemsToGraphicalPortItem = heatExchangerPortItems | portPairsPortItems

        return _ip.InternalPiping(nodes, modelPortItemsToGraphicalPortItem)

    def exportDck(self) -> None:  # pylint: disable=too-many-locals,too-many-statements
        if not self._areAllPortsConnected():
            msgb = QMessageBox()
            msgb.setText("Please connect all ports before exporting!")
            msgb.exec_()
            return
        success = self._debugConn()

        if not success:
            qmb = QMessageBox()
            qmb.setText("Ignore connection errors and continue with export?")
            qmb.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
            qmb.setDefaultButton(QMessageBox.Cancel)
            ret = qmb.exec()
            if ret == QMessageBox.Save:
                self.logger.debug("Overwriting")
            else:
                self.logger.debug("Canceling")
                return

        nPorts = len(self.directPortPairs)
        nHx = len(self.heatExchangers)

        tool = Type1924_TesPlugFlow()

        inputs = {
            "nUnit": 50,
            "nType": self.storageType,
            "nTes": self.nTes,
            "nPorts": nPorts,
            "nHx": nHx,
            "nHeatSources": 1,
        }

        directPairsPorts = self._getDirectPairPortsForExport()

        heatExchangerPorts = self._getHeatExchangerPortsForExport()

        auxiliaryPorts = self._getAuxiliaryPortForExport(inputs)

        tool.setInputs(inputs, directPairsPorts, heatExchangerPorts, auxiliaryPorts)

        tool.createDDck(self.path, self.displayName, typeFile="ddck")

    def _getDirectPairPortsForExport(self):
        directPairsPorts = []
        for directPortPair in self.directPortPairs:
            incomingConnection = directPortPair.fromPort.getConnection()
            inputTemperatureName = _cnames.getTemperatureVariableName(incomingConnection, _mfn.PortItemType.STANDARD)

            modelPipe = directPortPair.modelPipe
            massFlowRateName = _mnames.getMassFlowVariableName(self, modelPipe, modelPipe.fromPort)

            outgoingConnection = directPortPair.toPort.getConnection()
            reverseInputTemperatureName = _cnames.getTemperatureVariableName(
                outgoingConnection, _mfn.PortItemType.STANDARD
            )

            inputPos = directPortPair.relativeInputHeight
            outputPos = directPortPair.relativeOutputHeight

            outputTemperatureName = _temps.getInternalTemperatureVariableName(self, modelPipe)

            directPairsPort = {
                "T": inputTemperatureName,
                "side": directPortPair.side.formatDdck(),
                "Mfr": massFlowRateName,
                "Trev": reverseInputTemperatureName,
                "zIn": inputPos,
                "zOut": outputPos,
                "Tout": outputTemperatureName,
            }
            directPairsPorts.append(directPairsPort)
        return directPairsPorts

    def _getHeatExchangerPortsForExport(self):
        heatExchangerPorts = []
        for heatExchanger in self.heatExchangers:
            heatExchangerPort = self._getHeatExchangerPortForExport(heatExchanger)

            heatExchangerPorts.append(heatExchangerPort)
        return heatExchangerPorts

    def _getHeatExchangerPortForExport(self, heatExchanger):  # pylint: disable=too-many-locals
        heatExchangerName = heatExchanger.displayName

        incomingConnection = heatExchanger.port1.getConnection()
        inputTemperatureName = _cnames.getTemperatureVariableName(incomingConnection, _mfn.PortItemType.STANDARD)
        modelPipe = heatExchanger.modelPipe
        massFlowRateName = _mnames.getMassFlowVariableName(self, modelPipe, modelPipe.fromPort)

        outgoingConnection = heatExchanger.port2.getConnection()
        reverseInputTemperatureName = _cnames.getTemperatureVariableName(outgoingConnection, _mfn.PortItemType.STANDARD)

        inputPos = heatExchanger.relativeInputHeight
        outputPos = heatExchanger.relativeOutputHeight

        outputTemperatureName = _temps.getInternalTemperatureVariableName(self, modelPipe)

        loop = self._hydraulicLoops.getLoopForExistingConnection(incomingConnection)
        loopName = loop.name.value

        heatExchangerPort = {
            "Name": heatExchangerName,
            "T": inputTemperatureName,
            "Mfr": massFlowRateName,
            "Trev": reverseInputTemperatureName,
            "zIn": inputPos,
            "zOut": outputPos,
            "Tout": outputTemperatureName,
            "cp": _lnames.getHeatCapacityName(loopName),
            "rho": _lnames.getDensityName(loopName),
        }

        return heatExchangerPort

    @staticmethod
    def _getAuxiliaryPortForExport(inputs):
        auxiliaryPorts = []
        for _ in range(inputs["nHeatSources"]):
            dictInputAux = {"zAux": 0.0, "qAux": 0.0}
            auxiliaryPorts.append(dictInputAux)
        return auxiliaryPorts

    def _debugConn(self):
        self.logger.debug("Debugging conn")
        errorConnList = ""
        for directPort in self.directPortPairs:
            stFromPort = directPort.fromPort
            stToPort = directPort.toPort
            toPort1 = stFromPort.connectionList[0].toPort
            fromPort2 = stToPort.connectionList[0].fromPort
            connName1 = stFromPort.connectionList[0].displayName
            connName2 = stToPort.connectionList[0].displayName

            if stFromPort != toPort1:
                errorConnList = errorConnList + connName1 + "\n"
            if stToPort != fromPort2:
                errorConnList = errorConnList + connName2 + "\n"
        if errorConnList != "":
            msgBox = QMessageBox()
            msgBox.setText(f"{errorConnList} is connected wrongly, right click StorageTank to invert connection.")
            msgBox.exec()
            noError = False
        else:
            noError = True

        return noError

    def _areAllPortsConnected(self):
        for heatExchanger in self.heatExchangers:
            if not heatExchanger.port1.connectionList:
                return False
            if not heatExchanger.port2.connectionList:
                return False

        for ports in self.leftDirectPortPairsPortItems:
            if not ports.connectionList:
                return False

        for ports in self.rightDirectPortPairsPortItems:
            if not ports.connectionList:
                return False

        return True

    def addTree(self):
        """
        When a blockitem is added to the main window.
        A file explorer for that item is added to the right of the main window by calling this method
        """
        pathName = self.displayName
        if self.parent.parent().projectPath == "":
            self.path = self.parent.parent().projectFolder
        else:
            self.path = self.parent.parent().projectPath
        self.path = _os.path.join(self.path, "ddck")
        self.path = _os.path.join(self.path, pathName)
        if not _os.path.exists(self.path):
            _os.makedirs(self.path)

        self.model = MyQFileSystemModel()
        self.model.setRootPath(self.path)
        self.model.setName(self.displayName)
        self.tree = MyQTreeView(self.model, self)
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(self.path))
        self.tree.setObjectName(f"{self.displayName}Tree")
        self.tree.setMinimumHeight(200)
        self.tree.setSortingEnabled(True)
        self.parent.parent().splitter.addWidget(self.tree)

    def deleteBlock(self):
        """
        Overridden method to also delete folder
        """
        self.logger.debug("Block " + str(self) + " is deleting itself (" + self.displayName + ")")
        self.parent.parent().trnsysObj.remove(self)
        self.logger.debug("deleting block " + str(self) + self.displayName)
        self.parent.scene().removeItem(self)
        widgetToRemove = self.parent.parent().findChild(QTreeView, self.displayName + "Tree")
        _sh.rmtree(self.path)
        try:
            widgetToRemove.hide()
        except AttributeError:
            self.logger.debug("Widget doesnt exist!")
        else:
            self.logger.debug("Deleted widget")
        del self

    def setDisplayName(self, newName):
        """
        Overridden method to also change folder name
        """
        self.displayName = newName
        self.label.setPlainText(newName)
        self.model.setName(self.displayName)
        self.tree.setObjectName(f"{self.displayName}Tree")
        self.logger.debug(_os.path.dirname(self.path))
        destPath = _os.path.join(_os.path.split(self.path)[0], self.displayName)
        if _os.path.split(self.path)[-1] == "" or _os.path.split(self.path)[-1] == "ddck":
            _os.makedirs(destPath)
        else:
            if _os.path.exists(self.path):
                _os.rename(self.path, destPath)
        self.path = destPath
        self.logger.debug(self.path)
