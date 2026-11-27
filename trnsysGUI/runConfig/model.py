"""Reading and editing the ddck include lines of a pytrnsys run config.

The config file stays the source of truth: everything the GUI doesn't
manage (settings, comments, `calc` lines, ...) is preserved verbatim.

The GUI groups the ddcks of each diagram component into a block::

    #### component: Collector ####
    COMMON$ Solar_Library\\EN12975\\Type1357_NightCoolingEq as Collector
    PROJECT$ Collector\\collector_constants
    #### end component: Collector ####

pytrnsys ignores everything after a `#`, so the markers don't change how
the config is run.
"""

import collections.abc as _cabc
import dataclasses as _dc
import pathlib as _pl
import re as _re
import typing as _tp

PROJECT_PATH_VARIABLE = "PROJECT$"
LIBRARY_PATH_VARIABLE = "COMMON$"

_COMMENT_CHARACTER = "#"

_BLOCK_BEGIN_REGEX = _re.compile(
    r"^\s*#+\s*component:\s*(?P<name>\S+?)\s*#*\s*$"
)
_BLOCK_END_REGEX = _re.compile(
    r"^\s*#+\s*end component:\s*(?P<name>\S+?)\s*#*\s*$"
)
_STRING_REGEX = _re.compile(r'^\s*string\s+(?P<name>\S+)\s+"(?P<value>[^"]*)"')

_USED_DDCKS_MARKER = "USED DDCKs"
_PATHS_MARKER = "#PATHS#"


def _createBlockBeginLine(componentName: str) -> str:
    return f"#### component: {componentName} ####"


def _createBlockEndLine(componentName: str) -> str:
    return f"#### end component: {componentName} ####"


def isValidComponentName(componentName: str) -> bool:
    """Block markers need a non-empty name without spaces or `#`."""
    return bool(componentName) and not _re.search(r"[\s#]", componentName)


def _checkComponentName(componentName: str) -> None:
    if not isValidComponentName(componentName):
        raise RunConfigError(
            f"Invalid component name `{componentName}`: it must not be empty"
            " or contain spaces or `#`."
        )


def _stripComment(line: str) -> str:
    return line.split(_COMMENT_CHARACTER, maxsplit=1)[0]


@_dc.dataclass(frozen=True)
class DdckInclude:
    """A line like `COMMON$ Solar_Library\\EN12975\\Type1357 as Coll`."""

    pathVariable: str  # e.g. "PROJECT$"
    relativePath: str  # as written, without the ".ddck" suffix
    alias: str | None = None  # the `as` part
    isGlobal: bool = False

    @staticmethod
    def tryParse(
        line: str, pathVariableNames: _cabc.Container[str]
    ) -> "DdckInclude | None":
        """Mirrors `GetConfigMixin._includeDdckFile` in pytrnsys: a line is an
        include if its first word is a (path) variable defined in the config.
        Variables ending in `$` are accepted even if not (yet) defined, as
        pytrnsys defines `PROJECT$` itself for `run.config`."""
        words = _stripComment(line).split()
        if len(words) < 2:
            return None

        pathVariable = words[0]
        isPathVariable = (
            pathVariable in pathVariableNames or pathVariable.endswith("$")
        )
        if not isPathVariable or pathVariable == "string":
            return None

        relativePath = words[1]
        rest = words[2:]

        if not rest:
            return DdckInclude(pathVariable, relativePath)

        if rest == ["global"]:
            return DdckInclude(pathVariable, relativePath, isGlobal=True)

        if len(rest) == 2 and rest[0] == "as":
            return DdckInclude(pathVariable, relativePath, alias=rest[1])

        return None

    def toLine(self) -> str:
        line = f"{self.pathVariable} {self.relativePath}"
        if self.alias:
            line += f" as {self.alias}"
        elif self.isGlobal:
            line += " global"
        return line

    @property
    def componentName(self) -> str:
        """The name pytrnsys uses for the component (local variables,
        placeholders): the alias, or the containing directory's name."""
        if self.alias:
            return self.alias
        return _pl.PureWindowsPath(self.relativePath).parent.name

    def resolve(
        self, pathVariables: _cabc.Mapping[str, str], configDirPath: _pl.Path
    ) -> _pl.Path | None:
        """The absolute path of the ddck file, or None if the path variable
        isn't defined."""
        basePathString = pathVariables.get(self.pathVariable)
        if basePathString is None:
            return None

        basePath = _pl.Path(basePathString)
        if not basePath.is_absolute():
            basePath = configDirPath / basePath

        relativePath = _pl.Path(
            _pl.PureWindowsPath(self.relativePath).as_posix()
        )
        return (basePath / relativePath).with_suffix(".ddck")


