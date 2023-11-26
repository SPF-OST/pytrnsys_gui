import multiprocessing as _mp
import pathlib as _pl
import typing as _tp

import sys as _sys
import typer as _typer
import typing_extensions as _te

_ReadableFilePath = _te.Annotated[_pl.Path, _typer.Argument(readable=True, dir_okay=False, exists=True)]


def main(
    python_script_path: _ReadableFilePath,  # /NOSONAR  # pylint: disable=invalid-name
    arguments_to_script: _te.Annotated[  # /NOSONAR  # pylint: disable=invalid-name
        _tp.Optional[list[str]], _typer.Argument()
    ] = None,
) -> None:
    if arguments_to_script is None:
        arguments_to_script = []

    _runFile(python_script_path, arguments_to_script)


def _runFile(pythonScriptPath: _pl.Path, argumentsToScript: _tp.Sequence[str]) -> None:
    oldArgv = _sys.argv
    try:
        _sys.argv = [str(pythonScriptPath), *argumentsToScript]
        sourceCode = pythonScriptPath.read_text()
        compiledCode = compile(sourceCode, pythonScriptPath, mode="exec")
        exec(compiledCode)  # pylint: disable=exec-used
    finally:
        _sys.argv = oldArgv


if __name__ == "__main__":
    # Support freezing using PyInstaller, see
    # https://github.com/pyinstaller/pyinstaller/wiki/Recipe-Multiprocessing and
    # https://docs.python.org/3/library/multiprocessing.html#multiprocessing.freeze_support
    _mp.freeze_support()

    _typer.run(main)
