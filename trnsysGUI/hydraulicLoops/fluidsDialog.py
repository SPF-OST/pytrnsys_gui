"""Window to manage the fluids of a diagram: the built-in `water` and `brine`, fluids from the library
(fluidLibrary.py) and own fluids. The fluids are saved in the diagram and exported to hydraulic.ddck
(`F<name>Rho`, `F<name>Cp`, `F<name>Lambda`, `F<name>Mu`, ... see Export.exportFluids).
"""

from __future__ import annotations

import re as _re
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtWidgets as _qtw

from . import _serialization as _ser
from . import fluidLibrary as _lib
from . import model as _model

_VALID_NAME = _re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
_NAME, _CP, _RHO, _LAMBDA, _MU, _USED, _DESCRIPTION = range(7)
_HEADERS = [
    "Name",
    "cp [J/(kg K)]",
    "rho [kg/m3]",
    "lambda [W/(m K)]",
    "mu [mPa s]",
    "Used by loops",
    "Description",
]
_MPAS_PER_PAS = 1000.0  # viscosity shown in mPa s (= cP), stored in Pa s


class FluidsDialog(_qtw.QDialog):
    def __init__(
        self,
        fluids: _model.Fluids,
        hydraulicLoops: _tp.Sequence[_model.HydraulicLoop],
        parent: _qtw.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Fluids of the diagram")
        self.resize(1050, 380)

        self._fluids = fluids
        self._hydraulicLoops = hydraulicLoops

        self._table = _qtw.QTableWidget(0, len(_HEADERS))
        self._table.setHorizontalHeaderLabels(_HEADERS)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setVisible(False)
        for fluid in fluids.fluids:
            self._addRow(fluid)

        self._libraryComboBox = _qtw.QComboBox()
        for libraryFluid in _lib.LIBRARY_FLUIDS:
            self._libraryComboBox.addItem(
                f"{libraryFluid.name} - {libraryFluid.description}",
                userData=libraryFluid,
            )
        addFromLibraryButton = _qtw.QPushButton("Add from library")
        addFromLibraryButton.clicked.connect(self._addFromLibrary)
        newButton = _qtw.QPushButton("New fluid")
        newButton.clicked.connect(self._addNew)
        removeButton = _qtw.QPushButton("Remove")
        removeButton.clicked.connect(self._removeSelected)

        buttonsLayout = _qtw.QHBoxLayout()
        buttonsLayout.addWidget(self._libraryComboBox, 1)
        buttonsLayout.addWidget(addFromLibraryButton)
        buttonsLayout.addSpacing(20)
        buttonsLayout.addWidget(newButton)
        buttonsLayout.addWidget(removeButton)

        okCancel = _qtw.QDialogButtonBox(
            _qtw.QDialogButtonBox.Ok | _qtw.QDialogButtonBox.Cancel
        )
        okCancel.accepted.connect(self.accept)
        okCancel.rejected.connect(self.reject)

        note = _qtw.QLabel(
            "Properties are constants (one value per fluid), exported to hydraulic.ddck as F<name>Rho, "
            "F<name>Cp (kJ/(kg K)), F<name>CpSI, F<name>Lambda, F<name>LambdaKJh, F<name>Mu (Pa s), "
            "F<name>MuKgmh.\nwater and brine are built in (their names can't be changed); a fluid used by a loop "
            "can't be removed or renamed."
        )
        note.setWordWrap(True)

        layout = _qtw.QVBoxLayout(self)
        layout.addWidget(note)
        layout.addWidget(self._table)
        layout.addLayout(buttonsLayout)
        layout.addWidget(okCancel)

        self._table.resizeColumnsToContents()

    # --- rows ------------------------------------------------------------------------------
    def _usedBy(self, fluidName: str) -> list[str]:
        return [
            l.name.value
            for l in self._hydraulicLoops
            if l.fluid.name == fluidName
        ]

    def _addRow(self, fluid: _ser.Fluid, description: str = "") -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)

        isBuiltIn = fluid.name in _lib.BUILT_IN_DESCRIPTIONS
        usedBy = self._usedBy(fluid.name)
        description = _lib.BUILT_IN_DESCRIPTIONS.get(fluid.name, description)

        cells: list[tuple[str, bool, _tp.Any]] = [
            (fluid.name, not isBuiltIn and not usedBy, None),
            *_valueCell(fluid.specificHeatCapacityInJPerKgK),
            *_valueCell(fluid.densityInKgPerM3),
            (f"{fluid.thermalConductivityInWPerMK or 0:g}", True, None),
            (
                f"{(fluid.dynamicViscosityInPaS or 0) * _MPAS_PER_PAS:g}",
                True,
                None,
            ),
            (", ".join(usedBy), False, None),
            (description, False, None),
        ]
        for column, (text, isEditable, data) in enumerate(cells):
            item = _qtw.QTableWidgetItem(text)
            if not isEditable:
                item.setFlags(item.flags() & ~_qtc.Qt.ItemIsEditable)
            item.setData(_qtc.Qt.UserRole, data)
            self._table.setItem(row, column, item)
        self._table.resizeColumnToContents(_NAME)

    def _cell(self, row: int, column: int) -> _qtw.QTableWidgetItem:
        item = self._table.item(row, column)
        assert item is not None
        return item

    def _names(self) -> list[str]:
        return [
            self._cell(r, _NAME).text().strip()
            for r in range(self._table.rowCount())
        ]

    def _addFromLibrary(self) -> None:
        libraryFluid = self._libraryComboBox.currentData()
        if libraryFluid.name.lower() in {n.lower() for n in self._names()}:
            _qtw.QMessageBox.information(
                self,
                "Fluid exists",
                f"The diagram already has a fluid called `{libraryFluid.name}`.",
            )
            return
        self._addRow(libraryFluid.createFluid(), libraryFluid.description)

    def _addNew(self) -> None:
        names = {n.lower() for n in self._names()}
        suffix = 1
        while f"fluid{suffix}" in names:
            suffix += 1
        water = _lib.WATER
        self._addRow(
            _ser.Fluid(
                f"fluid{suffix}",
                specificHeatCapacityInJPerKgK=water.specificHeatCapacityInJPerKgK,
                densityInKgPerM3=water.densityInKgPerM3,
                thermalConductivityInWPerMK=water.thermalConductivityInWPerMK,
                dynamicViscosityInPaS=water.dynamicViscosityInPaS,
            ),
            "own fluid",
        )
        self._table.editItem(self._cell(self._table.rowCount() - 1, 0))

    def _removeSelected(self) -> None:
        rows = sorted(
            {i.row() for i in self._table.selectedIndexes()}, reverse=True
        )
        for row in rows:
            name = self._cell(row, _NAME).text()
            if name in _lib.BUILT_IN_DESCRIPTIONS or self._usedBy(name):
                _qtw.QMessageBox.information(
                    self,
                    "Fluid can't be removed",
                    f"`{name}` is built in or used by a hydraulic loop.",
                )
                continue
            self._table.removeRow(row)

    # --- apply ------------------------------------------------------------------------------
    def accept(self) -> None:  # pylint: disable=invalid-name
        result = self._readFluids()
        if isinstance(result, str):
            _qtw.QMessageBox.warning(self, "Invalid fluids", result)
            return

        self._fluids.fluids = sorted(result, key=lambda f: f.name)
        # the loops keep their fluid by name (new values of an edited fluid)
        for loop in self._hydraulicLoops:
            newFluid = self._fluids.getFluid(loop.fluid.name)
            assert newFluid
            loop.fluid = newFluid
        super().accept()

    def _readFluids(self) -> list[_ser.Fluid] | str:
        fluids: list[_ser.Fluid] = []
        seen: set[str] = set()
        for row in range(self._table.rowCount()):
            name = self._cell(row, _NAME).text().strip()
            if not _VALID_NAME.match(name):
                return f"`{name}`: a name must start with a letter and contain only letters, digits and `_`."
            if name.lower() in seen:
                return f"The name `{name}` is used twice (names are case insensitive)."
            seen.add(name.lower())
            try:
                cp = self._readValue(row, _CP)
                rho = self._readValue(row, _RHO)
                conductivity = float(self._cell(row, _LAMBDA).text())
                viscosity = float(self._cell(row, _MU).text()) / _MPAS_PER_PAS
            except ValueError:
                return f"`{name}`: the properties must be numbers."
            values = [conductivity, viscosity] + [
                v for v in (cp, rho) if isinstance(v, float)
            ]
            if any(v <= 0 for v in values):
                return f"`{name}`: the properties must be positive."
            fluids.append(
                _ser.Fluid(
                    name,
                    specificHeatCapacityInJPerKgK=cp,
                    densityInKgPerM3=rho,
                    thermalConductivityInWPerMK=conductivity,
                    dynamicViscosityInPaS=viscosity,
                )
            )
        return fluids

    def _readValue(self, row: int, column: int) -> float | _ser.Variable:
        """A number, or the head.ddck variable of a diagram saved before (shown read-only)."""
        variable = self._cell(row, column).data(_qtc.Qt.UserRole)
        if isinstance(variable, _ser.Variable):
            return variable
        return float(self._cell(row, column).text())

    @classmethod
    def showDialog(
        cls,
        fluids: _model.Fluids,
        hydraulicLoops: _tp.Sequence[_model.HydraulicLoop],
        parent: _qtw.QWidget | None = None,
    ) -> bool:
        return (
            cls(fluids, hydraulicLoops, parent).exec() == _qtw.QDialog.Accepted
        )


def _valueCell(
    value: float | _ser.Variable,
) -> list[tuple[str, bool, _tp.Any]]:
    if isinstance(value, _ser.Variable):
        return [(value.name, False, value)]
    return [(f"{value:g}", True, None)]
