# pylint: skip-file
# type: ignore

import os as _os
import random as _rnd
import shutil as _sh
import typing as _tp

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMenu, QMessageBox, QTreeView

import trnsysGUI.images as _img
import trnsysGUI.storageTank.model as _model
import trnsysGUI.IdGenerator as _id
from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.ConfigureStorageDialog import ConfigureStorageDialog
from trnsysGUI.Connection import Connection
from trnsysGUI.HeatExchanger import HeatExchanger
from trnsysGUI.MyQFileSystemModel import MyQFileSystemModel
from trnsysGUI.MyQTreeView import MyQTreeView
from trnsysGUI.PortItem import PortItem
import trnsysGUI.side as _sd
from trnsysGUI.directPortPair import DirectPortPair
from trnsysGUI.type1924.createType1924 import Type1924_TesPlugFlow

InOut = _tp.Literal["In", "Out"]
_T = _tp.TypeVar("_T", covariant=True)


class StorageTank(BlockItem):
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
        self.addTree()

    @property
    def leftDirectPortPairsPortItems(self):
        return self._getDirectPortPairPortItems(isOnLeftSide=True)

    @property
    def rightDirectPortPairsPortItems(self):
        return self._getDirectPortPairPortItems(isOnLeftSide=False)

    def _getDirectPortPairPortItems(self, isOnLeftSide: bool):
        return [
            p
            for dpp in self.directPortPairs
            if dpp.isOnLeftSide == isOnLeftSide
            for p in [dpp.fromPort, dpp.toPort]
        ]

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.STORAGE_TANK_SVG

    # Setter functions
    def setParent(self, p):
        self.logger.debug("Setting parent of Storage Tank (and its hx)")
        self.parent = p

        if self not in self.parent.parent().trnsysObj:
            self.parent.parent().trnsysObj.append(self)

        # TODO: Should hx be also in trnsysObj?
        for hx in self.heatExchangers:
            hx.parent = self

    def addDirectPortPair(
        self,
        isOnLeftSide,
        relativeInputHeight,
        relativeOutputHeight,
        storageTankHeight,
        **kwargs,
    ):
        sideNr = 0 if isOnLeftSide else 2

        port1 = PortItem("i", sideNr, self)
        port1.setZValue(100)

        port2 = PortItem("o", sideNr, self)
        port2.setZValue(100)

        x = 0 if isOnLeftSide else self.w
        inputY = storageTankHeight - relativeInputHeight * storageTankHeight
        outputY = storageTankHeight - relativeOutputHeight * storageTankHeight

        port1.setPos(x, inputY)
        port2.setPos(x, outputY)

        side = 0 if isOnLeftSide else 2
        port1.side = side
        port2.side = side

        randomInt = int(_rnd.uniform(20, 200))
        randomColor = QColor(randomInt, randomInt, randomInt)

        port1.innerCircle.setBrush(randomColor)
        port2.innerCircle.setBrush(randomColor)
        port1.visibleColor = randomColor
        port2.visibleColor = randomColor

        directPortPair = self._createDirectPortPair(
            self._idGenerator.getTrnsysID(),
            isOnLeftSide,
            port1,
            port2,
            relativeInputHeight,
            relativeOutputHeight,
            kwargs,
        )

        self.directPortPairs.append(directPortPair)
        self.inputs.append(directPortPair.fromPort)
        self.outputs.append(directPortPair.toPort)

    @staticmethod
    def _createDirectPortPair(
        trnsysId,
        isOnLeftSide,
        port1,
        port2,
        relativeInputHeight,
        relativeOutputHeight,
        kwargs,
    ):
        # Misuse of kwargs for detecting if the manual port pair is being loaded and not newly created
        if not kwargs:
            directPortPair = DirectPortPair(
                trnsysId,
                port1,
                port2,
                relativeInputHeight,
                relativeOutputHeight,
                isOnLeftSide
            )
            return directPortPair

        port1.id = kwargs["fromPortId"]
        port2.id = kwargs["toPortId"]

        directPortPair = DirectPortPair(
            trnsysId,
            port1,
            port2,
            relativeInputHeight,
            relativeOutputHeight,
            isOnLeftSide
        )

        return directPortPair

    def addHeatExchanger(self, name, side, relativeInputHeight, relativeOutputHeight):
        heatExchanger = HeatExchanger(
            sideNr=0 if side == _sd.Side.LEFT else 2,
            width=self.HEAT_EXCHANGER_WIDTH,
            relativeInputHeight=relativeInputHeight,
            relativeOutputHeight=relativeOutputHeight,
            storageTankWidth=self.w,
            storageTankHeight=self.h,
            parent=self,
            name=name
        )
        return heatExchanger

    # Transform related
    def changeSize(self):
        """ Resize block function """
        w = self.w
        h = self.h

        # Limit the block size:
        if h < 20:
            h = 20
        if w < 40:
            w = 40

        # center label:
        rect = self.label.boundingRect()
        lw, lh = rect.width(), rect.height()
        lx = (w - lw) / 2
        self.label.setPos(lx, h)

        return w, h

    def updateImage(self):
        super().updateImage()
        self.label.setPos(self.label.pos().x(), self.h)

    def updatePortItemPositions(self, deltaH, deltaW):
        for p in self.inputs + self.outputs:
            rel_h_old = p.pos().y() / self.h
            if p.side == 0:
                p.setPos(p.pos().x(), rel_h_old * (self.h + deltaH))
            else:
                p.setPos(p.pos().x() + deltaW, rel_h_old * (self.h + deltaH))

    def updateHeatExchangersAfterTankSizeChange(self):
        for hx in self.heatExchangers:
            hx.setTankSize(self.w, self.h)

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
            portPairModels
        )

        dictName = "Block-"
        return dictName, storageTankModel.to_dict()

    def _getDirectPortPairModelsForEncode(self):
        portPairModels = []
        for directPort in self.directPortPairs:
            side = _model.Side.createFromSideNr(directPort.fromPort.side)

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
            side = _model.Side.createFromSideNr(heatExchanger.sSide)

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
                self.id,
                heatExchanger.id
            )

            heatExchangerModels.append(heatExchangerModel)

        return heatExchangerModels

    def decode(self, i, resBlockList):
        offset_x = 0
        offset_y = 0
        self._decodeInternal(
            i, offset_x, offset_y, resBlockList, shallSetNamesAndIDs=True
        )

    def _decodeInternal(
        self,
        i,
        offset_x,
        offset_y,
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

        self.setPos(model.position[0] + offset_x, model.position[1] + offset_y)

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

        self.addDirectPortPair(
            isOnLeftSide=portPair.side == _model.Side.LEFT,
            relativeInputHeight=portPair.inputPort.relativeHeight,
            relativeOutputHeight=portPair.outputPort.relativeHeight,
            storageTankHeight=self.h,
            fromPortId=portPair.inputPort.id,
            toPortId=portPair.outputPort.id,
            loadedConn=True,
        )

    def _decodeHeatExchanger(
        self, heatExchangerModel: _model.HeatExchanger, shallSetNamesAndIDs: bool
    ):
        portPair = heatExchangerModel.portPair

        sideNr = portPair.side.toSideNr()

        nameSuffix = "" if shallSetNamesAndIDs else "New"
        name = heatExchangerModel.name + nameSuffix

        heatExchanger = HeatExchanger(
            sideNr,
            heatExchangerModel.width,
            portPair.inputPort.relativeHeight,
            portPair.outputPort.relativeHeight,
            self.w,
            self.h,
            self,
            name
        )

        if shallSetNamesAndIDs:
            heatExchanger.setId(heatExchangerModel.id)

        heatExchanger.port1.id = portPair.inputPort.id
        heatExchanger.port2.id = portPair.outputPort.id

    def decodePaste(self, i, offset_x, offset_y, resConnList, resBlockList, **kwargs):
        self._decodeInternal(
            i, offset_x, offset_y, resBlockList, resConnList, shallSetNamesAndIDs=False
        )

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

    def assignIDsToUninitializedValuesAfterJsonFormatMigration(self, generator: _id.IdGenerator) -> None:
        for heatExchanger in self.heatExchangers:
            if heatExchanger.trnsysId == generator.UNINITIALIZED_ID:
                heatExchanger.trnsysId = generator.getTrnsysID()

        for directPortPair in self.directPortPairs:
            if directPortPair.trnsysId == generator.UNINITIALIZED_ID:
                directPortPair.trnsysId = generator.getTrnsysID()

    def _getHeatExchangerForPortItem(self, portItem: PortItem) -> _tp.Optional[HeatExchanger]:
        heatExchanger = self._getSingleOrNone(
            hx for hx in self.heatExchangers if hx.port1 == portItem or hx.port2 == portItem
        )

        return heatExchanger

    def _getDirectPortPairForPortItemOrNone(self, portItem: PortItem) -> _tp.Optional[DirectPortPair]:
        directPortPair = self._getSingleOrNone(
            dpp for dpp in self.directPortPairs if dpp.fromPort == portItem or dpp.toPort == portItem
        )

        return directPortPair

    @staticmethod
    def _getSingleOrNone(iterable: _tp.Iterable[_T]) -> _T:
        sequence = list(iterable)

        if not sequence:
            return None

        if len(sequence) > 1:
            raise ValueError("More than one value in iterable.")

        return sequence[0]

    def _getTemperatureVariableNameForDirectPortPairPortItem(self, directPortPair, portItem):
        isInputPort = directPortPair.fromPort == portItem
        relativeHeightInPercent = (
            directPortPair.relativeInputHeightPercent
            if isInputPort
            else directPortPair.relativeOutputHeightPercent
        )
        return f"T{self.displayName}Port{directPortPair.side}{relativeHeightInPercent}"

    @staticmethod
    def _getTemperatureVariableNameForHeatExchangerPortItem(heatExchanger):
        return f"T{heatExchanger.displayName}"

    # Debug
    def dumpBlockInfo(self):
        self.logger.debug("storage input list " + str(self.inputs))
        self.logger.debug("storage outputs list " + str(self.outputs))
        self.logger.debug("storage leftside " + str(self.leftDirectPortPairsPortItems))
        self.logger.debug(
            "storage rightside " + str(self.rightDirectPortPairsPortItems)
        )
        self.parent.parent().dumpInformation()

    # Misc
    def contextMenuEvent(self, event):
        menu = QMenu()

        a1 = menu.addAction("Launch NotePad++")
        a1.triggered.connect(self.launchNotepadFile)

        rr = _img.ROTATE_TO_RIGHT_PNG.icon()
        a2 = menu.addAction(rr, "Rotate Block clockwise")
        a2.triggered.connect(self.rotateBlockCW)

        ll = _img.ROTATE_LEFT_PNG.icon()
        a3 = menu.addAction(ll, "Rotate Block counter-clockwise")
        a3.triggered.connect(self.rotateBlockCCW)

        a4 = menu.addAction("Reset Rotation")
        a4.triggered.connect(self.resetRotation)

        b1 = menu.addAction("Print Rotation")
        b1.triggered.connect(self.printRotation)

        c1 = menu.addAction("Delete this Block")
        c1.triggered.connect(self.deleteBlockCom)

        e3 = menu.addAction("Export ddck")
        e3.triggered.connect(self.exportDck)

        menu.exec_(event.screenPos())

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
        else:
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
                name,
                heatExchanger.trnsysId,
                incomingConnection,
                outgoingConnection,
                descConnLength
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
        return (f"{self.displayName}Dp{'L' if directPortPair.isOnLeftSide else 'R'}"
                f"{directPortPair.relativeInputHeightPercent}-{directPortPair.relativeOutputHeightPercent}")

    @staticmethod
    def _getMassFlowVariableSuffixForHeatExchanger(heatExchanger):
        return heatExchanger.displayName

    @staticmethod
    def _createFlowSolverParametersLine(
            name: str,
            trnsysId: int,
            incomingConnection: Connection,
            outgoingConnection: Connection,
            parametersPartLength) -> str:
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

        equationsJoined = "\n".join(allEquations) + "\n"
        nEquationsUsed = len(allEquations)

        return equationsJoined, nextEquationNumber, nEquationsUsed

    def _getFlowSolverOutputEquationsForHeatExchangers(self, abc, heatExchangers, nextEquationNumber, prefix, simulationUnit):
        heatExchangerLines = []
        for heatExchanger in heatExchangers:
            suffix = self._getMassFlowVariableSuffixForHeatExchanger(heatExchanger)

            equation1 = self._createFlowSolverOutputEquation(suffix, abc[0], prefix, nextEquationNumber, simulationUnit)
            equation2 = self._createFlowSolverOutputEquation(suffix, abc[1], prefix, nextEquationNumber + 1, simulationUnit)
            heatExchangerLines.append(equation1)
            heatExchangerLines.append(equation2)
            nextEquationNumber += 3
        return heatExchangerLines, nextEquationNumber

    def _getFlowSolverOutputEquationsForDirectPortPairs(self, abc, directPortPairs, nextEquationNumber, prefix, simulationUnit):
        equations = []
        for directPortPair in directPortPairs:
            suffix = self._getMassFlowVariableSuffixForDirectPortPair(directPortPair)

            equation1 = self._createFlowSolverOutputEquation(suffix, abc[0], prefix, nextEquationNumber, simulationUnit)
            equation2 = self._createFlowSolverOutputEquation(suffix, abc[1], prefix, nextEquationNumber + 1, simulationUnit)
            equations.append(equation1)
            equations.append(equation2)
            nextEquationNumber += 3
        return equations, nextEquationNumber

    def _createFlowSolverOutputEquation(self, name, x, prefix, equationNumber, simulationUnit):
        return f"{prefix}{name}_{x}=[{simulationUnit},{equationNumber}]\n"

    def exportDck(self):

        if not self.checkConnExists():
            msgb = QMessageBox()
            msgb.setText("Please connect all ports before exporting!")
            msgb.exec_()
            return
        noError = self.debugConn()

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
            Tname = "T" + incomingConnection.displayName
            side = directPortPair.side
            Mfrname = "Mfr" + incomingConnection.displayName

            outgoingConnection = directPortPair.toPort.connectionList[0]
            Trev = "T" + outgoingConnection.displayName

            inputPos = directPortPair.relativeInputHeight
            outputPos = directPortPair.relativeOutputHeight

            directPairsPort = {
                "T": Tname,
                "side": side,
                "Mfr": Mfrname,
                "Trev": Trev,
                "zIn": inputPos,
                "zOut": outputPos,
            }
            directPairsPorts.append(directPairsPort)

        heatExchangerPorts = []
        for heatExchanger in self.heatExchangers:
            HxName = heatExchanger.displayName
            incomingConnection = heatExchanger.port1.connectionList[0]
            Tname = "T" + incomingConnection.displayName
            Mfrname = "Mfr" + incomingConnection.displayName

            outgoingConnection = heatExchanger.port2.connectionList[0]
            Trev = "T" + outgoingConnection.displayName

            inputPos = heatExchanger.relativeInputHeight
            outputPos = heatExchanger.relativeOutputHeight

            heatExchangerPort = {
                "Name": HxName,
                "T": Tname,
                "Mfr": Mfrname,
                "Trev": Trev,
                "zIn": inputPos,
                "zOut": outputPos,
                "cp": "cpwat",
                "rho": "rhowat",
            }

            heatExchangerPorts.append(heatExchangerPort)

        auxiliaryPorts = []
        for i in range(inputs["nHeatSources"]):
            dictInputAux = {"zAux": 0.0, "qAux": 0.0}
            auxiliaryPorts.append(dictInputAux)

        exportPath = _os.path.join(self.path, self.displayName + ".ddck")
        self.logger.debug(exportPath)

        tool.setInputs(inputs, directPairsPorts, heatExchangerPorts, auxiliaryPorts)

        tool.createDDck(self.path, self.displayName, typeFile="ddck")
        self.loadedTo = self.path

    def debugConn(self):
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
            msgBox.setText(
                "%s is connected wrongly, right click StorageTank to invert connection."
                % (errorConnList)
            )
            msgBox.exec()
            noError = False
        else:
            noError = True

        return noError

    def checkConnExists(self):
        for hx in self.heatExchangers:
            if not hx.port1.connectionList:
                return False
            if not hx.port2.connectionList:
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
        self.logger.debug(self.parent.parent())
        pathName = self.displayName
        if self.parent.parent().projectPath == "":
            # self.path = os.path.dirname(__file__)
            # self.path = os.path.join(self.path, 'default')
            self.path = self.parent.parent().projectFolder
            # now = datetime.now()
            # self.fileName = now.strftime("%Y%m%d%H%M%S")
            # self.path = os.path.join(self.path, self.fileName)
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
        self.path = _os.path.join(path, "ddck")
        self.path = _os.path.join(self.path, pathName)
        if not _os.path.exists(self.path):
            _os.makedirs(self.path)
        self.model.setRootPath(self.path)
        self.tree.setRootIndex(self.model.index(self.path))

    def deleteBlock(self):
        """
        Overridden method to also delete folder
        """
        self.logger.debug(
            "Block " + str(self) + " is deleting itself (" + self.displayName + ")"
        )
        self.deleteConns()
        # self.logger.debug("self.parent.parent" + str(self.parent.parent()))
        self.parent.parent().trnsysObj.remove(self)
        self.logger.debug("deleting block " + str(self) + self.displayName)
        # self.logger.debug("self.scene is" + str(self.parent.scene()))
        self.parent.scene().removeItem(self)
        widgetToRemove = self.parent.parent().findChild(
            QTreeView, self.displayName + "Tree"
        )
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
