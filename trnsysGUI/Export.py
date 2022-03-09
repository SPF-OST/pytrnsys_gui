# pylint: skip-file
import re
import typing as _tp

from PyQt5.QtWidgets import QMessageBox

from trnsysGUI import massFlowSolver as _mfs
from trnsysGUI.connection.connectionBase import ConnectionBase  # type: ignore[attr-defined]
from trnsysGUI.TVentil import TVentil  # type: ignore[attr-defined]
from trnsysGUI.connection.doublePipeConnection import DoublePipeConnection
from trnsysGUI.connection.singlePipeConnection import SinglePipeConnection  # type: ignore[attr-defined]
import trnsysGUI.hydraulicLoops.names as _names
import trnsysGUI.hydraulicLoops.model as _hlm

import jinja2 as _jinja


class Export(object):
    def __init__(self, massFlowContributors: _tp.Sequence[_mfs.MassFlowNetworkContributorMixin], editor):
        self.logger = editor.logger

        self._massFlowContributors = massFlowContributors
        self.editor = editor
        self.maxChar = 20

        o: _mfs.MassFlowNetworkContributorMixin
        nodes = [n for o in self._massFlowContributors for n in o.getInternalPiping().openLoopsStartingNodes]
        self.lineNumOfPar = len(nodes)

        self.numOfPar = 4 * self.lineNumOfPar + 1

    def exportBlackBox(self, exportTo="ddck"):
        f = "*** Black box component temperatures" + "\n"
        equationNr = 0
        problemEncountered = False

        for t in self._massFlowContributors:
            status, equations = t.exportBlackBox()

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

        return problemEncountered, f

    def exportDoublePipeParameters(self, exportTo="ddck"):
        doesHydraulicContainDoublePipes = any([isinstance(obj, DoublePipeConnection) for obj in self._massFlowContributors])

        if not doesHydraulicContainDoublePipes:
            return ""

        commentStars = 6 * "*"

        if exportTo == "ddck":
            exportText = "CONSTANTS 25\n"
        elif exportTo == "mfs":
            exportText = "CONSTANTS 28\n"
        else:
            raise ValueError("Unknown value for `exportTo`", exportTo)

        exportText += "*** Default global PARAMETERS for TYPES 9511" + "\n"

        exportText += commentStars + " pipe and soil properties " + commentStars + "\n"
        exportText += self._addComment("dpLength = 24.384", "! Length of buried pipe, m")
        exportText += self._addComment("dpDiamIn = 0.02618", "! Inner diameter of pipes, m")
        exportText += self._addComment("dpDiamOut = 0.03198", "! Outer diameter of pipes, m")
        exportText += self._addComment("dpLambda = 1.37067", "! Thermal conductivity of pipe material, kJ/(h*m*K)")
        exportText += self._addComment("dpDepth = 3.0", "! Buried pipe depth, m")
        exportText += self._addComment("dpFlowMode = 1", "! Direction of second pipe flow: 1 = same, 2 = opposite")
        exportText += self._addComment("dpDiamCase = 0.17526", "! Diameter of casing material, m")
        exportText += self._addComment("dpLambdaFill = 0.14537", "! Thermal conductivity of fill insulation, kJ/(h*m*K)")
        exportText += self._addComment("dpDistPtoP = 0.06911", "! Center-to-center pipe spacing, m")
        exportText += self._addComment("dpLambdaGap = 8.722", "! Thermal conductivity of gap material, kJ/(h*m*K)")
        exportText += self._addComment("dpGapThick = 0.0000", "! Gap thickness, m")

        exportText += commentStars + " fluid properties " + commentStars + "\n"
        exportText += self._addComment("dpRhoFlu = 1000.0", "! Density of fluid, kg/m^3")
        exportText += self._addComment("dpLambdaFl = 2.2068", "! Thermal conductivity of fluid, kJ/(h*m*K)")
        exportText += self._addComment("dpCpFl = 4.19", "! Specific heat of fluid, kJ/(kg*K)")
        exportText += self._addComment("dpViscFl = 3.078", "! Viscosity of fluid, kg/(m*h)")

        exportText += commentStars + " initial conditions " + commentStars + "\n"
        exportText += self._addComment("dpTIniHot = 10.0", "! Initial fluid temperature - Pipe hot, deg C")
        exportText += self._addComment("dpTIniCold = 10.0", "! Initial fluid temperature - Pipe cold, deg C")

        exportText += commentStars + " thermal properties soil " + commentStars + "\n"
        exportText += self._addComment("dpLamdaSl = 8.722", "! Thermal conductivity of soil, kJ/(h*m*K)")
        exportText += self._addComment("dpRhoSl = 2500.0", "! Density of soil, kg/m^3")
        exportText += self._addComment("dpCpSl = 0.84", "! Specific heat of soil, kJ/(kg*K)")

        if exportTo == "mfs":
            exportText += commentStars + " general temperature dependency (dependent on weather data) " + commentStars + "\n"
            exportText += self._addComment("TambAvg = 7.96", "! Average surface temperature, deg C")
            exportText += self._addComment("dTambAmpl = 13.32", "! Amplitude of surface temperature, deg C")
            exportText += self._addComment("ddTcwOffset = 36", "! Days of minimum surface temperature")

        exportText += commentStars + " definition of nodes " + commentStars + "\n"
        exportText += self._addComment("dpNrFlNds = 100", "! Number of fluid nodes")
        exportText += self._addComment("dpNrSlRad = 8", "! Number of radial soil nodes")
        exportText += self._addComment("dpNrSlAx = 10", "! Number of axial soil nodes")
        exportText += self._addComment("dpNrSlCirc = 4", "! Number of circumferential soil nodes")
        exportText += self._addComment("dpRadNdDist = 0.0254", "! Radial distance of any node, m")

        exportText += "\n"

        return exportText

    def exportPumpOutlets(self):
        f = "*** Pump outlet temperatures" + "\n"
        equationNr = 0
        for t in self._massFlowContributors:
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

        for t in self._massFlowContributors:
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
        for t in self._massFlowContributors:
            f2 += t.exportDivSetting1()[0]
            constants += t.exportDivSetting1()[1]

        if constants > 0:
            f = "CONSTANTS " + str(constants) + "\n"
            f += f2 + "\n"

        for t in self._massFlowContributors:
            res = t.exportDivSetting2(nUnit)
            f += res[0]
            nUnit = res[1]

        return f

    def exportParametersFlowSolver(self, simulationUnit, simulationType, descConnLength):
        # If not all ports of an object are connected, less than 4 numbers will show up
        f = ""
        f += "UNIT " + str(simulationUnit) + " TYPE " + str(simulationType) + "\n"
        f += "PARAMETERS " + str(self.numOfPar) + "\n"
        f += str(self.lineNumOfPar) + "\n"

        nameString = ""
        for t in self._massFlowContributors:

            noHydraulicConnection = not isinstance(t, ConnectionBase) and not t.outputs and not t.inputs

            if noHydraulicConnection:
                continue
            else:
                ObjToCheck = t.exportParametersFlowSolver(descConnLength)
                f += ObjToCheck
                ObjToCheck = str(ObjToCheck).split(": ")[-1].rstrip()

                if len(ObjToCheck) > self.maxChar - 5:
                    nameString += ObjToCheck + "\n"

        if nameString != "":
            msgBox = QMessageBox()
            msgBox.setText(
                "The following variable names :\n%shas longer than %d characters!" % (nameString, self.maxChar - 5)
            )
            msgBox.exec_()

        tempS = f
        self.logger.debug("param solver text is ")
        self.logger.debug(f)
        t = self.convertToStringList(tempS)
        self.logger.debug("And now the ids come")

        f = "\n".join(t[0:3]) + "\n" + self.correctIds(t[3:]) + "\n"

        return f

    def convertToStringList(self, l):
        res = []
        temp = ""
        for i in l:
            if i == "\n":
                res.append(temp)
                temp = ""
            else:
                temp += i

        return res

    def findId(self, s):
        a = s[s.find("!") + 1 : s.find(" ", s.find("!"))]
        self.logger.debug(a)
        return a

    def correctIds(self, lineList):
        fileCopy = lineList[:]
        self.logger.debug("fds" + str(fileCopy))
        fileCopy = [" " + l for l in fileCopy]

        matchNumber = re.compile(r"\d+")

        counter = 0
        for line in lineList:
            counter += 1
            k = self.findId(line)
            if k != str(counter):

                descConnlen = 15
                res = fileCopy[:]
                for l in range(len(fileCopy)):
                    ids = matchNumber.findall(fileCopy[l])
                    for i in range(3):
                        if ids[i] == str(k):
                            ids[i] = str(counter)

                    fileCopyTempLine = fileCopy[l]
                    rest = fileCopyTempLine[fileCopyTempLine.find("!") :]
                    res[l] = ids[0] + " " + ids[1] + " " + ids[2] + " " + ids[3]
                    res[l] += " " * (descConnlen - len(res[l])) + rest

                fileCopy = res
                fileCopy = [l.replace("!" + str(k) + " ", "!" + str(counter) + " ") for l in fileCopy]

        return "\n".join(fileCopy)

    def exportInputsFlowSolver(self):
        f = ""
        f += "INPUTS " + str(self.lineNumOfPar) + "! for Type 935\n"

        numberOfInputs = 0

        counter = 0
        for t in self._massFlowContributors:
            res = t.exportInputsFlowSolver()
            f += res[0]
            counter += res[1] #DC this is a very strange way to print values, I would like to have 10 values per line and the fact that two go together makes it complicated
            numberOfInputs += res[1]

            if counter > 9 or t == self._massFlowContributors[-1]:
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

        for t in self._massFlowContributors:
            noHydraulicConnection = not isinstance(t, ConnectionBase) and not t.outputs and not t.inputs

            if noHydraulicConnection:
                continue
            else:
                res = t.exportOutputsFlowSolver(prefix, abc, equationNumber, simulationUnit)
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

        for t in self._massFlowContributors:

            res = t.exportPipeAndTeeTypesForTemp(unitNumber)
            f += res[0]
            unitNumber = res[1]

        self.editor.printerUnitnr = unitNumber

        return f

    def exportPrintPipeLosses(self):
        f = ""
        lossText = ""
        rightCounter = 0

        for t in self._massFlowContributors:
            if isinstance(t, SinglePipeConnection):
                if rightCounter != 0:
                    lossText += "+"
                lossText += "P" + t.displayName + "_kW"
                rightCounter += 1
            if isinstance(t, DoublePipeConnection):
                if rightCounter != 0:
                    lossText += "+"
                lossText += "P" + t.displayName + "Cold_kW" + "+"
                lossText += "P" + t.displayName + "Hot_kW"
                rightCounter += 1

        if rightCounter == 0:
            lossText += "0"

        f += "*** Pipe losses\nEQUATIONS 1\nPipeLossTot=" + lossText + "\n\n"
        return f

    def exportMassFlowPrinter(self, unitnr, descLen):
        typenr = 25
        printingMode = 0
        relAbsStart = 0
        overwriteApp = -1
        printHeader = -1
        delimiter = 0
        printLabels = 1

        f = "ASSIGN " + self.editor.diagramName.rsplit(".", 1)[0] + "_Mfr.prt " + str(unitnr) + "\n\n"

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

        s = ""
        equationType = "Mfr"
        breakline = 0
        for t in self._massFlowContributors:
            if isinstance(t, SinglePipeConnection):
                breakline, s = self._getEquation(breakline, s, t, "", equationType)
            if isinstance(t, DoublePipeConnection):
                breakline, s = self._getEquation(breakline, s, t, "Cold", equationType)
                breakline, s = self._getEquation(breakline, s, t, "Hot", equationType)
            if isinstance(t, TVentil) and t.isVisible():
                breakline += 1
                if breakline % 8 == 0:
                    s += "\n"
                s += "xFrac" + t.displayName + " "
        f += "INPUTS " + str(breakline) + "\n" + s + "\n" + "***" + "\n" + s + "\n\n"

        return f

    def _getEquation(self, breakline, s, t, temperature, equationType):
        breakline += 1
        if breakline % 8 == 0:
            s += "\n"
        s += equationType + t.displayName + temperature + " "
        return breakline, s

    @staticmethod
    def _addComment(firstColumn, comment):
        spacing = 40
        return str(firstColumn).ljust(spacing) + comment + "\n"

    def exportTempPrinter(self, unitnr, descLen):

        typenr = 25
        printingMode = 0
        relAbsStart = 0
        overwriteApp = -1
        printHeader = -1
        delimiter = 0
        printLabels = 1

        f = "ASSIGN " + self.editor.diagramName.rsplit(".", 1)[0] + "_T.prt " + str(unitnr) + "\n\n"

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

        s = ""
        equationType = "T"
        breakline = 0
        for t in self._massFlowContributors:
            if isinstance(t, SinglePipeConnection):
                breakline, s = self._getEquation(breakline, s, t, "", equationType)
            if isinstance(t, DoublePipeConnection):
                breakline, s = self._getEquation(breakline, s, t, "Cold", equationType)
                breakline, s = self._getEquation(breakline, s, t, "Hot", equationType)
        f += "INPUTS " + str(breakline) + "\n" + s + "\n" + "***" + "\n" + s + "\n\n"

        return f

    def exportFluids(self) -> str:
        def getValueOrVariableName(valueOrVariable: _tp.Union[float, _hlm.Variable], factor: float = 1) -> _tp.Union[float, str]:
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
        fluids = self.editor.fluids.fluids
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
{{loopLen}} = 
{{loopDia}} =
{{loopUVal}} =
{% endif -%}
{{loopRho}} = F{{fluid.name}}Rho
{{loopCp}} = F{{fluid.name}}Cp

{% endfor -%}
"""
        loops = self.editor.hydraulicLoops.hydraulicLoops

        nEquations = sum(6 if l.useLoopWideDefaults else 2 for l in loops)

        return self._render(template, loops=loops, nEquations=nEquations, names=_names)

    @staticmethod
    def _render(template: str, /, **kwargs):
        compiledTemplate = _jinja.Template(template)
        return compiledTemplate.render(**kwargs)
