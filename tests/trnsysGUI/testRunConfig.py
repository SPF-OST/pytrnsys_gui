# pylint: disable=invalid-name  # `tmp_path` fixture
import pathlib as _pl
import subprocess as _sp

import pytest as _pt

import pytrnsys.trnsys_util.readConfigTrnsys as _rct
import trnsysGUI.runConfig as _rc

_REPO_DIR_PATH = _pl.Path(__file__).parents[2]

_CONFIG = """\
string LIBRARY "C:/lib"
##################PATHS##################
string PROJECT$ "C:/project/ddck"
string COMMON$ "C:/pytrnsys/data/ddcks"
string projectPath "C:/project"

#############USED DDCKs##################
PROJECT$ generic\\head
PROJECT$ Collector\\type1 # the collector
PROJECT$ Dhw\\temperatures_printer as Dhw
PROJECT$ weather\\weather global
PROJECT$ generic\\end
"""


def _setIncludes(config, componentName, includes):
    config.setComponentEntries(
        componentName, [_rc.ComponentEntry(i) for i in includes]
    )


def _getTrackedConfigFilePaths() -> list[_pl.Path]:
    output = _sp.run(
        ["git", "ls-files", "*.config"],
        cwd=_REPO_DIR_PATH,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [_REPO_DIR_PATH / line for line in output.splitlines() if line]


class TestDdckInclude:
    @_pt.mark.parametrize(
        "line, expected",
        [
            (
                "PROJECT$ Collector\\type1",
                _rc.DdckInclude("PROJECT$", "Collector\\type1"),
            ),
            (
                "PROJECT$ Dhw\\printer as Dhw  # comment",
                _rc.DdckInclude("PROJECT$", "Dhw\\printer", alias="Dhw"),
            ),
            (
                "DDCK$ weather\\weather global",
                _rc.DdckInclude("DDCK$", "weather\\weather", isGlobal=True),
            ),
            ("PROJECT$ a\\b as", None),
            ("PROJECT$ a\\b foo bar", None),
            ('string PROJECT$ "C:/x"', None),
            ("# PROJECT$ commented\\out", None),
            ("bool doAutoUnitNumbering True", None),
            ("PROJECT$", None),
        ],
    )
    def testTryParse(self, line, expected):
        assert _rc.DdckInclude.tryParse(line, {"LIB"}) == expected

    def testNonDollarVariableMustBeDefined(self):
        assert _rc.DdckInclude.tryParse("LIB a\\b", {"LIB"})
        assert not _rc.DdckInclude.tryParse("LIB a\\b", set())

    @_pt.mark.parametrize(
        "line",
        [
            "PROJECT$ Collector\\type1",
            "COMMON$ solar_collector\\type1\\type1 as Collector",
            "PROJECT$ weather\\weather global",
        ],
    )
    def testToLineRoundTrips(self, line):
        include = _rc.DdckInclude.tryParse(line, set())

        assert include.toLine() == line

    def testComponentName(self):
        assert (
            _rc.DdckInclude("PROJECT$", "Collector\\type1").componentName
            == "Collector"
        )
        assert (
            _rc.DdckInclude("P$", "lib\\type1\\type1", "Coll").componentName
            == "Coll"
        )

    def testResolve(self, tmp_path):
        include = _rc.DdckInclude("PROJECT$", "Collector\\type1")

        absolute = include.resolve({"PROJECT$": "C:/project/ddck"}, tmp_path)
        relative = include.resolve({"PROJECT$": ".\\ddck"}, tmp_path)

        assert absolute == _pl.Path("C:/project/ddck/Collector/type1.ddck")
        assert relative == tmp_path / "ddck" / "Collector" / "type1.ddck"
        assert include.resolve({}, tmp_path) is None


class TestRunConfigReading:
    def testPathVariables(self):
        config = _rc.RunConfig(_CONFIG)

        assert config.getPathVariables() == {
            "LIBRARY": "C:/lib",
            "PROJECT$": "C:/project/ddck",
            "COMMON$": "C:/pytrnsys/data/ddcks",
            "projectPath": "C:/project",
        }

    def testIncludes(self):
        config = _rc.RunConfig(_CONFIG)

        includes = [il.include for il in config.getIncludeLines()]

        assert [i.toLine() for i in includes] == [
            "PROJECT$ generic\\head",
            "PROJECT$ Collector\\type1",
            "PROJECT$ Dhw\\temperatures_printer as Dhw",
            "PROJECT$ weather\\weather global",
            "PROJECT$ generic\\end",
        ]
        assert config.getComponentNames() == []

    @_pt.mark.parametrize(
        "configFilePath",
        _getTrackedConfigFilePaths(),
        ids=lambda p: str(p.relative_to(_REPO_DIR_PATH)),
    )
    def testRealConfigsRoundTripByteForByte(self, configFilePath, tmp_path):
        config = _rc.RunConfig.read(configFilePath)

        outputFilePath = tmp_path / "out.config"
        config.write(outputFilePath)

        assert outputFilePath.read_bytes() == configFilePath.read_bytes()

    @_pt.mark.parametrize(
        "text, message",
        [
            ("#### component: A ####\nP$ a\\b\n", "never closed"),
            (
                "#### component: A ####\n#### component: B ####\n",
                "not closed",
            ),
            (
                "#### component: A ####\n#### end component: B ####\n",
                "doesn't match",
            ),
            (
                "#### component: A ####\n#### end component: A ####\n" * 2,
                "several blocks",
            ),
        ],
    )
    def testMalformedBlocks(self, text, message):
        with _pt.raises(_rc.RunConfigError, match=message):
            _rc.RunConfig(text)


class TestRunConfigEditing:
    _COLLECTOR_INCLUDES = [
        _rc.DdckInclude("COMMON$", "solar_collector\\type1\\type1", "Coll"),
        _rc.DdckInclude("PROJECT$", "Coll\\constants"),
    ]

    def testNewBlockGoesBeforeEnd(self):
        config = _rc.RunConfig(_CONFIG)

        _setIncludes(config, "Coll", self._COLLECTOR_INCLUDES)

        assert config.toText() == _CONFIG.replace(
            "PROJECT$ generic\\end\n",
            "#### component: Coll ####\n"
            "COMMON$ solar_collector\\type1\\type1 as Coll\n"
            "PROJECT$ Coll\\constants\n"
            "#### end component: Coll ####\n"
            "PROJECT$ generic\\end\n",
        )
        assert config.getComponentNames() == ["Coll"]
        assert config.getComponentIncludes("Coll") == self._COLLECTOR_INCLUDES
        assert "PROJECT$ Coll\\constants" not in [
            i.toLine() for i in config.getIncludesOutsideComponentBlocks()
        ]

    def testNewBlockWithoutEndGoesAfterLastInclude(self):
        config = _rc.RunConfig('string PROJECT$ "x"\nPROJECT$ a\\b\n')

        _setIncludes(config, "Coll", self._COLLECTOR_INCLUDES[1:])

        assert config.toText().splitlines()[1:] == [
            "PROJECT$ a\\b",
            "#### component: Coll ####",
            "PROJECT$ Coll\\constants",
            "#### end component: Coll ####",
        ]

    def testNewBlockInEmptyConfigGoesAfterUsedDdcksMarker(self):
        config = _rc.RunConfig("#### USED DDCKs ####\nbool x True\n")

        _setIncludes(config, "Coll", self._COLLECTOR_INCLUDES[1:])

        assert config.toText().splitlines()[1] == "#### component: Coll ####"

    def testReplaceAndRemoveBlock(self):
        config = _rc.RunConfig(_CONFIG)
        _setIncludes(config, "Coll", self._COLLECTOR_INCLUDES)

        _setIncludes(config, "Coll", self._COLLECTOR_INCLUDES[:1])
        assert config.getComponentIncludes("Coll") == (
            self._COLLECTOR_INCLUDES[:1]
        )

        config.removeComponent("Coll")
        assert config.toText() == _CONFIG

    def testRenameComponent(self):
        config = _rc.RunConfig(_CONFIG)
        _setIncludes(
            config,
            "Coll",
            [
                *self._COLLECTOR_INCLUDES,
                _rc.DdckInclude("COMMON$", "lib\\x", alias="Other"),
            ],
        )

        config.renameComponent("Coll", "Collector2")

        assert config.getComponentNames() == ["Collector2"]
        assert [
            i.toLine() for i in config.getComponentIncludes("Collector2")
        ] == [
            "COMMON$ solar_collector\\type1\\type1 as Collector2",
            "PROJECT$ Collector2\\constants",
            "COMMON$ lib\\x as Other",
        ]

    def testRenameToExistingComponentFails(self):
        config = _rc.RunConfig(_CONFIG)
        _setIncludes(config, "A", self._COLLECTOR_INCLUDES)
        _setIncludes(config, "B", self._COLLECTOR_INCLUDES)

        with _pt.raises(_rc.RunConfigError):
            config.renameComponent("A", "B")

    def testSetPathVariable(self):
        config = _rc.RunConfig(_CONFIG)

        config.setPathVariable("COMMON$", "D:/lib")
        config.setPathVariable("OTHER$", "E:/other")

        variables = config.getPathVariables()
        assert variables["COMMON$"] == "D:/lib"
        assert variables["OTHER$"] == "E:/other"
        lines = config.toText().splitlines()
        assert lines.index('string OTHER$ "E:/other"') == (
            lines.index('string COMMON$ "D:/lib"') + 1
        )

    def testSetPathVariableInConfigWithoutPaths(self):
        config = _rc.RunConfig("bool a True\nPROJECT$ x\\y\n")

        config.setPathVariable("PROJECT$", "C:/ddck")

        assert config.toText() == (
            'bool a True\nstring PROJECT$ "C:/ddck"\nPROJECT$ x\\y\n'
        )

    def testCrlfIsPreserved(self):
        config = _rc.RunConfig(_CONFIG.replace("\n", "\r\n"))

        _setIncludes(config, "Coll", self._COLLECTOR_INCLUDES)

        text = config.toText()
        assert "\r\n#### component: Coll ####\r\n" in text
        assert "\n" not in text.replace("\r\n", "")


class TestPytrnsysCompatibility:
    def testPytrnsysIgnoresBlockMarkers(self, tmp_path):
        config = _rc.RunConfig(_CONFIG)
        _setIncludes(config, "Coll", self._getIncludes())
        configFilePath = tmp_path / "run.config"
        config.write(configFilePath)

        # As `RunParallelTrnsys` reads run configs.
        reader = _rct.ReadConfigTrnsys()
        inputs: dict = {}
        lines = reader.readFile(
            str(tmp_path),
            "run.config",
            inputs,
            parseFileCreated=False,
            controlDataType=False,
        )
        includeLines = [
            line.strip()
            for line in lines
            if line.split()[0] in inputs and not line.startswith("string")
        ]

        assert not [line for line in lines if "component:" in line]
        assert includeLines == [
            include.toLine()
            for include in [il.include for il in config.getIncludeLines()]
        ]

    @staticmethod
    def _getIncludes():
        return [
            _rc.DdckInclude(
                "COMMON$", "solar_collector\\type1\\type1", "Coll"
            ),
            _rc.DdckInclude("PROJECT$", "Coll\\constants"),
        ]


class TestLibrary:
    def testConfiguredPathWins(self, tmp_path):
        assert (
            _rc.getDdckLibraryDirPath(str(tmp_path), lambda: None) == tmp_path
        )

    def testFallsBackToAutoDetection(self, tmp_path):
        autoDetected = tmp_path / "auto"

        assert (
            _rc.getDdckLibraryDirPath(
                str(tmp_path / "missing"), lambda: autoDetected
            )
            == autoDetected
        )
        assert _rc.getDdckLibraryDirPath("", lambda: None) is None

    def testSaveAndLoadConfiguredPath(self, tmp_path):
        settingsFilePath = tmp_path / "sub" / "ddckLibrary.json"

        assert _rc.loadConfiguredLibraryPath(settingsFilePath) == ""

        _rc.saveConfiguredLibraryPath("C:/lib", settingsFilePath)
        assert _rc.loadConfiguredLibraryPath(settingsFilePath) == "C:/lib"

        settingsFilePath.write_text("not json")
        assert _rc.loadConfiguredLibraryPath(settingsFilePath) == ""


# Excerpt of a real project config (DigiSolar Komotini).
_CONFIG_WITHOUT_BLOCKS = """\
string PROJECT$ "ddck"
string COMMON$ "..\\..\\..\\pytrnsys_gui\\data\\ddck"
COMMON$ head global

# Night cooling with the analytical model.
COMMON$ Solar_Library/EN12975/Type1357_NightCoolingEq as Coll
deck CollMfrMin CollMfrNom*0.1
deck CollNightConvOn 0   # 1: night cooling on
COMMON$ Solar_Library/EN12975/database/TVP_MT-Power_v4 as Coll
deck CollNbModTot 360

COMMON$ Hydronics/Heat_Exchangers/Type5b as Hx
deck HxLMTDNom 5
PROJECT$ Coll/extra # project ddck of the collector
COMMON$ generic/end
"""


class TestEntriesWithDeckLines:
    def testDeckLinesStayWithTheirDdck(self):
        config = _rc.RunConfig(_CONFIG_WITHOUT_BLOCKS)
        config.adoptEntries("Coll")
        # pylint: disable-next=unbalanced-tuple-unpacking
        first, second, third = config.getComponentEntries("Coll")

        # Swap the first two and remove the third.
        config.setComponentEntries("Coll", [second, first])

        block = config.toText().split("#### component: Coll ####\n")[1]
        assert block.split("#### end component: Coll ####")[0] == (
            "COMMON$ Solar_Library/EN12975/database/TVP_MT-Power_v4 as Coll\n"
            "deck CollNbModTot 360\n"
            "COMMON$ Solar_Library/EN12975/Type1357_NightCoolingEq as Coll\n"
            "deck CollMfrMin CollMfrNom*0.1\n"
            "deck CollNightConvOn 0   # 1: night cooling on\n"
        )
        assert third.include.relativePath == "Coll/extra"

    def testUnchangedIncludeLineKeepsItsComment(self):
        config = _rc.RunConfig(_CONFIG_WITHOUT_BLOCKS)
        config.adoptEntries("Coll")

        assert "PROJECT$ Coll/extra # project ddck of the collector" in (
            config.toText()
        )

        entries = config.getComponentEntries("Coll")
        changed = _rc.ComponentEntry(
            _rc.DdckInclude("PROJECT$", "Coll/extra", alias="Other"),
            originalLine=entries[2].originalLine,
        )
        config.setComponentEntries("Coll", [*entries[:2], changed])

        assert "PROJECT$ Coll/extra as Other\n" in config.toText()

    def testRenameKeepsDeckLines(self):
        config = _rc.RunConfig(_CONFIG_WITHOUT_BLOCKS)
        config.adoptEntries("Coll")

        config.renameComponent("Coll", "Coll2")

        lines = config.toText().splitlines()
        index = lines.index(
            "COMMON$ Solar_Library/EN12975/database/TVP_MT-Power_v4 as Coll2"
        )
        assert lines[index + 1] == "deck CollNbModTot 360"


class TestAdoption:
    def testFindAdoptableEntries(self):
        config = _rc.RunConfig(_CONFIG_WITHOUT_BLOCKS)

        adoptables = config.findAdoptableEntries("Coll")

        assert [a.entry.include.relativePath for a in adoptables] == [
            "Solar_Library/EN12975/Type1357_NightCoolingEq",
            "Solar_Library/EN12975/database/TVP_MT-Power_v4",
            "Coll/extra",  # by its directory
        ]
        assert adoptables[0].entry.trailingLines == (
            "deck CollMfrMin CollMfrNom*0.1",
            "deck CollNightConvOn 0   # 1: night cooling on",
        )
        # Ends at the blank line.
        assert adoptables[1].entry.trailingLines == ("deck CollNbModTot 360",)
        assert not config.findAdoptableEntries("Nothing")

    def testAdoptCreatesBlockAtFirstDdck(self):
        config = _rc.RunConfig(_CONFIG_WITHOUT_BLOCKS)

        assert config.adoptEntries("Coll") == 3

        assert (
            config.toText()
            == """\
string PROJECT$ "ddck"
string COMMON$ "..\\..\\..\\pytrnsys_gui\\data\\ddck"
COMMON$ head global

# Night cooling with the analytical model.
#### component: Coll ####
COMMON$ Solar_Library/EN12975/Type1357_NightCoolingEq as Coll
deck CollMfrMin CollMfrNom*0.1
deck CollNightConvOn 0   # 1: night cooling on
COMMON$ Solar_Library/EN12975/database/TVP_MT-Power_v4 as Coll
deck CollNbModTot 360
PROJECT$ Coll/extra # project ddck of the collector
#### end component: Coll ####

COMMON$ Hydronics/Heat_Exchangers/Type5b as Hx
deck HxLMTDNom 5
COMMON$ generic/end
"""
        )
        assert not config.findAdoptableEntries("Coll")

    def testAdoptAppendsToExistingBlock(self):
        config = _rc.RunConfig(_CONFIG_WITHOUT_BLOCKS)
        config.adoptEntries("Hx")
        config.setComponentEntries(
            "Hx",
            [
                *config.getComponentEntries("Hx"),
                _rc.ComponentEntry(_rc.DdckInclude("COMMON$", "x/y", "Coll")),
            ],
        )

        config.adoptEntries("Coll")

        hxEntries = config.getComponentEntries("Hx")
        collEntries = config.getComponentEntries("Coll")
        assert [e.include.relativePath for e in hxEntries] == [
            "Hydronics/Heat_Exchangers/Type5b",
            "x/y",  # inside the Hx block: not adopted by Coll
        ]
        assert len(collEntries) == 3

    def testAdoptedConfigIncludesSameDdcksForPytrnsys(self):
        config = _rc.RunConfig(_CONFIG_WITHOUT_BLOCKS)
        before = [il.include for il in config.getIncludeLines()]

        config.adoptEntries("Coll")
        config.adoptEntries("Hx")

        after = [il.include for il in config.getIncludeLines()]
        assert sorted(before, key=str) == sorted(after, key=str)


class TestComponentNames:
    def testDdcksWithoutComponentAreNotAdoptable(self):
        config = _rc.RunConfig(_CONFIG_WITHOUT_BLOCKS)

        assert not config.findAdoptableEntries("")
        assert config.adoptEntries("") == 0

    @_pt.mark.parametrize("name", ["", "a b", "a#b"])
    def testInvalidNamesAreRejected(self, name):
        config = _rc.RunConfig(_CONFIG)
        entries = [_rc.ComponentEntry(_rc.DdckInclude("PROJECT$", "a\b"))]

        with _pt.raises(_rc.RunConfigError, match="Invalid component name"):
            config.setComponentEntries(name, entries)


class TestRenameOutsideBlocks:
    def testRenamesLinesOfComponentOutsideBlocks(self):
        config = _rc.RunConfig(
            'string PROJECT$ "ddck"\n'
            "PROJECT$ Collector/type1 # the collector\n"
            "PROJECT$ Dhw/printer as Collector\n"
            "COMMON$ lib/x as Collector\n"
            "PROJECT$ CollectorOther/y\n"
            "PROJECT$ generic/end\n"
        )

        config.renameComponent("Collector", "Coll")

        assert config.toText() == (
            'string PROJECT$ "ddck"\n'
            "PROJECT$ Coll/type1 # the collector\n"
            "PROJECT$ Dhw/printer as Coll\n"
            "COMMON$ lib/x as Coll\n"
            "PROJECT$ CollectorOther/y\n"
            "PROJECT$ generic/end\n"
        )
