# pylint: skip-file
# type: ignore

import pytrnsys.trnsys_util.buildTrnsysDeck as build
import numpy as num
import os
import pytrnsys.trnsys_util.readConfigTrnsys as readConfig
import pytrnsys.utils.log as log
import logging

logger = logging.getLogger("root")


class buildDck:
    def __init__(self, pathConfig, name="pytrnsysRun", configFile=None, runPath=None):

        self.pathConfig = pathConfig
        self.path = pathConfig

        self.defaultInputs()
        self.cmds = []

        self.readConfig(self.pathConfig, "run.config")
        self.getConfig()

        self.nameBase = self.inputs["nameRef"]

        self.buildTrnsysDeck()

    def defaultInputs(self):

        self.inputs = {}
        self.inputs["ignoreOnlinePlotter"] = False
        self.inputs["removePopUpWindow"] = False

        self.inputs["checkDeck"] = True
        self.inputs["reduceCpu"] = 0
        self.inputs["combineAllCases"] = True
        self.inputs["parseFileCreated"] = True
        self.inputs["HOME$"] = None
        self.inputs["trnsysVersion"] = "TRNSYS_EXE"
        self.inputs["trnsysExePath"] = "enviromentalVariable"
        self.inputs["copyBuildingData"] = False  # activate when Type 55 is used or change the path to the source
        self.inputs["addResultsFolder"] = False
        self.inputs["rerunFailedCases"] = False
        self.inputs["scaling"] = False
        self.inputs["doAutoUnitNumbering"] = True
        self.inputs["addAutomaticEnergyBalance"] = True
        self.inputs["generateUnitTypesUsed"] = True
        self.inputs["runCases"] = True
        self.inputs["runType"] = "runFromConfig"
        self.inputs["outputLevel"] = "INFO"

        self.overwriteForcedByUser = False

        self.variablesOutput = []

    def buildTrnsysDeck(self):
        """
        It builds a TRNSYS Deck from a listDdck with pathDdck using the BuildingTrnsysDeck Class.
        it reads the Deck list and writes a deck file. Afterwards it checks that the deck looks fine

        """
        deckExplanation = []
        deckExplanation.append("! ** New deck built from list of ddcks. **\n")
        deck = build.BuildTrnsysDeck(self.path, self.nameBase, self.listDdck)
        deck.readDeckList(
            self.pathConfig,
            doAutoUnitNumbering=self.inputs["doAutoUnitNumbering"],
            dictPaths=self.dictDdckPaths,
            replaceLineList=self.replaceLines,
        )

        deck.overwriteForcedByUser = self.overwriteForcedByUser
        deck.writeDeck(addedLines=deckExplanation)
        if deck.abortedByUser:
            return
        self.overwriteForcedByUser = deck.overwriteForcedByUser

        deck.checkTrnsysDeck(deck.nameDeck, check=self.inputs["checkDeck"])

        if self.inputs["generateUnitTypesUsed"] == True:

            deck.saveUnitTypeFile()

        if self.inputs["addAutomaticEnergyBalance"] == True:
            deck.automaticEnegyBalanceStaff()
            deck.writeDeck()  # Deck rewritten with added printer

        return deck.nameDeck

    def addParametricVariations(self, variations):
        """
        it fills a variableOutput with a list of all variations to run
        format <class 'list'>: [['Ac', 'AcollAp', 1.5, 2.0, 1.5, 2.0], ['Vice', 'VIceS', 0.3, 0.3, 0.4, 0.4]]

        Parameters
        ----------
        variations : list of list
            list object containing the variations to be used.

        Returns
        -------

        """

        if self.inputs["combineAllCases"] == True:

            labels = []
            values = []
            for i, row in enumerate(variations):
                labels.append(row[:2])
                values.append(row[2:])

            value_permutations = num.array(num.meshgrid(*values), dtype=object).reshape(len(variations), -1)
            result = num.concatenate((labels, value_permutations), axis=1)
            self.variablesOutput = result.tolist()

        else:
            nVariations = len(variations)
            sizeOneVariation = len(variations[0]) - 2
            for n in range(len(variations)):
                sizeCase = len(variations[n]) - 2
                if sizeCase != sizeOneVariation:
                    raise ValueError(
                        "for combineAllCases=False all variations must have same lenght :%d case n:%d has a lenght of :%d"
                        % (sizeOneVariation, n + 1, sizeCase)
                    )

            self.variablesOutput = variations

    def readConfig(self, path, name, parseFileCreated=False):

        """
        It reads the config file used for running TRNSYS and loads the self.inputs dictionary.
        It also loads the readed lines into self.lines
        """
        tool = readConfig.ReadConfigTrnsys()

        self.lines = tool.readFile(path, name, self.inputs, parseFileCreated=parseFileCreated, controlDataType=False)
        # logger = log.setup_custom_logger('root', self.inputs['outputLevel'])
        # stop propagting to root logger
        # logger.propagate = False
        if "pathBaseSimulations" in self.inputs:
            self.path = self.inputs["pathBaseSimulations"]
        if self.inputs["addResultsFolder"] == False:
            pass
        else:
            self.path = os.path.join(self.path, self.inputs["addResultsFolder"])

            if not os.path.isdir(self.path):
                os.mkdir(self.path)

    def getConfig(self):
        """
        Reads the config file.

        Parameters
        ----------

        Returns
        -------

        """
        self.variation = []  # parametric studies
        self.parDeck = []  # fixed values changed in all simulations
        self.listDdck = []
        self.parameters = {}  # deck parameters fixed for all simulations
        self.listFit = {}
        self.listFitObs = []
        self.listDdckPaths = set()
        self.dictDdckPaths = {}
        self.caseDict = {}
        self.sourceFilesToChange = []
        self.sinkFilesToChange = []
        self.foldersForDDckVariation = []
        self.replaceLines = []

        for line in self.lines:

            splitLine = line.split()

            if splitLine[0] == "variation":
                variation = []
                for i in range(len(splitLine)):
                    if i == 0:
                        pass
                    elif i <= 2:
                        variation.append(splitLine[i])
                    else:
                        try:
                            variation.append(float(splitLine[i]))
                        except:
                            variation.append(splitLine[i])

                self.variation.append(variation)

            elif splitLine[0] == "deck":

                if splitLine[2] == "string":
                    self.parameters[splitLine[1]] = splitLine[3]
                else:
                    if splitLine[2].isdigit():
                        self.parameters[splitLine[1]] = float(splitLine[2])
                    else:
                        self.parameters[splitLine[1]] = splitLine[2]

            elif splitLine[0] == "replace":

                splitString = line.split('$"')

                oldString = splitString[1].split('"')[0]
                newString = splitString[2].split('"')[0]

                self.replaceLines.append((oldString, newString))

            elif splitLine[0] == "changeDDckFile":
                self.sourceFilesToChange.append(splitLine[1])
                sinkFilesToChange = []
                for i in range(len(splitLine)):
                    if i < 2:
                        pass
                    else:
                        sinkFilesToChange.append(splitLine[i])
                self.sinkFilesToChange.append(sinkFilesToChange)

            elif splitLine[0] == "addDDckFolder":
                for i in range(len(splitLine)):
                    if i > 0:
                        self.foldersForDDckVariation.append(splitLine[i])

            elif splitLine[0] == "fit":
                self.listFit[splitLine[1]] = [splitLine[2], splitLine[3], splitLine[4]]
            elif splitLine[0] == "case":
                self.listFit[splitLine[1]] = splitLine[2:]
            elif splitLine[0] == "fitobs":
                self.listFitObs.append(splitLine[1])

            elif splitLine[0] in self.inputs.keys():
                fullPath = os.path.join(self.inputs[splitLine[0]], splitLine[1])
                self.listDdck.append(fullPath)
                self.listDdckPaths.add(self.inputs[splitLine[0]])
                self.dictDdckPaths[fullPath] = self.inputs[splitLine[0]]
            else:

                pass

        if len(self.variation) > 0:
            self.addParametricVariations(self.variation)
            self.variationsUsed = True
        else:
            self.variationsUsed = False

        if len(self.sourceFilesToChange) > 0:
            self.changeDDckFilesUsed = True
        else:
            self.changeDDckFilesUsed = False

        if len(self.foldersForDDckVariation) > 0:
            self.foldersForDDckVariationUsed = True
        else:
            self.foldersForDDckVariationUsed = False
