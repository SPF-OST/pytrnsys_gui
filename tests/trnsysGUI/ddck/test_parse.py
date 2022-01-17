import typing as _tp
import pathlib as _pl

import lark as _lark
import lark.tree as _ltree
import lark.visitors as _lvis

import trnsysGUI.ddck.parse as _parse


def test_parse():
    containingDirPath = _pl.Path(__file__).parent

    ddckFilePath = containingDirPath / "type977.ddck"

    tree = _parse.parse_ddck(ddckFilePath)

    pngFilePath = containingDirPath / "tree-output.png"

    _ltree.pydot__tree_to_png(tree, str(pngFilePath))

    print(tree.pretty())

    visitor = _CollectAllVariableNamesVisitor()

    visitor.visit(tree)

    print("\n".join(visitor.variableNames))


class _CollectAllVariableNamesVisitor(_lvis.Visitor_Recursive):
    def __init__(self):
        super().__init__()

        self._variableNames = set()

    @property
    def variableNames(self) -> _tp.Sequence[str]:
        return sorted(self._variableNames)

    def shared_var(self, tree: _lark.Tree) -> None:
        self._addVariableName(tree)

    def private_var(self, tree: _lark.Tree) -> None:
        self._addVariableName(tree)

    def computed_var(self, tree: _lark.Tree) -> None:
        self._addVariableName(tree)

    def _addVariableName(self, tree: _lark.Tree) -> None:
        children = tree.children
        assert len(children) == 1
        child = children[0]

        assert isinstance(child, _lark.Token)
        token = child

        variableName = token.value

        self._variableNames.add(variableName)
