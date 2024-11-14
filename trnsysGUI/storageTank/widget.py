import dataclasses as _dc
import pathlib as _pl
import random as _rnd
import typing as _tp

import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw
import dataclasses_jsonschema as _dcj

import trnsysGUI.blockItemGraphicItemMixins as _gimx
import trnsysGUI.blockItemHasInternalPiping as _bip
import trnsysGUI.components.ddckFolderHelpers as _dfh
import trnsysGUI.connection.names as _cnames
import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.hydraulicLoops.model as _hlm
import trnsysGUI.hydraulicLoops.names as _lnames
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.names as _mnames
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.names.rename as _rename
import trnsysGUI.storageTank.side as _sd
import trnsysGUI.temperatures as _temps
from trnsysGUI import idGenerator as _id
from trnsysGUI.directPortPair import DirectPortPair
from trnsysGUI.heatExchanger import HeatExchanger  # type: ignore[attr-defined]
from trnsysGUI.singlePipePortItem import SinglePipePortItem
from trnsysGUI.storageTank import model as _model
from trnsysGUI.storageTank.ConfigureStorageDialog import ConfigureStorageDialog
from trnsysGUI.type1924.createType1924 import Type1924_TesPlugFlow  # type: ignore[attr-defined]

InOut = _tp.Literal["In", "Out"]
_T_co = _tp.TypeVar("_T_co", covariant=True)


@_dc.dataclass
class PortIds:
    inputId: int
    outputId: int


