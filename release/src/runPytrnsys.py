import multiprocessing as _mp
import pathlib as _pl

import typer as _typer
import typing_extensions as _te

_ReadableFilePath = _te.Annotated[_pl.Path, _typer.Argument(readable=True, dir_okay=False, exists=True)]


def main(python_script_path: _ReadableFilePath) -> None:  # /NOSONAR  # pylint: disable=invalid-name
    # Support freezing using PyInstaller, see
    # https://github.com/pyinstaller/pyinstaller/wiki/Recipe-Multiprocessing and
    # https://docs.python.org/3/library/multiprocessing.html#multiprocessing.freeze_support
    _mp.freeze_support()

    _runFile(python_script_path)


def _runFile(pythonScriptPath: _pl.Path) -> None:
    sourceCode = pythonScriptPath.read_text()
    compiledCode = compile(sourceCode, pythonScriptPath, mode="exec")
    exec(compiledCode)  # pylint: disable=exec-used


_typer.run(main)
