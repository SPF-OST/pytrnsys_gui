import collections.abc as _cabc
import dataclasses as _dc
import pathlib as _pl
import typing as _tp

import jinja2 as _jj
import xmlschema as _xml

from . import modelConnection as _mc
from . import createModelConnections as _cmcs
from ._dialogs import convertDialog as _cd

_CONTAINING_DIR_PATH = _pl.Path(__file__).parent
_SCHEMA_FILE_PATH = _CONTAINING_DIR_PATH / "xmltmf.xsd"


def _createDdckJinjaTemplate() -> _jj.Template:
    environment = _jj.Environment(
        loader=_jj.PackageLoader(__name__),
        autoescape=_jj.select_autoescape(),
        lstrip_blocks=True,
        undefined=_jj.StrictUndefined,
    )
    template = environment.get_template("ddck.jinja")
    return template


_JINJA_TEMPLATE = _createDdckJinjaTemplate()


def convertXmltmfToDdck(xmlTmfFilePath: _pl.Path, ddckFilePath: _pl.Path) -> None:
    xmlTmfContent = xmlTmfFilePath.read_text(encoding="utf8")
    try:
        ddckContent = convertXmlTmfStringToDdck(xmlTmfContent)
    except ValueError as exception:
        raise ValueError(f"Error parsing {xmlTmfFilePath}") from exception

    ddckFilePath.write_text(ddckContent, encoding="utf8")


_StringMapping = _tp.Mapping[str, _tp.Any]
_Variable = _StringMapping


@_dc.dataclass
class _HydraulicConnectionsData:
    name: str | None
    portName: str
    propertyName: str
    variableNamePrefix: str | None

    @property
    def variableName(self) -> str:
        capitalizedPortName = self.portName.capitalize()
        return f":{self.variableNamePrefix}{capitalizedPortName}"

    @property
    def rhs(self) -> str:
        return f"@{self.propertyName}({self.portName})"

    @staticmethod
    def createForTemperature(connectionName: str | None, portName: str) -> "_HydraulicConnectionsData":
        return _HydraulicConnectionsData(connectionName, portName, "temp", "T")

    @staticmethod
    def createForReverseTemperature(connectionName: str | None, portName: str):
        return _HydraulicConnectionsData(connectionName, portName, "revtemp", None)

    @staticmethod
    def createForMassFlowRate(connectionName: str | None, portName: str) -> "_HydraulicConnectionsData":
        return _HydraulicConnectionsData(connectionName, portName, "mfr", "M")

    @staticmethod
    def createForFluidHeatCapacity(connectionName: str | None, portName: str) -> "_HydraulicConnectionsData":
        return _HydraulicConnectionsData(connectionName, portName, "cp", "Cp")

    @staticmethod
    def createForFluidDensity(connectionName: str | None, portName: str) -> "_HydraulicConnectionsData":
        return _HydraulicConnectionsData(connectionName, portName, "rho", "Rho")


@_dc.dataclass
class _ProcessedVariable:
    tmfName: str
    hydraulicConnectionsData: _tp.Optional[_HydraulicConnectionsData]
    roleOrder: int
    unit: str
    bounds: str
    defaultValue: _tp.Union[float, int]


def _createProcessedVariables(
    role: str,
    variables: _tp.Sequence[_StringMapping],
    connectionsDataByOrder: _tp.Mapping[int, _HydraulicConnectionsData],
) -> _tp.Sequence[_ProcessedVariable]:
    variables = _getVariablesWithRole(role, variables)
    sortedVariables = sorted(variables, key=lambda v: v["order"])

    processedVariables = []
    for roleOrder, variable in enumerate(sortedVariables, start=1):
        order = variable["order"]
        hydraulicConnectionsData = connectionsDataByOrder.get(order)
        bounds = _getBounds(variable)
        processedVariable = _ProcessedVariable(
            variable["name"], hydraulicConnectionsData, roleOrder, variable["unit"], bounds, variable["default"]
        )
        processedVariables.append(processedVariable)

    return processedVariables