class StorageTank(
    _bip.BlockItemHasInternalPiping, _gimx.SvgBlockItemGraphicItemMixin
):
    # pylint: disable=too-many-instance-attributes,too-many-public-methods
    HEAT_EXCHANGER_WIDTH = 40

    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(trnsysType, editor, displayName)

        self.parent = editor

        self._hydraulicLoops: _tp.Optional[_hlm.HydraulicLoops] = None

        self.dckFilePath = ""

        self.directPortPairs: _tp.List[DirectPortPair] = []

        self.heatExchangers: _tp.List[HeatExchanger] = []

        idGenerator: _id.IdGenerator = self.editor.idGen
        self.nTes = idGenerator.getStoragenTes()
        self.storageType = idGenerator.getStorageType()

        self.changeSize()

    def setHydraulicLoops(self, hydraulicLoops: _hlm.HydraulicLoops) -> None:
        self._hydraulicLoops = hydraulicLoops

    def getDisplayName(self) -> str:
        return self.displayName

    @classmethod
    @_tp.override
    def hasDdckPlaceHolders(cls) -> bool:
        return False

    @classmethod
    @_tp.override
    def hasDdckDirectory(cls) -> bool:
        return True

    @property
    def leftDirectPortPairsPortItems(self):
        return self._getDirectPortPairPortItems(_sd.Side.LEFT)

    @property
    def rightDirectPortPairsPortItems(self):
        return self._getDirectPortPairPortItems(_sd.Side.RIGHT)

    def _getDirectPortPairPortItems(self, side: _sd.Side):
        return [
            p
            for dpp in self.directPortPairs
            if dpp.side == side
            for p in [dpp.fromPort, dpp.toPort]
        ]

    @classmethod
    @_tp.override
    # pylint: disable=arguments-differ
    def _getImageAccessor(
        cls,
    ) -> _img.SvgImageAccessor:
        return _img.STORAGE_TANK_SVG

    # Setter functions
    def setParent(self, p):
        self.logger.debug("Setting parent of Storage Tank (and its hx)")
        self.parent = p

        for heatExchanger in self.heatExchangers:
            heatExchanger.storageTank = self

    def addDirectPortPair(  # pylint: disable=too-many-arguments
        self,
        trnsysId: int,
        side: _sd.Side,
        relativeInputHeight: float,
        relativeOutputHeight: float,
        storageTankHeight: float,
        portIds: _tp.Optional[PortIds] = None,
    ):
        inputPort = self._createPort(
            "i", relativeInputHeight, storageTankHeight, side
        )
        outputPort = self._createPort(
            "o", relativeOutputHeight, storageTankHeight, side
        )

        randomInt = int(_rnd.uniform(20, 200))
        randomColor = _qtg.QColor(randomInt, randomInt, randomInt)
        self._setPortColor(inputPort, randomColor)
        self._setPortColor(outputPort, randomColor)

        if portIds:
            inputPort.id = portIds.inputId
            outputPort.id = portIds.outputId

        directPortPair = DirectPortPair(
            trnsysId,
            inputPort,
            outputPort,
            relativeInputHeight,
            relativeOutputHeight,
            side,
        )

        self.directPortPairs.append(directPortPair)

        self.inputs = [*self.inputs, directPortPair.fromPort]
        self.outputs = [*self.outputs, directPortPair.toPort]

    def _createPort(
        self,
        name: str,
        relativeHeight: float,
        storageTankHeight: float,
        side: _sd.Side,
    ) -> SinglePipePortItem:
        portItem = _cspi.createSinglePipePortItem(name, self)
        portItem.setZValue(100)
        xPos = 0 if side == _sd.Side.LEFT else self.w
        yPos = storageTankHeight - relativeHeight * storageTankHeight
        portItem.setPos(xPos, yPos)
        return portItem

    @staticmethod
    def _setPortColor(
        portItem: SinglePipePortItem, color: _qtg.QColor
    ) -> None:
        portItem.innerCircle.setBrush(color)
        portItem.visibleColor = color

    def addHeatExchanger(
        self, name, trnsysId, side, relativeInputHeight, relativeOutputHeight
    ):
        heatExchanger = HeatExchanger(
            trnsysId=trnsysId,
            sideNr=side.toSideNr(),
            width=self.HEAT_EXCHANGER_WIDTH,
            relativeInputHeight=relativeInputHeight,
            relativeOutputHeight=relativeOutputHeight,
            storageTankWidth=self.w,
            storageTankHeight=self.h,
            storageTank=self,
            name=name,
        )
        return heatExchanger

    def updateImage(self):
        super().updateImage()
        self.label.setPos(self.label.pos().x(), self.h)

    def setSize(self, *, width: int, height: int) -> None:
        self.prepareGeometryChange()

        deltaH = height - self.h
        deltaW = width - self.w
        self.w = width
        self.h = height
        self._updatePortItemPositionsAfterTankSizeChange(deltaW, deltaH)
        self._updateHeatExchangersAfterTankSizeChange()

    def _updatePortItemPositionsAfterTankSizeChange(
        self, deltaW: int, deltaH: int
    ) -> None:
        for portItem in self.inputs + self.outputs:
            oldRelativeHeight = portItem.pos().y() / self.h
            if portItem.side == 0:
                portItem.setPos(
                    portItem.pos().x(), oldRelativeHeight * (self.h + deltaH)
                )
            else:
                portItem.setPos(
                    portItem.pos().x() + deltaW,
                    oldRelativeHeight * (self.h + deltaH),
                )

    def _updateHeatExchangersAfterTankSizeChange(self):
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

            inputPortModel = _model.Port(
                directPort.fromPort.id, directPort.relativeInputHeight
            )

            outputPortModel = _model.Port(
                directPort.toPort.id, directPort.relativeOutputHeight
            )

            portPairModel = _model.PortPair(
                side, directPort.trnsysId, inputPortModel, outputPortModel
            )

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

            portPair = _model.PortPair(
                side, heatExchanger.trnsysId, inputPort, outputPort
            )

            heatExchangerModel = _model.HeatExchanger(
                portPair,
                heatExchanger.displayName,
                heatExchanger.w,
                heatExchanger.id,
            )

            heatExchangerModels.append(heatExchangerModel)

        return heatExchangerModels

    def decode(self, i: _dcj.JsonDict, resBlockList: list) -> None:
        offsetX = 0
        offsetY = 0

        self.logger.debug("Loading a Storage in Decoder")

        model = _model.StorageTank.from_dict(i)
        self.flippedH = model.isHorizontallyFlipped
        self.displayName = model.BlockDisplayName

        self.changeSize()

        self.h = model.height

        self.updateImage()

        self.setPos(model.position[0] + offsetX, model.position[1] + offsetY)
        self.trnsysId = model.trnsysId

        for heatExchangerModel in model.heatExchangers:
            self._decodeHeatExchanger(heatExchangerModel, True)

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

    def _decodeHeatExchanger(
        self,
        heatExchangerModel: _model.HeatExchanger,
        shallSetNamesAndIDs: bool,
    ):
        portPair = heatExchangerModel.portPair

        nameSuffix = "" if shallSetNamesAndIDs else "New"
        name = heatExchangerModel.name + nameSuffix

        heatExchanger = self.addHeatExchanger(
            name,
            portPair.trnsysId,
            portPair.side,
            portPair.inputPort.relativeHeight,
            portPair.outputPort.relativeHeight,
        )

        if shallSetNamesAndIDs:
            heatExchanger.setId(heatExchangerModel.id)

        heatExchanger.port1.id = portPair.inputPort.id
        heatExchanger.port2.id = portPair.outputPort.id

    def assignIDsToUninitializedValuesAfterJsonFormatMigration(
        self, generator: _id.IdGenerator
    ) -> None:  # type: ignore[attr-defined]
        for heatExchanger in self.heatExchangers:
            if heatExchanger.trnsysId == generator.UNINITIALIZED_ID:
                heatExchanger.trnsysId = generator.getTrnsysID()

        for directPortPair in self.directPortPairs:
            if directPortPair.trnsysId == generator.UNINITIALIZED_ID:
                directPortPair.trnsysId = generator.getTrnsysID()

    def _getHeatExchangerForPortItem(
        self, portItem: SinglePipePortItem
    ) -> _tp.Optional[HeatExchanger]:
        heatExchanger = self._getSingleOrNone(
            hx
            for hx in self.heatExchangers
            if portItem in [hx.port1, hx.port2]
        )

        return heatExchanger

    def _getDirectPortPairForPortItemOrNone(
        self, portItem: SinglePipePortItem
    ) -> _tp.Optional[DirectPortPair]:
        directPortPair = self._getSingleOrNone(
            dpp
            for dpp in self.directPortPairs
            if portItem in [dpp.fromPort, dpp.toPort]
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
    def _addChildContextMenuActions(self, contextMenu: _qtw.QMenu) -> None:
        super()._addChildContextMenuActions(contextMenu)

        exportDdckAction = contextMenu.addAction("Export ddck")
        exportDdckAction.triggered.connect(self.exportDck)

    def mouseDoubleClickEvent(self, event: _qtw.QGraphicsSceneMouseEvent) -> None:
        dialog = self.createStorageDialog()
        dialog.exec()

    def createStorageDialog(self) -> ConfigureStorageDialog:
        renameHelper = _rename.RenameHelper(self.editor.namesManager)
        dialog = ConfigureStorageDialog(
            self, self.editor, renameHelper, self.editor.projectFolder
        )
        return dialog

    def getInternalPiping(self) -> _ip.InternalPiping:
        heatExchangerNodes = [hx.modelPipe for hx in self.heatExchangers]
        heatExchangerPortItems = {
            mpi: gpi
            for hx in self.heatExchangers
            for mpi, gpi in [
                (hx.modelPipe.fromPort, hx.port1),
                (hx.modelPipe.toPort, hx.port2),
            ]
        }

        portPairNodes = [pp.modelPipe for pp in self.directPortPairs]
        portPairsPortItems = {
            mpi: gpi
            for pp in self.directPortPairs
            for mpi, gpi in [
                (pp.modelPipe.fromPort, pp.fromPort),
                (pp.modelPipe.toPort, pp.toPort),
            ]
        }

        nodes = [*heatExchangerNodes, *portPairNodes]
        modelPortItemsToGraphicalPortItem = (
            heatExchangerPortItems | portPairsPortItems
        )

        return _ip.InternalPiping(nodes, modelPortItemsToGraphicalPortItem)

    def exportDck(
        self,
    ) -> None:  # pylint: disable=too-many-locals,too-many-statements
        if not self._areAllPortsConnected():
            msgb = _qtw.QMessageBox()
            msgb.setText("Please connect all ports before exporting!")
            msgb.exec_()
            return
        success = self._debugConn()

        if not success:
            qmb = _qtw.QMessageBox()
            qmb.setText("Ignore connection errors and continue with export?")
            qmb.setStandardButtons(
                _qtw.QMessageBox.Save | _qtw.QMessageBox.Cancel
            )
            qmb.setDefaultButton(_qtw.QMessageBox.Cancel)
            ret = qmb.exec()
            if ret == _qtw.QMessageBox.Save:
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

        tool.setInputs(
            inputs, directPairsPorts, heatExchangerPorts, auxiliaryPorts
        )

        projectDirPath = _pl.Path(self.editor.projectFolder)
        ddckDirPath = _dfh.getComponentDdckDirPath(
            self.displayName, projectDirPath
        )

        if not ddckDirPath.is_dir():
            _qtw.QMessageBox.information(
                None,
                "Component ddck directory doesn't exist",
                f"The component ddck directory `{ddckDirPath}` does not exist. The ddck file will not be exported. "
                f"Please create the directory and try again.",
            )
            return

        tool.createDDck(str(ddckDirPath), self.displayName, typeFile="ddck")

    def _getDirectPairPortsForExport(self):
        directPairsPorts = []
        for directPortPair in self.directPortPairs:
            incomingConnection = directPortPair.fromPort.getConnection()
            inputTemperatureName = _cnames.getTemperatureVariableName(
                incomingConnection, _mfn.PortItemType.STANDARD
            )

            modelPipe = directPortPair.modelPipe
            massFlowRateName = _mnames.getMassFlowVariableName(
                self.displayName, modelPipe, modelPipe.fromPort
            )

            outgoingConnection = directPortPair.toPort.getConnection()
            reverseInputTemperatureName = _cnames.getTemperatureVariableName(
                outgoingConnection, _mfn.PortItemType.STANDARD
            )

            inputPos = directPortPair.relativeInputHeight
            outputPos = directPortPair.relativeOutputHeight

            outputTemperatureName = _temps.getInternalTemperatureVariableName(
                componentDisplayName=self.displayName, nodeName=modelPipe.name
            )

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
            heatExchangerPort = self._getHeatExchangerPortForExport(
                heatExchanger
            )

            heatExchangerPorts.append(heatExchangerPort)
        return heatExchangerPorts

    def _getHeatExchangerPortForExport(
        self, heatExchanger
    ):  # pylint: disable=too-many-locals
        heatExchangerName = heatExchanger.displayName

        incomingConnection = heatExchanger.port1.getConnection()
        inputTemperatureName = _cnames.getTemperatureVariableName(
            incomingConnection, _mfn.PortItemType.STANDARD
        )
        modelPipe = heatExchanger.modelPipe
        massFlowRateName = _mnames.getMassFlowVariableName(
            self.displayName, modelPipe, modelPipe.fromPort
        )

        outgoingConnection = heatExchanger.port2.getConnection()
        reverseInputTemperatureName = _cnames.getTemperatureVariableName(
            outgoingConnection, _mfn.PortItemType.STANDARD
        )

        inputPos = heatExchanger.relativeInputHeight
        outputPos = heatExchanger.relativeOutputHeight

        outputTemperatureName = _temps.getInternalTemperatureVariableName(
            componentDisplayName=self.displayName, nodeName=modelPipe.name
        )

        loop = self._hydraulicLoops.getLoopForExistingConnection(
            incomingConnection
        )
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
            msgBox = _qtw.QMessageBox()
            msgBox.setText(
                f"{errorConnList} is connected wrongly, right click StorageTank to invert connection."
            )
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
