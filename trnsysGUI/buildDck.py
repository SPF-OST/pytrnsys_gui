# pylint: skip-file
# type: ignore

import logging
import os
import typing as _tp

import pytrnsys.rsim.getConfigMixin as _rcm
import pytrnsys.trnsys_util.buildTrnsysDeck as _btd
import pytrnsys.trnsys_util.readConfigTrnsys as _rc
import pytrnsys.utils.result as _res

logger = logging.getLogger("root")


class buildDck(_rcm.GetConfigMixin):
    def __init__(self, pathConfig):
        super().__init__()

        self.pathConfig = pathConfig
        self.path = pathConfig

        self._defaultInputs()
        self.cmds = []

    def _defaultInputs(self):

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

    def buildTrnsysDeck(self) -> _res.Result[_tp.Optional[str]]:
        """
        It builds a TRNSYS Deck from a listDdck with pathDdck using the BuildingTrnsysDeck Class.
        it reads the Deck list and writes a deck file. Afterwards it checks that the deck looks fine

        """
        readConfigResult = self._readConfig(self.pathConfig, "run.config")
        if _res.isError(readConfigResult):
            return _res.error(readConfigResult)

        try:
            self.getConfig()
        except ValueError as valueError:
            return _res.error(str(valueError))

        self.nameBase = self.inputs["nameRef"]

        deckExplanation = []
        deckExplanation.append("! ** New deck built from list of ddcks. **\n")
        deck = _btd.BuildTrnsysDeck(
            self.path,
            self.nameBase,
            self._ddckFilePathWithComponentNames,
            self._defaultVisibility,
            self._ddckPlaceHolderValuesJsonPath,
        )
        result = deck.readDeckList(
            self.pathConfig,
            doAutoUnitNumbering=self.inputs["doAutoUnitNumbering"],
            dictPaths=self.dictDdckPaths,
            replaceLineList=self.replaceLines,
        )

        if _res.isError(result):
            return _res.error(result)

        deck.overwriteForcedByUser = self.overwriteForcedByUser
        deck.writeDeck(addedLines=deckExplanation)
        if deck.abortedByUser:
            return
        self.overwriteForcedByUser = deck.overwriteForcedByUser

        result = deck.checkTrnsysDeck(deck.nameDeck, check=self.inputs["checkDeck"])
        if _res.isError(result):
            return _res.error(result)

        if self.inputs["generateUnitTypesUsed"] == True:
            deck.saveUnitTypeFile()

        if self.inputs["addAutomaticEnergyBalance"] == True:
            deck.addAutomaticEnergyBalancePrinters()
            deck.writeDeck()  # Deck rewritten with added printer

        deck.analyseDck()

        return deck.nameDeck

    def _readConfig(self, path, name, parseFileCreated=False) -> _res.Result[None]:
        """
        It reads the config file used for running TRNSYS and loads the self.inputs dictionary.
        It also loads the read lines into self.lines
        """
        tool = _rc.ReadConfigTrnsys()

        self.lines = tool.readFile(path, name, self.inputs, parseFileCreated=parseFileCreated, controlDataType=False)
        if "pathBaseSimulations" in self.inputs:
            self.path = self.inputs["pathBaseSimulations"]

        resultsFolder = self.inputs.get("addResultsFolder")
        if not resultsFolder:
            return

        self.path = os.path.join(self.path, resultsFolder)

        if not os.path.isdir(self.path):
            try:
                os.mkdir(self.path)
            except FileNotFoundError:
                return _res.Error(f"The path could not be found: {self.path}")
