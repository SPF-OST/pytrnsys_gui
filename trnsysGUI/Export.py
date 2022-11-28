# pylint: skip-file
import dataclasses as _dc
import logging as _log
import typing as _tp

import jinja2 as _jinja

import trnsysGUI.TVentil as _tventil
import trnsysGUI.connection.connectionBase as _cb
import trnsysGUI.connection.doublePipeConnection as _dpc
import trnsysGUI.connection.names as _cnames
import trnsysGUI.connection.singlePipeConnection as _spc
import trnsysGUI.connection.values as _values
import trnsysGUI.hydraulicLoops.model as _hlm
import trnsysGUI.hydraulicLoops.names as _lnames
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.export as _mfse
import trnsysGUI.massFlowSolver.globalNetwork as _gn
import trnsysGUI.massFlowSolver.names as _mnames
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.temperatures as _temps
import trnsysGUI.temperatures.hydraulic as _thyd

_UNUSED_INDEX = 0


@_dc.dataclass
class _SerializedNode:
    name: str
    index: int
    nodeType: int
    neighborIndexes: _tp.Tuple[int, int, int]


class Export:
    def __init__(
        self,
        diagramName: str,
        hasInternalPipings: _tp.Sequence[_ip.HasInternalPiping],
        hydraulicLoops: _tp.Sequence[_hlm.HydraulicLoop],
        fluids: _tp.Sequence[_hlm.Fluid],
        logger: _log.Logger,
        editor,
    ) -> None:
        self._hydraulicLoops = hydraulicLoops
        self._fluids = fluids
        self._diagramName = diagramName
        self._hasInternalPipings = hasInternalPipings
        self.logger = logger
        self._editor = editor

        self.maxChar = 20

        o: _ip.HasInternalPiping
        nodes = [n for c in self._hasInternalPipings for n in c.getInternalPiping().nodes]
        self.lineNumOfPar = len(nodes)

        self.numOfPar = 4 * self.lineNumOfPar + 1

    def exportBlackBox(self, exportTo="ddck"):
        f = "*** Black box component temperatures" + "\n"
        equationNr = 0

        for t in self._hasInternalPipings:
            if not t.shallRenameOutputTemperaturesInHydraulicFile():
                continue

            equations = _thyd.export(t)

            for equation in equations:
                f += equation + "\n"
            equationNr += len(equations)

        if exportTo == "mfs":
            lines = f.split("\n")
            f = ""
            for i in range(len(lines)):
                if "=" in lines[i]:
                    lines[i] = lines[i].split("=")[0] + "=1"
                f += lines[i] + "\n"

        if equationNr == 0:
            f = ""
        else:
            f = "\nEQUATIONS " + str(equationNr) + "\n" + f + "\n"

        problemEncountered = False
        return problemEncountered, f

    def exportDoublePipeParameters(self, exportTo="ddck"):
        doesHydraulicContainDoublePipes = any(
            isinstance(obj, _dpc.DoublePipeConnection) for obj in self._hasInternalPipings
        )

        if not doesHydraulicContainDoublePipes:
            return ""

        constantsBlock = """\
*** Default global PARAMETERS for TYPES 9511 ***
CONSTANTS 25

****** Pipe and soil properties ******
dpLength = 579.404 ! Length of buried pipe in m
dpDiamIn = 0.4028 ! Inner diameter of pipes in m
dpDiamOut = 0.429 ! Outer diameter of pipes in m
dpLambda = 175 ! Thermal conductivity of pipe material, kJ/(h*m*K)
dpDepth = 1.8 ! Buried pipe depth in m
dpDiamCase = 2 ! Diameter of casing material in m
dpLambdaFill = 7  ! Thermal conductivity of fill insulation in kJ/hr.m.K
dpDistPtoP = 0.55  ! Center-to-center pipe spacing in m
dpLambdaGap = 1.44  ! Thermal conductivity of gap material in kJ/hr.m.K (gravel)
dpGapThick = 0  ! Gap thickness in m

****** Fluid properties ******
dpRhoFlu = 1000.0 ! Density of fluid, kg/m^3
dpLambdaFl = LamWat*3.6  ! Thermal conductivity of fluid in kJ/hr.m.K
dpCpFl = 4.19 ! Specific heat of fluid, kJ/kg.K
dpViscFl = 3.078  ! Viscosity of fluid in kg/m.hr

****** Initial conditions ******
dpTIniHot = 15  ! Initial fluid temperature - pipe 1 in degrees celsius
dpTIniCold  = 10  ! Initial fluid temperature - pipe 2 in degrees celsius

****** Soil's thermal properties ******
dpLamdaSl = 8.64  ! Thermal conductivity of soil in kJ/hr.m.K
dpRhoSl = 1800  ! Density of soil in kg/m^3
dpCpSl = 1.0  ! Specific heat of soil in kJ/kg.K

****** Definition of nodes ******
dpNrFlNds = 60  ! Number of fluid nodes
dpNrSlRad = 10  ! Number of radial soil nodes
dpSoilThickness = 0.5  ! Thickness of soil around the gravel considered in the model in m
dpRadNdDist = dpSoilThickness/dpNrSlRad ! Radial distance of any node in m
dpNrSlAx = 20  ! Number of axial soil nodes
dpNrSlCirc = 4  ! Number of circumferential soil nodes
"""
        massFlowSolverConstantsBlock = """\
CONSTANTS 3
TambAvg = 7.96 ! Average surface temperature in degrees celsius
dTambAmpl = 13.32 ! Amplitude of surface temperature in n degrees celsius
ddTcwOffset = 36 ! Days of minimum surface temperature
"""
        if exportTo == "ddck":
            return constantsBlock
        elif exportTo == "mfs":
            return constantsBlock + "\n\n" + massFlowSolverConstantsBlock
        else:
            raise ValueError("Unknown value for `exportTo`", exportTo)

    def exportPumpOutlets(self):
        f = "*** Pump outlet temperatures" + "\n"
        equationNr = 0
        for t in self._hasInternalPipings:
            f += t.exportPumpOutlets()[0]
            equationNr += t.exportPumpOutlets()[1]

        if equationNr == 0:
            f = ""
        else:
            f = "EQUATIONS " + str(equationNr) + "\n" + f + "\n"

        return f

    def exportMassFlows(self):  # What the controller should give
        f = "*** Massflowrates" + "\n"
        equationNr = 0

        for t in self._hasInternalPipings:
            f += t.exportMassFlows()[0]
            equationNr += t.exportMassFlows()[1]

        if equationNr == 0:
            f = ""
        else:
            f = "EQUATIONS " + str(equationNr) + "\n" + f + "\n"

        return f

    def exportDivSetting(self, unit):
        """
        :param unit: the index of the previous unit number used.
        :return:
        """
        f = ""

        nUnit = unit
        constants = 0
        f2 = ""
        for t in self._hasInternalPipings:
            f2 += t.exportDivSetting1()[0]
            constants += t.exportDivSetting1()[1]

        if constants > 0:
            f = "CONSTANTS " + str(constants) + "\n"
            f += f2 + "\n"

        for t in self._hasInternalPipings:
            res = t.exportDivSetting2(nUnit)
            f += res[0]
            nUnit = res[1]

        return f

    def exportParametersFlowSolver(self, simulationUnit: int, simulationType: int, descConnLength: int) -> str:
        hasInternalPipings = []
        for hasInternalPiping in self._hasInternalPipings:
            noHydraulicConnection = (
                not isinstance(hasInternalPiping, _cb.ConnectionBase)
                and not hasInternalPiping.outputs  # type: ignore[attr-defined]
                and not hasInternalPiping.inputs  # type: ignore[attr-defined]
            )

            if noHydraulicConnection:
                continue

            hasInternalPipings.append(hasInternalPiping)

        serializedNodes = self._getSerializedNodes(hasInternalPipings)

        lines = []
        for serializedNode in serializedNodes:
            neighborIndexes = serializedNode.neighborIndexes

            firstColumn = f"{neighborIndexes[0]} {neighborIndexes[1]} {neighborIndexes[2]} {serializedNode.nodeType} "
            secondColumn = f"!{serializedNode.index} : {serializedNode.name}"

            line = f"{firstColumn.ljust(descConnLength)}{secondColumn}"

            lines.append(line)

        jointLines = "\n".join(lines)

        resultText = f"""\
UNIT {simulationUnit} TYPE {simulationType}
PARAMETERS {len(serializedNodes) * 4 + 1}
{len(serializedNodes)}
{jointLines}
"""

        return resultText

    @classmethod
    def _getSerializedNodes(
        cls,
        hasInternalPipings: _tp.Sequence[_ip.HasInternalPiping],
    ) -> _tp.Sequence[_SerializedNode]:
        globalNetwork = _gn.getGlobalNetwork(hasInternalPipings)
        internalPortItemToExternalRealNode = globalNetwork.internalPortItemToExternalNode

        nodesToIndex = {nwp.node: i for i, nwp in enumerate(globalNetwork.nodesWithParent, start=1)}

        serializedNodes = []
        for index, nodeWithParent in enumerate(globalNetwork.nodesWithParent, start=1):
            node = nodeWithParent.node
            parent = nodeWithParent.parent

            neighborsAndUnusedIndexes = cls._getNeighborAndUnusedIndexes(
                node, nodesToIndex, internalPortItemToExternalRealNode
            )

            displayName = parent.getDisplayName()
            nodeNameOrEmpty = node.name or ""
            fullName = f"{displayName}{nodeNameOrEmpty}"
            serializedNode = _SerializedNode(fullName, index, node.getNodeType(), neighborsAndUnusedIndexes)

            serializedNodes.append(serializedNode)

        return serializedNodes

    @staticmethod
    def _getNeighborAndUnusedIndexes(
        realNode: _mfn.Node,
        realNodesToIndex: _tp.Mapping[_mfn.Node, int],
        internalPortItemToExternalRealNode: _tp.Mapping[_mfn.PortItem, _mfn.Node],
    ) -> _tp.Tuple[int, int, int]:
        neighborIndexes = []
        for neighbor in realNode.getPortItems():
            if isinstance(neighbor, _mfn.Node):
                neighborIndex = realNodesToIndex[neighbor]
            elif isinstance(neighbor, _mfn.PortItem):
                externalRealNode = internalPortItemToExternalRealNode[neighbor]
                neighborIndex = realNodesToIndex[externalRealNode]
            else:
                raise AssertionError("Can't get here.")

            neighborIndexes.append(neighborIndex)

        nNeighborIndexes = len(neighborIndexes)

        assert nNeighborIndexes > 0
        neighborAndUnusedIndexes = [neighborIndexes[0], _UNUSED_INDEX, _UNUSED_INDEX]

        if nNeighborIndexes > 1:
            neighborAndUnusedIndexes[1] = neighborIndexes[1]

        if nNeighborIndexes > 2:
            neighborAndUnusedIndexes[2] = neighborIndexes[2]

        return neighborAndUnusedIndexes[0], neighborAndUnusedIndexes[1], neighborAndUnusedIndexes[2]

    def exportInputsFlowSolver(self):
        f = ""
        f += "INPUTS " + str(self.lineNumOfPar) + "! for Type 9351\n"

        numberOfInputs = 0

        counter = 0
        for t in self._hasInternalPipings:
            res = _mfse.exportInputsFlowSolver(t)
            f += res[0]
            counter += res[
                1
            ]  # DC this is a very strange way to print values, I would like to have 10 values per line and the fact that two go together makes it complicated
            numberOfInputs += res[1]

            if counter > 9 or t == self._hasInternalPipings[-1]:
                f += "\n"
                counter = 0

        f += "*** Initial Inputs\n"
        counter = 0
        for _ in range(numberOfInputs):
            f += "0 "
            counter += 1
            # DC if we use 10 per line its way easier to count and see if it is well done.
            # Above should be the same but some elements give two at once and depending if they are at then end of the line 11 values show up
            if counter > 9:
                f += "\n"
                counter = 0

        f += "\n\n"

        return f

    def exportOutputsFlowSolver(self, simulationUnit):
        f = ""

        abc = "ABC"

        prefix = "Mfr"
        equationNumber = 1
        nEqUsed = 1  # DC

        tot = ""

        for t in self._hasInternalPipings:
            noHydraulicConnection = not isinstance(t, _cb.ConnectionBase) and not t.outputs and not t.inputs

            if noHydraulicConnection:
                continue
            else:
                res = _mfse.exportOutputsFlowSolver(t, equationNumber, simulationUnit)
                tot += res[0]
                equationNumber = res[1]
                nEqUsed += res[2]

        head = (
            "EQUATIONS {0}	! Output up to three (A,B,C) mass flow rates of each component, positive = "
            "input/inlet, negative = output/outlet ".format(nEqUsed - 1)
        )

        f += head + "\n"
        f += tot + "\n"
        f += "\n"

        return f

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        # Prints the part of the export where the pipes, tp and div Units are printed

        f = ""
        unitNumber = startingUnit
        # typeNr1 = 929 # Temperature calculation from a tee-piece
        # typeNr2 = 931 # Temperature calculation from a pipe

        for t in self._hasInternalPipings:
            res = t.exportPipeAndTeeTypesForTemp(unitNumber)
            f += res[0]
            unitNumber = res[1]

        self._editor.printerUnitnr = unitNumber

        return f

    def exportSinglePipeEnergyBalanceVariables(self):
        singlePipesWithTrnsysUnits = [
            ip
            for ip in self._hasInternalPipings
            if isinstance(ip, _spc.SinglePipeConnection) and ip.shallCreateTrnsysUnit
        ]

        if not singlePipesWithTrnsysUnits:
            return ""

        convectedFluxes = [sp.getConvectedHeatFluxVariableName() for sp in singlePipesWithTrnsysUnits]
        summedConvectedFluxes = "+".join(convectedFluxes)

        dissipatedFluxes = [sp.getDissipatedHeatFluxVariableName() for sp in singlePipesWithTrnsysUnits]
        summedDissipatedFluxes = "+".join(dissipatedFluxes)

        internalEnergies = [sp.getInternalHeatVariableName() for sp in singlePipesWithTrnsysUnits]
        summedInternalEnergies = "+".join(internalEnergies)

        Totals = _cnames.EnergyBalanceTotals.SinglePipe
        equation = f"""\
*** Single pipe losses
EQUATIONS 1
spPipeEnIntTot = {summedInternalEnergies}

UNIT 100 TYPE 150
PARAMETERS 3
1 ! Number of inputs
1 ! Number of time steps
0 ! Initial value
INPUTS 1
spPipeEnIntTot
**
0

EQUATIONS 4
{Totals.CONVECTED} = {summedConvectedFluxes}
{Totals.DISSIPATED} = {summedDissipatedFluxes}
{Totals.PIPE_INTERNAL_CHANGE} = (spPipeEnIntTot - [100,1]) / dtSim / 3600 ! kW
{Totals.IMBALANCE} = {Totals.CONVECTED} - {Totals.DISSIPATED} - {Totals.PIPE_INTERNAL_CHANGE}
"""
        return equation

    def exportDoublePipeEnergyBalanceVariables(self):
        doublePipes = [ip for ip in self._hasInternalPipings if isinstance(ip, _dpc.DoublePipeConnection)]

        if not doublePipes:
            return ""

        dissipatedHeatFluxesToFarField = []
        convectedHeatFluxes = []
        pipeInternalEnergyChanges = []
        soilInternalEnergyChanges = []
        for doublePipe in doublePipes:
            coldConvectedHeatFlux = doublePipe.getEnergyBalanceVariableName(
                _dpc.EnergyBalanceVariables.CONVECTED, _mfn.PortItemType.COLD
            )
            hotConvectedHeatFlux = doublePipe.getEnergyBalanceVariableName(
                _dpc.EnergyBalanceVariables.CONVECTED, _mfn.PortItemType.HOT
            )
            convectedHeatFluxes.extend([coldConvectedHeatFlux, hotConvectedHeatFlux])

            dissipatedHeatFluxToFarField = doublePipe.getEnergyBalanceVariableName(
                _dpc.EnergyBalanceVariables.SOIL_TO_FAR_FIELD
            )
            dissipatedHeatFluxesToFarField.append(dissipatedHeatFluxToFarField)

            coldPipeInternalEnergyChange = doublePipe.getEnergyBalanceVariableName(
                _dpc.EnergyBalanceVariables.PIPE_INTERNAL_CHANGE, _mfn.PortItemType.COLD
            )
            hotPipeInternalEnergyChange = doublePipe.getEnergyBalanceVariableName(
                _dpc.EnergyBalanceVariables.PIPE_INTERNAL_CHANGE, _mfn.PortItemType.HOT
            )
            pipeInternalEnergyChanges.extend([coldPipeInternalEnergyChange, hotPipeInternalEnergyChange])

            soilInternalEnergyChange = doublePipe.getEnergyBalanceVariableName(
                _dpc.EnergyBalanceVariables.SOIL_INTERNAL_CHANGE
            )
            soilInternalEnergyChanges.append(soilInternalEnergyChange)

        summedConvectedHeatFluxes = " + ".join(convectedHeatFluxes)
        summedDissipationToFarField = " + ".join(dissipatedHeatFluxesToFarField)
        summedPipeInternalEnergyChanges = " + ".join(pipeInternalEnergyChanges)
        summedSoilInternalEnergyChanges = " + ".join(soilInternalEnergyChanges)

        Totals = _cnames.EnergyBalanceTotals.DoublePipe

        equations = f"""\
*** Double pipe energy balance
EQUATIONS 5
{Totals.CONVECTED} = {summedConvectedHeatFluxes}
{Totals.DISSIPATION_TO_FAR_FIELD} = {summedDissipationToFarField}
{Totals.PIPE_INTERNAL_CHANGE} = {summedPipeInternalEnergyChanges}
{Totals.SOIL_INTERNAL_CHANGE} = {summedSoilInternalEnergyChanges}
{Totals.IMBALANCE} = {Totals.CONVECTED} - {Totals.DISSIPATION_TO_FAR_FIELD}  - {Totals.PIPE_INTERNAL_CHANGE} - {Totals.SOIL_INTERNAL_CHANGE}
"""

        return equations

    def exportMassFlowPrinter(self, unitnr, descLen):
        typenr = 25
        printingMode = 0
        relAbsStart = 0
        overwriteApp = -1
        printHeader = -1
        delimiter = 0
        printLabels = 1

        f = "ASSIGN " + self._diagramName.rsplit(".", 1)[0] + "_Mfr.prt " + str(unitnr) + "\n\n"

        f += "UNIT " + str(unitnr) + " TYPE " + str(typenr)
        f += " " * (descLen - len(f)) + "! User defined Printer" + "\n"
        f += "PARAMETERS 10" + "\n"
        f += "dtSim"
        f += " " * (descLen - len(f)) + "! 1 Printing interval" + "\n"
        f += "START"
        f += " " * (descLen - len(f)) + "! 2 Start time" + "\n"
        f += "STOP"
        f += " " * (descLen - len(f)) + "! 3 Stop time" + "\n"
        f += str(unitnr)
        f += " " * (descLen - len(f)) + "! 4 Logical unit" + "\n"
        f += str(printingMode)
        f += " " * (descLen - len(f)) + "! 5 Units printing mode" + "\n"
        f += str(relAbsStart)
        f += " " * (descLen - len(f)) + "! 6 Relative or absolute start time" + "\n"
        f += str(overwriteApp)
        f += " " * (descLen - len(f)) + "! 7 Overwrite or Append" + "\n"
        f += str(printHeader)
        f += " " * (descLen - len(f)) + "! 8 Print header" + "\n"
        f += str(delimiter)
        f += " " * (descLen - len(f)) + "! 9 Delimiter" + "\n"
        f += str(printLabels)
        f += " " * (descLen - len(f)) + "! 10 Print labels" + "\n"
        f += "\n"

        allVariableNames = []
        for hasInternalPiping in self._hasInternalPipings:
            if isinstance(hasInternalPiping, _spc.SinglePipeConnection):
                mfrVariableName = _mnames.getCanonicalMassFlowVariableName(
                    hasInternalPiping, hasInternalPiping.modelPipe
                )
                allVariableNames.append(mfrVariableName)
            elif isinstance(hasInternalPiping, _dpc.DoublePipeConnection):
                coldMfrVariableName = _mnames.getCanonicalMassFlowVariableName(
                    hasInternalPiping, hasInternalPiping.coldModelPipe
                )
                hotMfrVariableName = _mnames.getCanonicalMassFlowVariableName(
                    hasInternalPiping, hasInternalPiping.hotModelPipe
                )
                allVariableNames.extend([coldMfrVariableName, hotMfrVariableName])
            elif isinstance(hasInternalPiping, _tventil.TVentil):
                inputVariableName = _mnames.getInputVariableName(hasInternalPiping, hasInternalPiping.modelDiverter)
                allVariableNames.append(inputVariableName)

        variableNameOctets = [allVariableNames[s : s + 8] for s in range(0, len(allVariableNames), 8)]

        formattedInputVariables = "\n".join(" ".join(o) for o in variableNameOctets) + "\n"

        f += f"""\
INPUTS {len(allVariableNames)}
{formattedInputVariables}
***
{formattedInputVariables}

"""
        return f

    def exportTempPrinter(self, unitnr, descLen):

        typenr = 25
        printingMode = 0
        relAbsStart = 0
        overwriteApp = -1
        printHeader = -1
        delimiter = 0
        printLabels = 1

        f = "ASSIGN " + self._diagramName.rsplit(".", 1)[0] + "_T.prt " + str(unitnr) + "\n\n"

        f += "UNIT " + str(unitnr) + " TYPE " + str(typenr)
        f += " " * (descLen - len(f)) + "! User defined Printer" + "\n"
        f += "PARAMETERS 10" + "\n"
        f += "dtSim"
        f += " " * (descLen - len(f)) + "! 1 Printing interval" + "\n"
        f += "START"
        f += " " * (descLen - len(f)) + "! 2 Start time" + "\n"
        f += "STOP"
        f += " " * (descLen - len(f)) + "! 3 Stop time" + "\n"
        f += str(unitnr)
        f += " " * (descLen - len(f)) + "! 4 Logical unit" + "\n"
        f += str(printingMode)
        f += " " * (descLen - len(f)) + "! 5 Units printing mode" + "\n"
        f += str(relAbsStart)
        f += " " * (descLen - len(f)) + "! 6 Relative or absolute start time" + "\n"
        f += str(overwriteApp)
        f += " " * (descLen - len(f)) + "! 7 Overwrite or Append" + "\n"
        f += str(printHeader)
        f += " " * (descLen - len(f)) + "! 8 Print header" + "\n"
        f += str(delimiter)
        f += " " * (descLen - len(f)) + "! 9 Delimiter" + "\n"
        f += str(printLabels)
        f += " " * (descLen - len(f)) + "! 10 Print labels" + "\n"
        f += "\n"

        allVariableNames = []
        for hasInternalPiping in self._hasInternalPipings:
            if not isinstance(hasInternalPiping, (_spc.SinglePipeConnection, _dpc.DoublePipeConnection)):
                continue

            internalPiping = hasInternalPiping.getInternalPiping()
            nodes = internalPiping.nodes
            temperatureVariableNames = [_temps.getTemperatureVariableName(hasInternalPiping, n) for n in nodes]

            allVariableNames.extend(temperatureVariableNames)

        variableNameOctets = [allVariableNames[s : s + 8] for s in range(0, len(allVariableNames), 8)]

        formattedInputVariables = "\n".join(" ".join(s) for s in variableNameOctets) + "\n"

        f += f"""\
INPUTS {len(allVariableNames)}
{formattedInputVariables}
***
{formattedInputVariables}

"""
        return f

    def exportFluids(self) -> str:
        def getValueOrVariableName(
            valueOrVariable: _tp.Union[float, _hlm.Variable], factor: float = 1
        ) -> _tp.Union[float, str]:
            if isinstance(valueOrVariable, float):
                return valueOrVariable * factor

            if isinstance(valueOrVariable, _hlm.Variable):
                if factor == 1:
                    return valueOrVariable.name

                return f"{valueOrVariable.name}*{factor}"

            raise ValueError(f"Can't deal with type {type(valueOrVariable).__name__}.")

        template = """\
** Fluids:
EQUATIONS {{2 * fluids|length}}
{% for fluid in fluids -%}
** {{fluid.name}}
{% set rho = getValueOrVariableName(fluid.densityInKgPerM3) -%}
{% set cp = getValueOrVariableName(fluid.specificHeatCapacityInJPerKgK, 1e-3) -%}
F{{fluid.name}}Rho = {{rho}} ! [kg/m^3]
F{{fluid.name}}Cp = {{cp}} ! [kJ/(kg*K)]
{% endfor -%}
"""
        fluids = self._fluids
        return self._render(template, fluids=fluids, getValueOrVariableName=getValueOrVariableName)

    def exportHydraulicLoops(self) -> str:
        template = """\
** Hydraulic loops
EQUATIONS {{nEquations}}
{% for hydraulicLoop in loops -%}
{% set loopName = hydraulicLoop.name.value -%}
{% set loopRho = names.getDensityName(loopName) -%}
{% set loopCp = names.getHeatCapacityName(loopName) -%}
{% set fluid = hydraulicLoop.fluid -%}
{% set loopLen = names.getDefaultLengthName(loopName) -%}
{% set loopDia = names.getDefaultDiameterName(loopName) -%}
{% set loopUVal = names.getDefaultUValueName(loopName) -%}
{% set loopNPipes = names.getNumberOfPipesName(loopName) -%}
** {{loopName}}
{% if hydraulicLoop.useLoopWideDefaults -%}
{{loopNPipes}} = {{hydraulicLoop.connections | length}}
{{loopLen}} = {{values.DEFAULT_LENGTH_IN_M}} ! [m]
{{loopDia}} = {{values.DEFAULT_DIAMETER_IN_CM / 100}} ! [m]
{{loopUVal}} = {{values.DEFAULT_U_VALUE_IN_W_PER_M2_K * 60*60/1000}} ! [kJ/(h*m^2*K)] (= {{values.DEFAULT_U_VALUE_IN_W_PER_M2_K}} W/(m^2*K))
{% endif -%}
{{loopRho}} = F{{fluid.name}}Rho
{{loopCp}} = F{{fluid.name}}Cp

{% endfor -%}
"""
        loops = self._hydraulicLoops

        nEquations = sum(6 if l.useLoopWideDefaults else 2 for l in loops)

        return self._render(template, loops=loops, nEquations=nEquations, names=_lnames, values=_values)

    @staticmethod
    def _render(template: str, /, **kwargs):
        compiledTemplate = _jinja.Template(template)
        return compiledTemplate.render(**kwargs)