@_dc.dataclass(frozen=True)
class ComponentEntry:
    """A ddck of a component together with the lines following it in the
    config (`deck` parameters, comments), which move and get removed with
    it. The include line itself is regenerated from `include`."""

    include: DdckInclude
    trailingLines: _tp.Tuple[str, ...] = ()

    # The line as read, to keep its formatting and trailing comment as long
    # as the include doesn't change.
    originalLine: str | None = _dc.field(default=None, compare=False)

    def toLines(self) -> _tp.Sequence[str]:
        return [self._getIncludeLine(), *self.trailingLines]

    def _getIncludeLine(self) -> str:
        if self.originalLine is not None:
            originalInclude = DdckInclude.tryParse(
                self.originalLine, {self.include.pathVariable}
            )
            if originalInclude == self.include:
                return self.originalLine
        return self.include.toLine()


@_dc.dataclass(frozen=True)
class AdoptableEntry:
    lineIndex: int
    entry: ComponentEntry

    @property
    def numberOfLines(self) -> int:
        return 1 + len(self.entry.trailingLines)


@_dc.dataclass(frozen=True)
class SectionItem:
    """An element of the config's ddck section, in config order: a component
    block (`componentName` set) or a ddck outside of blocks (`entry` set,
    with the lines following it)."""

    lineIndex: int
    numberOfLines: int
    componentName: str | None = None
    entry: ComponentEntry | None = None

    @property
    def isComponentBlock(self) -> bool:
        return self.componentName is not None


@_dc.dataclass(frozen=True)
class PrefixedIdentifiersLine:
    """A config line using identifiers prefixed with a component's old name
    (e.g. `deck CollNbModTot 360` for component `Coll`) and the line with
    the new name."""

    lineIndex: int
    line: str
    newLine: str
    identifiers: _tp.Tuple[str, ...]
    isInComponentBlock: bool


@_dc.dataclass(frozen=True)
class IncludeLine:
    lineIndex: int
    include: DdckInclude
    blockComponentName: str | None  # None: not in a component block


@_dc.dataclass(frozen=True)
class _Block:
    componentName: str
    beginLineIndex: int
    endLineIndex: int  # index of the end marker line


class RunConfigError(Exception):
    pass