def convertXmlTmfStringToDdck(
    xmlTmfContent: str, suggestedHydraulicConnections: _cabc.Set[_mc.Connection] | None = None
) -> str:
    schema = _xml.XMLSchema11(_SCHEMA_FILE_PATH)

    try:
        schema.validate(xmlTmfContent)
    except _xml.XMLSchemaValidationError as validationError:
        raise ValueError("Failed to validate schema.") from validationError

    proforma: _tp.Any = schema.to_dict(xmlTmfContent)

    variables = proforma["variables"]["variable"]

    if "hydraulicConnections" in proforma:
        serializedHydraulicConnections = proforma["hydraulicConnections"]["connection"]
        hydraulicConnections = _cmcs.createModelConnectionsFromProforma(serializedHydraulicConnections, variables)
    elif suggestedHydraulicConnections is not None:
        hydraulicConnections = suggestedHydraulicConnections
    else:
        hydraulicConnections = []

    connectionsDataByOrder = _createHydraulicConnectionDataByOrder(hydraulicConnections)

    parameters = _createProcessedVariables("parameter", variables, connectionsDataByOrder)
    inputs = _createProcessedVariables("input", variables, connectionsDataByOrder)
    outputs = _createProcessedVariables("output", variables, connectionsDataByOrder)

    ddckContent = _JINJA_TEMPLATE.render(type=proforma["type"], parameters=parameters, inputs=inputs, outputs=outputs)

    return ddckContent


def _createHydraulicConnectionDataByOrder(
    hydraulicConnections: _cabc.Set[_mc.Connection],
) -> _cabc.Mapping[int, _HydraulicConnectionsData]:
    hydraulicConnectionDataByOrder: dict[int, _HydraulicConnectionsData] = {}
    for hydraulicConnection in hydraulicConnections:
        connectionName = hydraulicConnection.name
        inputPort = hydraulicConnection.inputPort
        dataByOrderForFluid = _getHydraulicConnectionDataByOrderForFluid(connectionName, hydraulicConnection, inputPort)

        dataByOrderForInput = _getHydraulicConnectionDataByOrderForInput(connectionName, inputPort)
        dataByOrderForOutput = _getHydraulicConnectionDataByOrderForOutput(
            connectionName, hydraulicConnection.outputPort
        )
        hydraulicConnectionDataByOrder |= dataByOrderForFluid | dataByOrderForInput | dataByOrderForOutput

    return hydraulicConnectionDataByOrder


def _getHydraulicConnectionDataByOrderForFluid(connectionName, hydraulicConnection, inputPort):
    dataByOrderForFluid = {}
    heatCapacityVariable = hydraulicConnection.fluid.heatCapacity
    if heatCapacityVariable:
        dataByOrderForFluid[heatCapacityVariable.order] = _HydraulicConnectionsData.createForFluidHeatCapacity(
            connectionName, inputPort.name
        )
    densityVariable = hydraulicConnection.fluid.density
    if densityVariable:
        dataByOrderForFluid[densityVariable.order] = _HydraulicConnectionsData.createForFluidDensity(
            connectionName, inputPort.name
        )
    return dataByOrderForFluid


def _getHydraulicConnectionDataByOrderForInput(
    connectionName: str, inputPort: _mc.InputPort
) -> dict[int, _HydraulicConnectionsData]:
    portName = inputPort.name
    mfrOrder = inputPort.massFlowRate.order
    tempOrder = inputPort.temperature.order

    hydraulicConnectionData = {
        mfrOrder: _HydraulicConnectionsData.createForMassFlowRate(connectionName, portName),
        tempOrder: _HydraulicConnectionsData.createForTemperature(connectionName, portName),
    }

    return hydraulicConnectionData


def _getHydraulicConnectionDataByOrderForOutput(
    connectionName: str,
    outputPort: _mc.OutputPort,
) -> _tp.Mapping[int, _HydraulicConnectionsData]:
    portName = outputPort.name
    tempOrder = outputPort.temperature.order
    revTempOrder = outputPort.reverseTemperature.order if outputPort.reverseTemperature else None

    hydraulicConnectionData = {
        tempOrder: _HydraulicConnectionsData.createForTemperature(connectionName, portName),
    }

    if revTempOrder is not None:
        hydraulicConnectionData[revTempOrder] = _HydraulicConnectionsData.createForReverseTemperature(
            connectionName, portName
        )

    return hydraulicConnectionData


def _getOrder(variableReference: _StringMapping) -> int:
    return variableReference["variableReference"]["order"]


def _getVariablesWithRole(role: str, variables: _tp.Sequence[_StringMapping]) -> _tp.Sequence[_StringMapping]:
    return [v for v in variables if v["role"] == role]


def _getBounds(variable: _StringMapping) -> str:
    leftBracket, rightBracket = [b.strip() for b in variable["boundaries"].split(";")]
    minimum = variable["min"]
    maximum = variable["max"]
    bounds = f"{leftBracket}{minimum},{maximum}{rightBracket}"
    return bounds
