import dataclasses as _dc
import typing as _tp

import dataclasses_jsonschema as _dcj


@_dc.dataclass
class Variable(_dcj.JsonSchemaMixin):
    name: str


Value = _tp.Union[Variable, float]  # /NOSONAR


def getConvertedValueOrName(
    valueOrName: Value, conversionFactor=1.0
) -> float | str:
    if isinstance(valueOrName, Variable):
        return valueOrName.name

    value = valueOrName

    return value * conversionFactor
