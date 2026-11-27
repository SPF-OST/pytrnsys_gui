import pytest as _pt

import trnsysGUI.runConfig as _rc

_CONFIG = """\
string PROJECT$ "ddck"
#############USED DDCKs##################
COMMON$ head global

# Collector
#### component: Coll ####
COMMON$ Solar/type1 as Coll
deck CollA 2
#### end component: Coll ####
PROJECT$ control/control # the control
deck CtrlOn 1

PROJECT$ weather/weather
COMMON$ end global
"""


def _describe(config: _rc.RunConfig) -> list[str]:
    return [
        (
            f"[{item.componentName}]"
            if item.isComponentBlock
            else item.entry.include.toLine()
        )
        for item in config.getSectionItems()
    ]


class TestSectionItems:
    def testItemsInConfigOrder(self):
        config = _rc.RunConfig(_CONFIG)

        items = config.getSectionItems()

        assert _describe(config) == [
            "COMMON$ head global",
            "[Coll]",
            "PROJECT$ control/control",
            "PROJECT$ weather/weather",
            "COMMON$ end global",
        ]
        assert items[1].numberOfLines == 4
        assert items[2].entry.trailingLines == ("deck CtrlOn 1",)

    def testMoveDownKeepsUnattachedLinesInPlace(self):
        config = _rc.RunConfig(_CONFIG)

        config.moveSectionItem(1, 3)  # the Coll block after weather

        assert (
            config.toText()
            == """\
string PROJECT$ "ddck"
#############USED DDCKs##################
COMMON$ head global

# Collector
PROJECT$ control/control # the control
deck CtrlOn 1

PROJECT$ weather/weather
#### component: Coll ####
COMMON$ Solar/type1 as Coll
deck CollA 2
#### end component: Coll ####
COMMON$ end global
"""
        )

    def testMoveUpAndBackIsIdentity(self):
        config = _rc.RunConfig(_CONFIG)

        config.moveSectionItem(2, 0)
        assert _describe(config)[0] == "PROJECT$ control/control"

        config.moveSectionItem(0, 2)
        assert config.toText() == _CONFIG

    @_pt.mark.parametrize("index, newIndex", [(-1, 0), (0, 5), (0, -1)])
    def testInvalidMove(self, index, newIndex):
        with _pt.raises(IndexError):
            _rc.RunConfig(_CONFIG).moveSectionItem(index, newIndex)

    def testRemoveItemWithItsDeckLines(self):
        config = _rc.RunConfig(_CONFIG)

        config.removeSectionItem(2)

        assert "control" not in config.toText()
        assert "CtrlOn" not in config.toText()
        assert len(config.getSectionItems()) == 4

    def testReplaceIncludeKeepsCommentAndDeckLines(self):
        config = _rc.RunConfig(_CONFIG)

        config.replaceSectionInclude(
            2, _rc.DdckInclude("PROJECT$", "control/control", isGlobal=True)
        )

        assert (
            "PROJECT$ control/control global # the control\ndeck CtrlOn 1\n"
            in config.toText()
        )

    def testReplaceOnBlockFails(self):
        with _pt.raises(_rc.RunConfigError):
            _rc.RunConfig(_CONFIG).replaceSectionInclude(
                1, _rc.DdckInclude("PROJECT$", "x")
            )

    def testInsertBeforeEndAppearsBeforeEnd(self):
        config = _rc.RunConfig(_CONFIG)

        config.insertIncludeBeforeEnd(_rc.DdckInclude("PROJECT$", "new/x"))

        assert _describe(config)[-2:] == [
            "PROJECT$ new/x",
            "COMMON$ end global",
        ]


class TestReplaceIncludeLine:
    def testInBlockAndOutside(self):
        config = _rc.RunConfig(_CONFIG)
        blockLineIndex = (
            config.toText().splitlines().index("COMMON$ Solar/type1 as Coll")
        )
        looseLineIndex = blockLineIndex + 3

        config.replaceIncludeLine(
            blockLineIndex, _rc.DdckInclude("PROJECT$", "Coll/type1")
        )
        config.replaceIncludeLine(
            looseLineIndex,
            _rc.DdckInclude("PROJECT$", "control/control", isGlobal=True),
        )

        lines = config.toText().splitlines()
        assert lines[blockLineIndex] == "PROJECT$ Coll/type1"
        assert lines[looseLineIndex] == (
            "PROJECT$ control/control global # the control"
        )
        assert config.getComponentIncludes("Coll")[0].relativePath == (
            "Coll/type1"
        )

    def testNoIncludeOnLine(self):
        with _pt.raises(_rc.RunConfigError):
            _rc.RunConfig(_CONFIG).replaceIncludeLine(
                0, _rc.DdckInclude("PROJECT$", "x")
            )
