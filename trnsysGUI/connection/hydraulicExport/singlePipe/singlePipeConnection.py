import dataclasses as _dc

import trnsysGUI.connection.hydraulicExport.common as _com


@_dc.dataclass
class SinglePipe:
    inputPort: _com.InputPort
    outputPort: _com.OutputPort


@_dc.dataclass
class ExportHydraulicSinglePipeConnection:
    displayName: str
    pipe: SinglePipe
