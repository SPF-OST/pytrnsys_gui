import collections.abc as _cabc
import logging as _log
import pathlib as _pl
import typing as _tp

import pytrnsys.rsim.getConfigMixin as _rcm
import pytrnsys.trnsys_util.buildTrnsysDeck as _btd
import pytrnsys.trnsys_util.readConfigTrnsys as _rc
import pytrnsys.utils.result as _res
import pytrnsys.utils.warnings as _warn

logger = _log.getLogger("root")


class DckBuilder(_rcm.GetConfigMixin):  # type: ignore[name-defined]
    def __init__(self, projectDirPath: _pl.Path) -> None:
        super().__init__()

        self._projectDirPath = projectDirPath
        self._outputDirPath = projectDirPath

        self.inputs = dict[str, _tp.Any]()
        self.overwriteForcedByUser = False
        self.variablesOutput = list[_tp.Any]()
        self.lines: _cabc.Sequence[str] | None = None

        self._setDefaultInputs()

    def _setDefaultInputs(self):

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

    def buildTrnsysDeck(self) -> _res.Result[_warn.ValueWithWarnings[str | None]]:
        """
        It builds a TRNSYS Deck from a listDdck with pathDdck using the BuildingTrnsysDeck Class.
        it reads the Deck list and writes a deck file. Afterwards it checks that the deck looks fine

        """
        readConfigResult = self._readConfig()
        if _res.isError(readConfigResult):
            return _res.error(readConfigResult)

        try:
            self.getConfig()
        except ValueError as valueError:
            return _res.error(str(valueError))

        nameBase = self.inputs["nameRef"]

        deckExplanation = []
        deckExplanation.append("! ** New deck built from list of ddcks. **\n")
        deck = _btd.BuildTrnsysDeck(  # type: ignore[attr-defined]
            str(self._outputDirPath),
            nameBase,
            self._includedDdckFiles,
            self._defaultVisibility,
            self._ddckPlaceHolderValuesJsonPath,
        )
        result = deck.readDeckList(
            self._projectDirPath,
            doAutoUnitNumbering=self.inputs["doAutoUnitNumbering"],
            dictPaths=self.dictDdckPaths,
            replaceLineList=self.replaceLines,
        )

        if _res.isError(result):
            return _res.error(result)
        warnings: _warn.ValueWithWarnings[None] = _res.value(result)

        deck.overwriteForcedByUser = self.overwriteForcedByUser
        deck.writeDeck(addedLines=deckExplanation)
        if deck.abortedByUser:
            return warnings.withValue(None)

        self.overwriteForcedByUser = deck.overwriteForcedByUser

        result = deck.checkTrnsysDeck(deck.nameDeck, check=self.inputs["checkDeck"])
        if _res.isError(result):
            return _res.error(result)

        if self.inputs["generateUnitTypesUsed"]:
            deck.saveUnitTypeFile()

        if self.inputs["addAutomaticEnergyBalance"]:
            deck.addAutomaticEnergyBalancePrinters()
            deck.writeDeck()  # Deck rewritten with added printer

        deck.analyseDck()

        return warnings.withValue(deck.nameDeck)

    def _readConfig(self) -> _res.Result[None]:
        tool = _rc.ReadConfigTrnsys()  # type: ignore[attr-defined]

        configFileName = "run.config"

        configFilePath = self._projectDirPath / configFileName
        if not configFilePath.is_file():
            return _res.Error(
                f"The config file `{configFilePath}` does not exist or isn't a file. "
                "Please create it first before exporting the .dck file."
            )

        self.lines = tool.readFile(
            str(self._projectDirPath),
            configFileName,
            self.inputs,
            parseFileCreated=False,
            controlDataType=False,
        )
        if "pathBaseSimulations" in self.inputs:
            self._outputDirPath = _pl.Path(self.inputs["pathBaseSimulations"])

        resultsFolder = self.inputs.get("addResultsFolder")
        if not resultsFolder:
            return None

        self._outputDirPath = self._outputDirPath / resultsFolder

        try:
            self._outputDirPath.mkdir(parents=True, exist_ok=True)
        except FileNotFoundError:
            return _res.Error(f"Could not create directory: {self._outputDirPath}")

        return None
