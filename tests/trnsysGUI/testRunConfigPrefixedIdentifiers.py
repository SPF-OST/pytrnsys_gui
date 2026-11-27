import pytest as _pt

import trnsysGUI.runConfig as _rc

_CONFIG = """\
string PROJECT$ "ddck"
string nameRef "CollProject"
deck CollAreaTotal 100   # CollIgnored in comment
variation AColl CollAM2PerMWh 2 3
deck Collector_x 1
deck HxQNom CollACollAp*Collc0*1
#### component: Coll ####
COMMON$ Solar/collector as Coll
deck CollNbModTot 360
deck CollMfrMin CollMfrNom*0.1
#### end component: Coll ####
# deck CollCommented 1
PROJECT$ Coll/CollThing
deck :CollLocal 1
"""


class TestPrefixedIdentifiers:
    def testFindAfterRename(self):
        config = _rc.RunConfig(_CONFIG)
        config.renameComponent("Coll", "Solar")

        lines = config.findPrefixedIdentifierLines("Coll", "Solar")

        assert [
            (line.identifiers, line.isInComponentBlock) for line in lines
        ] == [
            (("CollAreaTotal",), False),
            (("CollAM2PerMWh",), False),
            # Can't be told apart from a local variable: offered too.
            (("Collector_x",), False),
            (("CollACollAp", "Collc0"), False),
            (("CollNbModTot",), True),
            (("CollMfrMin", "CollMfrNom"), True),
        ]
        assert lines[0].newLine == (
            "deck SolarAreaTotal 100   # CollIgnored in comment"
        )
        assert lines[3].newLine == "deck HxQNom SolarACollAp*Solarc0*1"
        assert lines[5].newLine == "deck SolarMfrMin SolarMfrNom*0.1"

    def testReplaceLine(self):
        config = _rc.RunConfig(_CONFIG)
        config.renameComponent("Coll", "Solar")
        line = config.findPrefixedIdentifierLines("Coll", "Solar")[4]

        config.replaceLine(line.lineIndex, line.line, line.newLine)

        assert "deck SolarNbModTot 360\n" in config.toText()
        with _pt.raises(_rc.RunConfigError):
            config.replaceLine(line.lineIndex, line.line, "x")

    def testNothingFound(self):
        # Only containing the name, or the name itself.
        config = _rc.RunConfig("deck AColl 1\ndeck Coll 2\n")

        assert not config.findPrefixedIdentifierLines("Coll", "Solar")
