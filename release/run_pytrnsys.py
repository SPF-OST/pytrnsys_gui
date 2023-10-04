import pathlib as _pl

import typer as _typer
import typing_extensions as _te


def main(python_script_path: _te.Annotated[_pl.Path, _typer.Argument(readable=True, dir_okay=False)]) -> None:
    _runFile(python_script_path)


def _runFile(pythonScriptPath: _pl.Path) -> None:
    sourceCode = pythonScriptPath.read_text()
    compiledCode = compile(sourceCode, pythonScriptPath, "exec")
    exec(compiledCode)


_typer.run(main)
