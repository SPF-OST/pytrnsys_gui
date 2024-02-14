from __future__ import annotations

import typing as _tp

import trnsysGUI.connection.names as _cnames
import trnsysGUI.names.undo as _nu

if _tp.TYPE_CHECKING:
    import trnsysGUI.connection.connectionBase as _cb
    import trnsysGUI.diagram.Editor as _ed


def reAddConnection(connection: _cb.ConnectionBase) -> None:
    editor: _ed.Editor = connection.parent  # type: ignore[name-defined]
    editor.connectionList.append(connection)
    connection.fromPort.connectionList.append(connection)
    connection.toPort.connectionList.append(connection)


def setDisplayNameForReAdd(connection: _cb.ConnectionBase, undoNamingHelper: _nu.UndoNamingHelper) -> None:
    preferredName = connection.displayName
    alternativeName = _cnames.getDefaultConnectionNameBase(connection.fromPort, connection.toPort)

    displayName = undoNamingHelper.addOrGenerateAndAddAnNonCollidingNameForAdd(
        preferredName,
        _nu.DeleteCommandTargetType.CONNECTION,
        checkDdckFolder=False,
        generatedNameBase=alternativeName,
        firstGeneratedNameHasNumber=False,
    )

    connection.setDisplayName(displayName)
