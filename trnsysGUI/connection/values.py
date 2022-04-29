import dataclasses as _dc
import typing as _tp

import dataclasses_jsonschema as _dcj


@_dc.dataclass
class Variable(_dcj.JsonSchemaMixin):
    name: str


Value = _tp.Union[Variable, float]

DEFAULT_DIAMETER_IN_CM = 2.0
DEFAULT_LENGTH_IN_M = 2.0
DEFAULT_U_VALUE_IN_W_PER_M2_K = 0.8333