class RunConfig:  # pylint: disable=too-many-public-methods
    """An editable run config. All edits keep unrelated lines untouched."""

    def __init__(self, text: str, filePath: _pl.Path | None = None) -> None:
        self.filePath = filePath
        self._hasTrailingNewline = text.endswith("\n")
        self._newline = "\r\n" if "\r\n" in text else "\n"
        self._lines = text.replace("\r\n", "\n").split("\n")
        if self._hasTrailingNewline:
            self._lines.pop()

        self._getBlocks()  # raises on malformed blocks

    # Reading and writing

    @staticmethod
    def read(filePath: _pl.Path) -> "RunConfig":
        data = filePath.read_bytes()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("windows-1252")
        # Keep line endings: `read_bytes` doesn't translate them.
        return RunConfig(text, filePath)

    def write(self, filePath: _pl.Path | None = None) -> None:
        filePath = filePath or self.filePath
        if not filePath:
            raise ValueError("No file path given.")
        filePath.write_bytes(self.toText().encode("utf-8"))
        self.filePath = filePath

    def toText(self) -> str:
        text = "\n".join(self._lines)
        if self._hasTrailingNewline:
            text += "\n"
        return text.replace("\n", self._newline)

    @property
    def configDirPath(self) -> _pl.Path:
        if not self.filePath:
            raise ValueError("The config has no file path.")
        return self.filePath.parent

    # Path variables (`string NAME$ "value"`)

    def getPathVariables(self) -> dict[str, str]:
        variables = {}
        for line in self._lines:
            match = _STRING_REGEX.match(_stripComment(line))
            if match:
                variables[match.group("name")] = match.group("value")
        return variables

    def setPathVariable(self, name: str, value: str) -> None:
        newLine = f'string {name} "{value}"'

        for index, line in enumerate(self._lines):
            match = _STRING_REGEX.match(_stripComment(line))
            if match and match.group("name") == name:
                self._lines[index] = newLine
                return

        self._lines.insert(self._getPathVariableInsertionIndex(), newLine)

    def setString(self, name: str, value: str) -> None:
        """Sets `string <name> "<value>"`, added after the last `string`
        line if missing."""
        newLine = f'string {name} "{value}"'

        lastStringIndex = None
        for index, line in enumerate(self._lines):
            match = _STRING_REGEX.match(_stripComment(line))
            if not match:
                continue
            if match.group("name") == name:
                self._lines[index] = newLine
                return
            lastStringIndex = index

        insertionIndex = (
            lastStringIndex + 1
            if lastStringIndex is not None
            else self._getPathVariableInsertionIndex()
        )
        self._lines.insert(insertionIndex, newLine)

    def insertIncludeBeforeEnd(self, include: DdckInclude) -> None:
        """Adds a ddck outside of component blocks, before the `end` ddck
        (or after the last ddck)."""
        self._lines.insert(self._getBlockInsertionIndex(), include.toLine())

    def _getPathVariableInsertionIndex(self) -> int:
        # After the last path variable (`string X$ ...`) ...
        lastPathVariableIndex = None
        for index, line in enumerate(self._lines):
            match = _STRING_REGEX.match(_stripComment(line))
            if match and match.group("name").endswith("$"):
                lastPathVariableIndex = index
        if lastPathVariableIndex is not None:
            return lastPathVariableIndex + 1

        # ... or after the PATHS marker ...
        for index, line in enumerate(self._lines):
            if _PATHS_MARKER in line:
                return index + 1

        # ... or before the first include ...
        includeLines = self.getIncludeLines()
        if includeLines:
            return self._getFirstLineIndexOfIncludeSection(includeLines)

        return len(self._lines)

    def _getFirstLineIndexOfIncludeSection(
        self, includeLines: _cabc.Sequence[IncludeLine]
    ) -> int:
        firstIndex = includeLines[0].lineIndex
        for block in self._getBlocks():
            firstIndex = min(firstIndex, block.beginLineIndex)
        return firstIndex

    # Includes

    def getIncludeLines(self) -> _tp.Sequence[IncludeLine]:
        pathVariableNames = self.getPathVariables().keys()
        blocks = self._getBlocks()

        includeLines = []
        for index, line in enumerate(self._lines):
            include = DdckInclude.tryParse(line, pathVariableNames)
            if not include:
                continue
            block = self._findBlockContaining(blocks, index)
            blockComponentName = block.componentName if block else None
            includeLines.append(
                IncludeLine(index, include, blockComponentName)
            )
        return includeLines

    def getComponentNames(self) -> _tp.Sequence[str]:
        return [b.componentName for b in self._getBlocks()]

    def getComponentEntries(
        self, componentName: str
    ) -> _tp.Sequence[ComponentEntry]:
        block = self._findBlock(componentName)
        if not block:
            return []
        _, entries = self._getBlockContent(block)
        return entries

    def getComponentIncludes(
        self, componentName: str
    ) -> _tp.Sequence[DdckInclude]:
        return [e.include for e in self.getComponentEntries(componentName)]

    def getIncludesOutsideComponentBlocks(self) -> _tp.Sequence[DdckInclude]:
        return [
            il.include
            for il in self.getIncludeLines()
            if il.blockComponentName is None
        ]

    def setComponentEntries(
        self, componentName: str, entries: _cabc.Sequence[ComponentEntry]
    ) -> None:
        """Replaces the component's ddcks (with their trailing lines). Lines
        at the beginning of an existing block, before its first ddck, are
        kept. An empty sequence removes the block."""
        _checkComponentName(componentName)
        block = self._findBlock(componentName)

        if not entries:
            if block:
                del self._lines[block.beginLineIndex : block.endLineIndex + 1]
            return

        leadingLines: _tp.Sequence[str] = []
        if block:
            leadingLines, _ = self._getBlockContent(block)

        newBlockLines = [
            _createBlockBeginLine(componentName),
            *leadingLines,
            *(line for entry in entries for line in entry.toLines()),
            _createBlockEndLine(componentName),
        ]

        if block:
            self._lines[block.beginLineIndex : block.endLineIndex + 1] = (
                newBlockLines
            )
            return

        insertionIndex = self._getBlockInsertionIndex()
        self._lines[insertionIndex:insertionIndex] = newBlockLines

    def removeComponent(self, componentName: str) -> None:
        self.setComponentEntries(componentName, [])

    def renameComponent(self, oldName: str, newName: str) -> None:
        """Renames the component's block and its ddcks outside of blocks
        (those pytrnsys attributes to it, e.g. in configs without blocks).
        Aliases equal to the old name and project ddcks in the component's
        ddck folder follow the rename (the GUI moves `ddck/<old name>` to
        `ddck/<new name>`)."""
        _checkComponentName(newName)
        if self._findBlock(newName):
            raise RunConfigError(
                f"The config already has a block for component `{newName}`."
            )

        self._renameIncludesOutsideBlocks(oldName, newName)

        block = self._findBlock(oldName)
        if not block:
            return

        leadingLines, entries = self._getBlockContent(block)
        renamedEntries = [
            _dc.replace(
                entry,
                include=self._renameInclude(entry.include, oldName, newName),
            )
            for entry in entries
        ]

        self._lines[block.beginLineIndex : block.endLineIndex + 1] = [
            _createBlockBeginLine(newName),
            *leadingLines,
            *(line for entry in renamedEntries for line in entry.toLines()),
            _createBlockEndLine(newName),
        ]

    def _renameIncludesOutsideBlocks(self, oldName: str, newName: str) -> None:
        if not isValidComponentName(oldName):
            return

        for includeLine in self.getIncludeLines():
            include = includeLine.include
            isOfComponent = (
                includeLine.blockComponentName is None
                and include.componentName == oldName
            )
            if not isOfComponent:
                continue

            renamedInclude = self._renameInclude(include, oldName, newName)
            if renamedInclude == include:
                continue

            originalLine = self._lines[includeLine.lineIndex]
            comment = originalLine[len(_stripComment(originalLine)) :]
            newLine = renamedInclude.toLine()
            if comment:
                newLine += " " + comment
            self._lines[includeLine.lineIndex] = newLine

    # The ddck section as a whole (project ddcks and component blocks)

    def getSectionItems(self) -> _tp.Sequence[SectionItem]:
        """Component blocks and ddcks outside of blocks, in config order.
        Lines that belong to neither (blank lines, headings, ...) aren't
        items and stay where they are when items are moved."""
        pathVariableNames = self.getPathVariables().keys()
        blocks = self._getBlocks()

        items = [
            SectionItem(
                b.beginLineIndex,
                b.endLineIndex - b.beginLineIndex + 1,
                componentName=b.componentName,
            )
            for b in blocks
        ]

        for includeLine in self.getIncludeLines():
            if includeLine.blockComponentName is not None:
                continue
            trailingLines = self._getTrailingLines(
                includeLine.lineIndex, pathVariableNames, blocks
            )
            entry = ComponentEntry(
                includeLine.include,
                tuple(trailingLines),
                self._lines[includeLine.lineIndex],
            )
            items.append(
                SectionItem(
                    includeLine.lineIndex,
                    1 + len(trailingLines),
                    entry=entry,
                )
            )

        return sorted(items, key=lambda i: i.lineIndex)

    def moveSectionItem(self, index: int, newIndex: int) -> None:
        """Moves the item to position `newIndex` among the items: its lines
        go just before the item now at that position (or after the last
        item)."""
        items = self.getSectionItems()
        if index == newIndex:
            return
        if not (0 <= index < len(items) and 0 <= newIndex < len(items)):
            raise IndexError(f"Can't move item {index} to {newIndex}.")

        item = items[index]
        movedLines = self._lines[
            item.lineIndex : item.lineIndex + item.numberOfLines
        ]

        if newIndex > index:
            target = items[newIndex]
            insertionIndex = target.lineIndex + target.numberOfLines
        else:
            insertionIndex = items[newIndex].lineIndex

        # Insert first (indices before the item are unaffected), then delete.
        self._lines[insertionIndex:insertionIndex] = movedLines
        deleteStart = (
            item.lineIndex
            if insertionIndex > item.lineIndex
            else item.lineIndex + len(movedLines)
        )
        del self._lines[deleteStart : deleteStart + len(movedLines)]

    def removeSectionItem(self, index: int) -> None:
        item = self.getSectionItems()[index]
        del self._lines[item.lineIndex : item.lineIndex + item.numberOfLines]

    def replaceIncludeLine(self, lineIndex: int, include: DdckInclude) -> None:
        """Replaces the ddck on the given line (in or outside of a block),
        keeping the line's comment."""
        originalLine = self._lines[lineIndex]
        originalInclude = DdckInclude.tryParse(
            originalLine, self.getPathVariables().keys()
        )
        if originalInclude is None:
            raise RunConfigError(
                f"Line {lineIndex + 1} doesn't include a ddck."
            )
        if originalInclude == include:
            return
        comment = originalLine[len(_stripComment(originalLine)) :]
        newLine = include.toLine()
        if comment:
            newLine += " " + comment
        self._lines[lineIndex] = newLine

    def replaceSectionInclude(self, index: int, include: DdckInclude) -> None:
        """Changes the ddck (outside of blocks) of the item, keeping the
        lines following it and the include line's comment."""
        item = self.getSectionItems()[index]
        if item.entry is None:
            raise RunConfigError("The item is a component block.")

        originalLine = self._lines[item.lineIndex]
        comment = originalLine[len(_stripComment(originalLine)) :]
        newLine = include.toLine()
        if include == item.entry.include:
            newLine = originalLine
        elif comment:
            newLine += " " + comment
        self._lines[item.lineIndex] = newLine

    # Identifiers prefixed with a component's name

    def findPrefixedIdentifierLines(
        self, oldName: str, newName: str
    ) -> _tp.Sequence[PrefixedIdentifiersLine]:
        """Lines (not ddck includes, `string`s or comments) using
        identifiers that start with `oldName` (and are longer) - as pytrnsys
        prefixes the local variables of a component's ddcks with its name
        (e.g. `Collc0` for `c0` of `Coll`). Other identifiers can start with
        the name too (e.g. `Collector`): the user decides. `isInComponentBlock` refers to the
        block of `newName` (call this after `renameComponent`)."""
        regex = _re.compile(rf"(?<![\w$:]){_re.escape(oldName)}\w+")
        pathVariableNames = self.getPathVariables().keys()
        block = self._findBlock(newName)

        result = []
        for index, line in enumerate(self._lines):
            code = _stripComment(line)
            isSkipped = (
                not code.strip()
                or _STRING_REGEX.match(code)
                or DdckInclude.tryParse(line, pathVariableNames)
                or _BLOCK_BEGIN_REGEX.match(line)
                or _BLOCK_END_REGEX.match(line)
            )
            if isSkipped:
                continue

            identifiers = tuple(m.group(0) for m in regex.finditer(code))
            if not identifiers:
                continue

            newCode = regex.sub(
                lambda m: newName + m.group(0)[len(oldName) :], code
            )
            isInBlock = bool(
                block and block.beginLineIndex < index < block.endLineIndex
            )
            result.append(
                PrefixedIdentifiersLine(
                    index,
                    line,
                    newCode + line[len(code) :],
                    identifiers,
                    isInBlock,
                )
            )
        return result

    def replaceLine(
        self, lineIndex: int, expectedLine: str, newLine: str
    ) -> None:
        """Replaces a line, checking it's still what the caller saw."""
        if self._lines[lineIndex] != expectedLine:
            raise RunConfigError(
                f"Line {lineIndex + 1} changed: `{self._lines[lineIndex]}`."
            )
        self._lines[lineIndex] = newLine

    # Adopting ddcks of existing configs (without blocks)

    def findAdoptableEntries(
        self, componentName: str
    ) -> _tp.Sequence[AdoptableEntry]:
        """ddcks outside component blocks that pytrnsys attributes to the
        component (by their `as` or containing directory), with the lines
        following them (`deck ...`, comments) up to the next blank line or
        ddck. ddcks without a component (no `as`, not in a directory, e.g.
        `COMMON$ head global`) are never adoptable."""
        if not isValidComponentName(componentName):
            return []

        pathVariableNames = self.getPathVariables().keys()
        blocks = self._getBlocks()

        adoptables = []
        for includeLine in self.getIncludeLines():
            if includeLine.blockComponentName is not None:
                continue
            if includeLine.include.componentName != componentName:
                continue

            trailingLines = self._getTrailingLines(
                includeLine.lineIndex, pathVariableNames, blocks
            )
            entry = ComponentEntry(
                includeLine.include,
                tuple(trailingLines),
                self._lines[includeLine.lineIndex],
            )
            adoptables.append(AdoptableEntry(includeLine.lineIndex, entry))

        return adoptables

    def adoptEntries(self, componentName: str) -> int:
        """Moves the adoptable ddcks (see `findAdoptableEntries`) into the
        component's block, which is created where the first of them was if
        it doesn't exist yet. Returns the number of adopted ddcks."""
        adoptables = self.findAdoptableEntries(componentName)
        if not adoptables:
            return 0

        firstLineIndex = adoptables[0].lineIndex
        for adoptable in reversed(adoptables):
            start = adoptable.lineIndex
            del self._lines[start : start + adoptable.numberOfLines]

        adoptedEntries = [a.entry for a in adoptables]

        if self._findBlock(componentName):
            existingEntries = self.getComponentEntries(componentName)
            self.setComponentEntries(
                componentName, [*existingEntries, *adoptedEntries]
            )
        else:
            self._lines[firstLineIndex:firstLineIndex] = [
                _createBlockBeginLine(componentName),
                *(
                    line
                    for entry in adoptedEntries
                    for line in entry.toLines()
                ),
                _createBlockEndLine(componentName),
            ]

        return len(adoptables)

    def _getTrailingLines(
        self,
        includeLineIndex: int,
        pathVariableNames: _cabc.Container[str],
        blocks: _cabc.Sequence[_Block],
    ) -> _tp.Sequence[str]:
        blockMarkerIndices = {b.beginLineIndex for b in blocks} | {
            b.endLineIndex for b in blocks
        }

        trailingLines = []
        for index in range(includeLineIndex + 1, len(self._lines)):
            line = self._lines[index]
            isEndOfEntry = (
                not line.strip()
                or index in blockMarkerIndices
                or DdckInclude.tryParse(line, pathVariableNames) is not None
            )
            if isEndOfEntry:
                break
            trailingLines.append(line)
        return trailingLines

    @staticmethod
    def _renameInclude(
        include: DdckInclude, oldName: str, newName: str
    ) -> DdckInclude:
        alias = newName if include.alias == oldName else include.alias

        relativePath = include.relativePath
        if include.pathVariable == PROJECT_PATH_VARIABLE:
            parts = _pl.PureWindowsPath(relativePath).parts
            if parts and parts[0] == oldName:
                # Keep the separator style of the line.
                separator = "\\" if "\\" in relativePath else "/"
                relativePath = separator.join([newName, *parts[1:]])

        return _dc.replace(include, alias=alias, relativePath=relativePath)

    # Blocks

    def _getBlocks(self) -> _tp.Sequence[_Block]:
        blocks = []
        openName: str | None = None
        openIndex = -1
        for index, line in enumerate(self._lines):
            beginMatch = _BLOCK_BEGIN_REGEX.match(line)
            endMatch = _BLOCK_END_REGEX.match(line)

            if beginMatch:
                if openName is not None:
                    raise RunConfigError(
                        f"Line {index + 1}: block of component `{openName}`"
                        " is not closed before the next one starts."
                    )
                openName = beginMatch.group("name")
                openIndex = index
            elif endMatch:
                endName = endMatch.group("name")
                if openName != endName:
                    raise RunConfigError(
                        f"Line {index + 1}: end of block of component"
                        f" `{endName}` doesn't match its beginning."
                    )
                blocks.append(_Block(openName, openIndex, index))
                openName = None

        if openName is not None:
            raise RunConfigError(
                f"Line {openIndex + 1}: block of component `{openName}` is"
                " never closed."
            )

        names = [b.componentName for b in blocks]
        duplicates = {n for n in names if names.count(n) > 1}
        if duplicates:
            raise RunConfigError(
                "There are several blocks for component(s): "
                + ", ".join(sorted(duplicates))
            )

        return blocks

    def _getBlockContent(
        self, block: _Block
    ) -> _tp.Tuple[_tp.Sequence[str], _tp.Sequence[ComponentEntry]]:
        """The lines before the block's first ddck, and its ddcks, each with
        the (non-ddck) lines following it."""
        pathVariableNames = self.getPathVariables().keys()

        leadingLines: list[str] = []
        entries: list[ComponentEntry] = []
        currentInclude: DdckInclude | None = None
        currentLine = ""
        currentTrailingLines: list[str] = []

        for line in self._lines[block.beginLineIndex + 1 : block.endLineIndex]:
            include = DdckInclude.tryParse(line, pathVariableNames)
            if include:
                if currentInclude:
                    entries.append(
                        ComponentEntry(
                            currentInclude,
                            tuple(currentTrailingLines),
                            currentLine,
                        )
                    )
                currentInclude = include
                currentLine = line
                currentTrailingLines = []
            elif currentInclude:
                currentTrailingLines.append(line)
            else:
                leadingLines.append(line)

        if currentInclude:
            entries.append(
                ComponentEntry(
                    currentInclude, tuple(currentTrailingLines), currentLine
                )
            )

        return leadingLines, entries

    def _findBlock(self, componentName: str) -> _Block | None:
        for block in self._getBlocks():
            if block.componentName == componentName:
                return block
        return None

    @staticmethod
    def _findBlockContaining(
        blocks: _cabc.Sequence[_Block], lineIndex: int
    ) -> _Block | None:
        for block in blocks:
            if block.beginLineIndex < lineIndex < block.endLineIndex:
                return block
        return None

    def _getBlockInsertionIndex(self) -> int:
        """New blocks go before the `end` ddck (which must stay last), else
        after the last include or block, else after the "USED DDCKs" marker,
        else at the end of the file."""
        includeLines = self.getIncludeLines()

        for includeLine in includeLines:
            if includeLine.blockComponentName is not None:
                continue
            name = _pl.PureWindowsPath(includeLine.include.relativePath).name
            if name.lower() == "end":
                return includeLine.lineIndex

        lastIndex = max(
            [il.lineIndex for il in includeLines]
            + [b.endLineIndex for b in self._getBlocks()],
            default=None,
        )
        if lastIndex is not None:
            return lastIndex + 1

        for index, line in enumerate(self._lines):
            if _USED_DDCKS_MARKER in line:
                return index + 1

        return len(self._lines)
