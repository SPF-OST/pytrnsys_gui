from __future__ import annotations

import collections.abc as _cabc
import functools as _ft
import pathlib as _pl


class ConfigFileUpdater:
    def __init__(self, configFilePath: _pl.Path) -> None:  # type: ignore[name-defined]
        self._configFilePath = configFilePath

        configFileContents = _pl.Path(self._configFilePath).read_text("UTF8")
        self.lines = configFileContents.splitlines()

    def statementChecker(self, keyword: str) -> int:
        for i, line in enumerate(self.lines):
            if keyword in line:
                return i
        return -1

    def updateConfig(self):
        self.lines = [l for l in self.lines if not l.startswith("PROJECT$ ")]

        lineNameRef = self.statementChecker("string nameRef")
        projectDirName = self._projectDirPath.name
        if lineNameRef == -1:
            self.lines.append(f'string nameRef "{projectDirName}"')
        else:
            self.lines[lineNameRef] = f'string nameRef "{projectDirName}"'

        ddckDirPath = self._projectDirPath / "ddck"

        linePaths = self.statementChecker("#PATHS#")
        if linePaths == -1:
            self.lines.append(
                f'''\

"##################PATHS##################"

string PROJECT$ "{ddckDirPath}"'''
            )
        else:
            lineProjectPathDdck = self.statementChecker("PROJECT$ ")
            if lineProjectPathDdck == -1:
                self.lines.append(f'string PROJECT$ "{ddckDirPath}"')
            else:
                self.lines[lineProjectPathDdck] = (
                    f'string PROJECT$ "{ddckDirPath}"'
                )

        lineProjectPath = self.statementChecker("string projectPath")
        if lineProjectPath == -1:
            self.lines.append(f'string projectPath "{self._projectDirPath}"')
        else:
            self.lines[lineProjectPath] = (
                f'string projectPath "{self._projectDirPath}"'
            )

        lineDdck = self.statementChecker("USED DDCKs")
        if lineDdck == -1:
            self.lines.append("\n#############USED DDCKs##################\n")
            lineDdck = len(self.lines) - 2

        sortedDdckFilePaths = self._getSortedDdckFilePaths(ddckDirPath)

        for i, ddckFilePath in enumerate(sortedDdckFilePaths):
            ddckFilePathWithoutSuffix = ddckFilePath.with_suffix("")
            self.lines.insert(
                lineDdck + 2 + i, f"PROJECT$ {ddckFilePathWithoutSuffix}"
            )

        newConfigFileContents = "\n".join(self.lines)
        self._configFilePath.write_text(newConfigFileContents)

    @staticmethod
    def _getSortedDdckFilePaths(
        ddckDirPath: _pl.Path,
    ) -> _cabc.Sequence[_pl.Path]:
        @_ft.cmp_to_key
        def cmpHeadFirstEndLast(path1: _pl.Path, path2: _pl.Path) -> int:
            stem1 = path1.stem
            stem2 = path2.stem

            if stem1 == "head" and stem2 != "head":
                return -1
            if stem1 != "head" and stem2 == "head":
                return 1
            if stem1 == "end" and stem2 != "end":
                return 1
            if stem1 != "end" and stem2 == "end":
                return -1

            if path1 == path2:
                return 0

            return -1 if str(path1) < str(path2) else 1

        absoluteDdckFilePaths = ddckDirPath.rglob("*.ddck")
        relativeDdckFilePaths = [
            p.relative_to(ddckDirPath) for p in absoluteDdckFilePaths
        ]
        sortedDdckFilePaths = sorted(
            relativeDdckFilePaths, key=cmpHeadFirstEndLast
        )
        return sortedDdckFilePaths

    @property
    def _projectDirPath(self) -> _pl.Path:
        return self._configFilePath.parent
