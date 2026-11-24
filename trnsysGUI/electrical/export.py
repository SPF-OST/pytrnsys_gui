"""Placeholders and `electrical.ddck` of the electrical layer.

Each connected terminal `T` of a component gets two placeholders in `DdckPlaceHolderValues.json`:

- `@pel(T)`: the power of the connection at `T` [kW], positive in the direction of its arrow. Exactly one of the
  two components it connects must define it (e.g. `@pel(Out) = -@pelsign(Out)*PelProduced`), the other reads it.
- `@pelsign(T)`: `(1)` if a positive connection power flows into the component at `T`, `(-1)` if it flows out.
  So `@pelsign(T)*@pel(T)` is always the power going into the component at `T`.

A component with at least one electrical connection gets placeholders for all its terminals: an unconnected
terminal gets `@pel = 0`, so a ddck can read all its terminals (e.g. D1..D10); it must not assign to it.
"""

import collections.abc as _cabc
import typing as _tp

import trnsysGUI.BlockItem as _bi
import trnsysGUI.electrical.connection as _econn
import trnsysGUI.electrical.terminals as _et

PlaceHoldersByTerminalName = dict[str, dict[str, str]]


def getPlaceholders(
    trnsysObjects: _cabc.Sequence[_tp.Any],
) -> dict[str, PlaceHoldersByTerminalName]:
    placeholdersByComponent: dict[str, PlaceHoldersByTerminalName] = {}
    for blockItem in trnsysObjects:
        if not isinstance(blockItem, _bi.BlockItem):
            continue

        terminals = _et.getTerminals(blockItem)
        if not any(t.connections for t in terminals):
            # not part of the electrical layer: no electrical placeholders
            continue

        placeholdersByTerminal: PlaceHoldersByTerminalName = {}
        for terminal in terminals:
            if not terminal.connections:
                # unconnected: no power, so that a generic ddck can read all its terminals (e.g. D1..D10)
                placeholdersByTerminal[terminal.name] = {
                    "@pel": "0",
                    "@pelsign": "(1)",
                }
                continue
            connection = terminal.connections[0]
            sign = "(1)" if connection.toTerminal is terminal else "(-1)"
            placeholdersByTerminal[terminal.name] = {
                "@pel": connection.variableName,
                "@pelsign": sign,
            }

        placeholdersByComponent[blockItem.displayName] = placeholdersByTerminal

    return placeholdersByComponent


def addPlaceholders(
    placeholders: _cabc.MutableMapping[str, _tp.Any],
    trnsysObjects: _cabc.Sequence[_tp.Any],
) -> None:
    for componentName, placeholdersByTerminal in getPlaceholders(
        trnsysObjects
    ).items():
        existing = dict(placeholders.get(componentName, {}))
        existing.update(placeholdersByTerminal)
        placeholders[componentName] = existing


def createElectricalDdck(editor, projectName: str) -> str:
    connections = sorted(editor.electricalConnections, key=lambda c: c.name)

    width = max([len(c.variableName) for c in connections] + [8])
    connectionLines = "\n".join(
        f"** {c.variableName:<{width}}  {c.fromTerminal.qualifiedName} -> {c.toTerminal.qualifiedName}"
        for c in connections
    )

    header = f"""\
*******************************
**BEGIN electrical.ddck
*******************************

*****************************************
** Contact person : pytrnsys GUI (generated, do not edit: export it again from the diagram)
** Description    : electrical connections of the diagram. Each connection has a power Pel<Name> [kW],
**                  positive in the direction of its arrow. It is defined by the ddck of one of the two
**                  components it connects (placeholders @pel and @pelsign) and read by the other one.
*****************************************

** Connections (variable, from -> to):
{connectionLines or "** (none)"}
"""

    if not connections:
        return (
            header
            + "\n*******************************\n**END electrical.ddck\n*******************************\n"
        )

    variableNames = [c.variableName for c in connections]
    formattedVariables = "\n".join(
        " ".join(variableNames[i : i + 8])
        for i in range(0, len(variableNames), 8)
    )

    printer = f"""
*****************************************
** Time step printer of the electrical powers [kW]
*****************************************
CONSTANTS 1
unitPrintElectrical = 71

ASSIGN {projectName}_Pel.prt unitPrintElectrical

UNIT 72 TYPE 25
PARAMETERS 10
dtSim                 ! 1 Printing interval
START                 ! 2 Start time
STOP                  ! 3 Stop time
unitPrintElectrical   ! 4 Logical unit
0                     ! 5 Units printing mode
0                     ! 6 Relative or absolute start time
-1                    ! 7 Overwrite or Append
-1                    ! 8 Print header
0                     ! 9 Delimiter
1                     ! 10 Print labels
INPUTS {len(variableNames)}
{formattedVariables}
***
{formattedVariables}

*******************************
**END electrical.ddck
*******************************
"""
    return header + printer
