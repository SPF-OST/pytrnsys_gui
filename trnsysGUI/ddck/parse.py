import pathlib as _pl
import pkgutil as _pu

import lark as _lark

import trnsysGUI.ddck as _ddck

_DDCK_LARK_GRAMMAR_FILE_NAME = "ddck.lark"


def _createParser() -> _lark.Lark:
    data = _pu.get_data(_ddck.__name__, _DDCK_LARK_GRAMMAR_FILE_NAME)
    assert data, "Could not find ddck Lark grammar file."
    grammar = data.decode()
    parser = _lark.Lark(grammar, parser="lalr")
    return parser


_PARSER = _createParser()


def parse_ddck(ddckFilePath: _pl.Path) -> _lark.Tree:
    ddckText = ddckFilePath.read_text()

    tree = _PARSER.parse(ddckText)

    return tree
