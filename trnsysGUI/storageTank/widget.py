import os as _os
import random as _rnd
import shutil as _sh
import typing as _tp
import dataclasses as _dc

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMenu, QMessageBox, QTreeView

from trnsysGUI import idGenerator as _id
import trnsysGUI.images as _img
import trnsysGUI.storageTank.model as _model
import trnsysGUI.storageTank.side as _sd
from trnsysGUI.BlockItem import BlockItem  # type: ignore[attr-defined]
from trnsysGUI.storageTank.ConfigureStorageDialog import ConfigureStorageDialog  # type: ignore[attr-defined]
from trnsysGUI.Connection import Connection  # type: ignore[attr-defined]
from trnsysGUI.HeatExchanger import HeatExchanger  # type: ignore[attr-defined]
from trnsysGUI.MyQFileSystemModel import MyQFileSystemModel  # type: ignore[attr-defined]
from trnsysGUI.MyQTreeView import MyQTreeView  # type: ignore[attr-defined]
from trnsysGUI.PortItem import PortItem  # type: ignore[attr-defined]
from trnsysGUI.directPortPair import DirectPortPair
from trnsysGUI.type1924.createType1924 import Type1924_TesPlugFlow  # type: ignore[attr-defined]

InOut = _tp.Literal["In", "Out"]
_T = _tp.TypeVar("_T", covariant=True)


@_dc.dataclass
class PortIds:
    inputId: int
    outputId: int


class StorageTank(BlockItem):  # pylint: disable=too-many-instance-attributes,too-many-public-methods
    HEAT_EXCHANGER_WIDTH = 40

    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.parent = parent
        self._idGenerator: _id.IdGenerator = self.parent.parent().idGen
        self.dckFilePath = ""

        self.directPortPairs: _tp.List[DirectPortPair] = []

        self.heatExchangers: _tp.List[HeatExchanger] = []

        self.blackBoxEquations = []

        self.nTes = self.parent.parent().idGen.getStoragenTes()
        self.storageType = self.parent.parent().idGen.getStorageType()

        self.changeSize()

        self.path = None
        self._addTree()

    @property
    def leftDirectPortPairsPortItems(self):
        return self._getDirectPortPairPortItems(_sd.Side.LEFT)

    @property
    def rightDirectPortPairsPortItems(self):
        return self._getDirectPortPairPortItems(_sd.Side.RIGHT)

    def _getDirectPortPairPortItems(self, side: _sd.Side):
        return [
            p for dpp in self.directPortPairs if dpp.side == side for p in [dpp.fromPort, dpp.toPort]
        ]

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

        directPortPair = DirectPortPair(
            trnsysId, inputPort, outputPort, relativeInputHeight, relativeOutputHeight, side
        )

        self.directPortPairs.append(directPortPair)
        self.inputs.append(directPortPair.fromPort)
        self.outputs.append(directPortPair.toPort)

    def _createPort(
        self, name: str, relativeHeight: float, storageTankHeight: float, side: _sd.Side
    ) -> PortItem:
        sideNr = side.toSideNr()
        portItem = PortItem(name, sideNr, self)
        portItem.setZValue(100)
        xPos = 0 if side == _sd.Side.LEFT else self.w
        yPos = storageTankHeight - relativeHeight * storageTankHeight
        portItem.setPos(xPos, yPos)
        portItem.side = sideNr
        return portItem

    @staticmethod
    def _setPortColor(portItem: PortItem, color: QColor) -> None:
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

    # Transform related
    def changeSize(self):
        """Resize block function"""
        width = self.w
        height = self.h

        # Limit the block size:
        if height < 20:
            height = 20
        if width < 40:
            width = 40

        # center label:
        rect = self.label.boundingRect()
        labelWidth = rect.width()
        labelXPos = (width - labelWidth) / 2
        self.label.setPos(labelXPos, height)

        return width, height

    def updateImage(self):
        super().updateImage()
        self.label.setPos(self.label.pos().x(), self.h)

    def updatePortItemPositions(self, deltaH, deltaW):
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
            self.groupName,
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
            self.groupName = "defaultGroup"
            self.setBlockToGroup(model.groupName)

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

    def getTemperatureVariableName(self, portItem: PortItem) -> str:
        directPortPair = self._getDirectPortPairForPortItemOrNone(portItem)
        if directPortPair:
            return self._getTemperatureVariableNameForDirectPortPairPortItem(directPortPair, portItem)

        heatExchanger = self._getHeatExchangerForPortItem(portItem)
        if heatExchanger:
            return self._getTemperatureVariableNameForHeatExchangerPortItem(heatExchanger)

        raise ValueError("Port item doesn't belong to this storage tank.")

    def getFlowSolverParametersId(self, portItem: PortItem) -> int:
        directPortPair = self._getDirectPortPairForPortItemOrNone(portItem)
        if directPortPair:
            return directPortPair.trnsysId

        heatExchanger = self._getHeatExchangerForPortItem(portItem)
        if heatExchanger:
            return heatExchanger.trnsysId

        raise ValueError("Port item doesn't belong to this storage tank.")

    def assignIDsToUninitializedValuesAfterJsonFormatMigration(
        self, generator: _id.IdGenerator
    ) -> None:  # type: ignore[attr-defined]
        for heatExchanger in self.heatExchangers:
            if heatExchanger.trnsysId == generator.UNINITIALIZED_ID:
                heatExchanger.trnsysId = generator.getTrnsysID()

        for directPortPair in self.directPortPairs:
            if directPortPair.trnsysId == generator.UNINITIALIZED_ID:
                directPortPair.trnsysId = generator.getTrnsysID()

    def _getHeatExchangerForPortItem(self, portItem: PortItem) -> _tp.Optional[HeatExchanger]:
        heatExchanger = self._getSingleOrNone(hx for hx in self.heatExchangers if portItem in [hx.port1, hx.port2])

        return heatExchanger

    def _getDirectPortPairForPortItemOrNone(self, portItem: PortItem) -> _tp.Optional[DirectPortPair]:
        directPortPair = self._getSingleOrNone(
            dpp for dpp in self.directPortPairs if portItem in [dpp.fromPort, dpp.toPort]
        )

        return directPortPair

    @staticmethod
    def _getSingleOrNone(iterable: _tp.Iterable[_T]) -> _tp.Optional[_T]:
        sequence = list(iterable)

        if not sequence:
            return None

        if len(sequence) > 1:
            raise ValueError("More than one value in iterable.")

        return sequence[0]

    def _getTemperatureVariableNameForDirectPortPairPortItem(self, directPortPair, portItem):
        isInputPort = directPortPair.fromPort == portItem
        relativeHeightInPercent = (
            directPortPair.relativeInputHeightPercent if isInputPort else directPortPair.relativeOutputHeightPercent
        )
        return f"T{self.displayName}Port{directPortPair.side.formatDdck()}{relativeHeightInPercent}"

    @staticmethod
    def _getTemperatureVariableNameForHeatExchangerPortItem(heatExchanger):
        return f"T{heatExchanger.displayName}"

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

    # Export related
    def exportBlackBox(self):
        equations = []
        ddcxPath = _os.path.join(self.path, self.displayName)
        ddcxPath = ddcxPath + ".ddcx"
        self.exportDck()
        if _os.path.isfile(ddcxPath):
            infile = open(ddcxPath, "r")
            lines = infile.readlines()
            for line in lines:
                if line[0] == "T":
                    equations.append(line.replace("\n", ""))
            return "success", equations

        self.logger.warning("No file at " + ddcxPath)
        return "noDdckFile", equations

    def exportParametersFlowSolver(self, descConnLength):
        # The order is important here (has to be the same as in `exportOutputsFlowSolver`):
        # first the direct port pairs, then the heat exchangers
        directPortPairsLines = self._getFlowSolverParametersLinesForDirectPortPairs(self.directPortPairs, descConnLength)

        heatExchangers = self.heatExchangers
        heatExchangersLines = self._getFlowSolverParametersLinesForHeatExchangers(heatExchangers, descConnLength)

        allLines = directPortPairsLines + heatExchangersLines

        result = "\n".join(allLines) + "\n"

        return result

    def _getFlowSolverParametersLinesForHeatExchangers(self, heatExchangers, descConnLength):
        lines = []
        for heatExchanger in heatExchangers:
            incomingConnection: Connection = heatExchanger.port1.connectionList[0]
            outgoingConnection: Connection = heatExchanger.port2.connectionList[0]

            name = self._getMassFlowVariableSuffixForHeatExchanger(heatExchanger)

            line = self._createFlowSolverParametersLine(
                name, heatExchanger.trnsysId, incomingConnection, outgoingConnection, descConnLength
            )

            lines.append(line)
        return lines

    def _getFlowSolverParametersLinesForDirectPortPairs(self, directPortPairs, descConnLength):
        lines = []
        for directPortPair in directPortPairs:
            incomingConnection: Connection = directPortPair.fromPort.connectionList[0]
            outgoingConnection: Connection = directPortPair.toPort.connectionList[0]

            name = self._getMassFlowVariableSuffixForDirectPortPair(directPortPair)

            line = self._createFlowSolverParametersLine(
                name, directPortPair.trnsysId, incomingConnection, outgoingConnection, descConnLength
            )
            lines.append(line)
        return lines

    def _getMassFlowVariableSuffixForDirectPortPair(self, directPortPair: DirectPortPair):
        return (
            f"{self.displayName}Dp{'L' if directPortPair.side.isLeft else 'R'}"
            f"{directPortPair.relativeInputHeightPercent}-{directPortPair.relativeOutputHeightPercent}"
        )

    @staticmethod
    def _getMassFlowVariableSuffixForHeatExchanger(heatExchanger):
        return heatExchanger.displayName

    @staticmethod
    def _createFlowSolverParametersLine(
        name: str, trnsysId: int, incomingConnection: Connection, outgoingConnection: Connection, parametersPartLength
    ) -> str:
        parametersPart = f"{incomingConnection.trnsysId} {outgoingConnection.trnsysId} 0 0"

        currentParametersPart = len(parametersPart)
        if currentParametersPart < parametersPartLength:
            padding = " " * (parametersPartLength - currentParametersPart)
            parametersPart += padding

        line = f"{parametersPart}!{trnsysId} : {name}"

        return line

    def exportInputsFlowSolver1(self):
        return self._getInputs("0,0")

    def exportInputsFlowSolver2(self):
        return self._getInputs("-1")

    def _getInputs(self, inputsValue):
        heatExchangerInputs = [inputsValue for _ in self.heatExchangers]
        directPortPairInputs = [inputsValue for _ in self.directPortPairs]
        allInputs = heatExchangerInputs + directPortPairInputs
        allInputsJoined = " ".join(allInputs) + " "
        return allInputsJoined, len(allInputs)

    def exportOutputsFlowSolver(self, prefix, abc, equationNumber, simulationUnit):
        nextEquationNumber = equationNumber

        # The order is important here (has to be the same as in `exportParametersFlowSolver`):
        # first the direct port pairs, then the heat exchangers
        directPortPairsEquations, nextEquationNumber = self._getFlowSolverOutputEquationsForDirectPortPairs(
            abc, self.directPortPairs, nextEquationNumber, prefix, simulationUnit
        )
        heatExchangersEquations, nextEquationNumber = self._getFlowSolverOutputEquationsForHeatExchangers(
            abc, self.heatExchangers, nextEquationNumber, prefix, simulationUnit
        )

        allEquations = directPortPairsEquations + heatExchangersEquations
        self.exportEquations.extend(allEquations)

        equationsJoined = "".join(allEquations)
        nEquationsUsed = len(allEquations)

        return equationsJoined, nextEquationNumber, nEquationsUsed

    def _getFlowSolverOutputEquationsForHeatExchangers(
        self, abc, heatExchangers, nextEquationNumber, prefix, simulationUnit
    ):
        heatExchangerLines = []
        for heatExchanger in heatExchangers:
            suffix = self._getMassFlowVariableSuffixForHeatExchanger(heatExchanger)

            equation1 = self._createFlowSolverOutputEquation(suffix, abc[0], prefix, nextEquationNumber, simulationUnit)
            equation2 = self._createFlowSolverOutputEquation(
                suffix, abc[1], prefix, nextEquationNumber + 1, simulationUnit
            )
            heatExchangerLines.append(equation1)
            heatExchangerLines.append(equation2)
            nextEquationNumber += 3
        return heatExchangerLines, nextEquationNumber

    def _getFlowSolverOutputEquationsForDirectPortPairs(
        self, abc, directPortPairs, nextEquationNumber, prefix, simulationUnit
    ):
        equations = []
        for directPortPair in directPortPairs:
            suffix = self._getMassFlowVariableSuffixForDirectPortPair(directPortPair)

            equation1 = self._createFlowSolverOutputEquation(suffix, abc[0], prefix, nextEquationNumber, simulationUnit)
            equation2 = self._createFlowSolverOutputEquation(
                suffix, abc[1], prefix, nextEquationNumber + 1, simulationUnit
            )
            equations.append(equation1)
            equations.append(equation2)
            nextEquationNumber += 3
        return equations, nextEquationNumber

    @staticmethod
    def _createFlowSolverOutputEquation(name, alphabeticPortIndex, prefix, equationNumber, simulationUnit):
        return f"{prefix}{name}_{alphabeticPortIndex}=[{simulationUnit},{equationNumber}]\n"

    def exportDck(self):  # pylint: disable=too-many-locals,too-many-statements

        if not self._checkConnExists():
            msgb = QMessageBox()
            msgb.setText("Please connect all ports before exporting!")
            msgb.exec_()
            return
        noError = self._debugConn()

        if not noError:
            qmb = QMessageBox()
            qmb.setText("Ignore connection errors and continue with export?")
            qmb.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
            qmb.setDefaultButton(QMessageBox.Cancel)
            ret = qmb.exec()
            if ret == QMessageBox.Save:
                self.logger.debug("Overwriting")
                # continue
            else:
                self.logger.debug("Canceling")
                return

        nPorts = len(self.directPortPairs)
        nHx = len(self.heatExchangers)

        self.logger.debug("Storage Type: " + str(self.storageType))
        self.logger.debug("nTes: " + str(self.nTes))
        self.logger.debug("nPorts: " + str(nPorts))
        self.logger.debug("nHx: " + str(nHx))

        tool = Type1924_TesPlugFlow()

        inputs = {
            "nUnit": 50,
            "nType": self.storageType,
            "nTes": self.nTes,
            "nPorts": nPorts,
            "nHx": nHx,
            "nHeatSources": 1,
        }

        directPairsPorts = []
        for directPortPair in self.directPortPairs:
            incomingConnection = directPortPair.fromPort.connectionList[0]
            temperatureName = "T" + incomingConnection.displayName
            massFlowRateName = "Mfr" + incomingConnection.displayName

            outgoingConnection = directPortPair.toPort.connectionList[0]
            reverseTemperatureName = "T" + outgoingConnection.displayName

            inputPos = directPortPair.relativeInputHeight
            outputPos = directPortPair.relativeOutputHeight

            directPairsPort = {
                "T": temperatureName,
                "side": directPortPair.side.formatDdck(),
                "Mfr": massFlowRateName,
                "Trev": reverseTemperatureName,
                "zIn": inputPos,
                "zOut": outputPos,
            }
            directPairsPorts.append(directPairsPort)

        heatExchangerPorts = []
        for heatExchanger in self.heatExchangers:
            heatExchangerName = heatExchanger.displayName
            incomingConnection = heatExchanger.port1.connectionList[0]
            temperatureName = "T" + incomingConnection.displayName
            massFlowRateName = "Mfr" + incomingConnection.displayName

            outgoingConnection = heatExchanger.port2.connectionList[0]
            reverseTemperatureName = "T" + outgoingConnection.displayName

            inputPos = heatExchanger.relativeInputHeight
            outputPos = heatExchanger.relativeOutputHeight

            heatExchangerPort = {
                "Name": heatExchangerName,
                "T": temperatureName,
                "Mfr": massFlowRateName,
                "Trev": reverseTemperatureName,
                "zIn": inputPos,
                "zOut": outputPos,
                "cp": "cpwat",
                "rho": "rhowat",
            }

            heatExchangerPorts.append(heatExchangerPort)

        auxiliaryPorts = []
        for _ in range(inputs["nHeatSources"]):
            dictInputAux = {"zAux": 0.0, "qAux": 0.0}
            auxiliaryPorts.append(dictInputAux)

        exportPath = _os.path.join(self.path, self.displayName + ".ddck")
        self.logger.debug(exportPath)

        tool.setInputs(inputs, directPairsPorts, heatExchangerPorts, auxiliaryPorts)

        tool.createDDck(self.path, self.displayName, typeFile="ddck")

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
            msgBox.setText("%s is connected wrongly, right click StorageTank to invert connection." % (errorConnList))
            msgBox.exec()
            noError = False
        else:
            noError = True

        return noError

    def _checkConnExists(self):
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

    def _addTree(self):
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
        self.tree.setObjectName("%sTree" % self.displayName)
        # for i in range(1, self.model.columnCount()-1):
        #     self.tree.hideColumn(i)
        self.tree.setMinimumHeight(200)
        self.tree.setSortingEnabled(True)
        self.parent.parent().splitter.addWidget(self.tree)

    def updateTreePath(self, path):
        """
        When the user chooses the project path for the file explorers, this method is called
        to update the root path.
        """
        pathName = self.displayName
        self.path = _os.path.join(path, "../ddck", pathName)
        if not _os.path.exists(self.path):
            _os.makedirs(self.path)
        self.model.setRootPath(self.path)
        self.tree.setRootIndex(self.model.index(self.path))

    def deleteBlock(self):
        """
        Overridden method to also delete folder
        """
        self.logger.debug("Block " + str(self) + " is deleting itself (" + self.displayName + ")")
        self.deleteConns()
        # self.logger.debug("self.parent.parent" + str(self.parent.parent()))
        self.parent.parent().trnsysObj.remove(self)
        self.logger.debug("deleting block " + str(self) + self.displayName)
        # self.logger.debug("self.scene is" + str(self.parent.scene()))
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

    def setName(self, newName):
        """
        Overridden method to also change folder name
        """
        self.displayName = newName
        self.label.setPlainText(newName)
        self.model.setName(self.displayName)
        self.tree.setObjectName("%sTree" % self.displayName)
        self.logger.debug(_os.path.dirname(self.path))
        destPath = _os.path.join(_os.path.split(self.path)[0], self.displayName)
        if _os.path.split(self.path)[-1] == "" or _os.path.split(self.path)[-1] == "ddck":
            _os.makedirs(destPath)
        else:
            if _os.path.exists(self.path):
                _os.rename(self.path, destPath)
        self.path = destPath
        self.logger.debug(self.path)
