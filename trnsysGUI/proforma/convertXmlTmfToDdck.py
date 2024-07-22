import abc as _abc
import dataclasses as _dc
import pathlib as _pl
import typing as _tp

import jinja2 as _jj
import xmlschema as _xml

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
    portName: str
    variableNamePrefix: str
    propertyName: str

    @property
    def variableName(self) -> str:
        capitalizedPortName = self.portName.capitalize()
        return f":{self.variableNamePrefix}{capitalizedPortName}"

    @property
    def rhs(self) -> str:
        return f"@{self.propertyName}({self.portName})"

    @staticmethod
    def createForTemperature(portName: str) -> "_HydraulicConnectionsData":
        return _HydraulicConnectionsData(portName, "T", "temp")

    @staticmethod
    def createForMassFlowRate(portName: str) -> "_HydraulicConnectionsData":
        return _HydraulicConnectionsData(portName, "M", "mfr")

    @staticmethod
    def createForFluidHeatCapacity(portName: str) -> "_HydraulicConnectionsData":
        return _HydraulicConnectionsData(portName, "Cp", "cp")

    @staticmethod
    def createForFluidDensity(portName: str) -> "_HydraulicConnectionsData":
        return _HydraulicConnectionsData(portName, "Rho", "rho")


@_dc.dataclass
class _PortBase(_abc.ABC):
    name: str

    @_abc.abstractmethod
    def getHydraulicConnectionsData(self, variable: _Variable) -> _HydraulicConnectionsData:
        raise NotImplementedError()

    @_abc.abstractmethod
    def getVariableOrders(self) -> _tp.Sequence[int]:
        raise NotImplementedError()


@_dc.dataclass
class _InputPort(_PortBase):
    massFlowRate: _Variable
    temperature: _Variable
    fluidDensity: _tp.Optional[_Variable]
    fluidHeatCapacity: _Variable

    def getHydraulicConnectionsData(self, variable: _Variable) -> _HydraulicConnectionsData:
        if variable is self.massFlowRate:
            return _HydraulicConnectionsData.createForMassFlowRate(self.name)

        if variable is self.temperature:
            return _HydraulicConnectionsData.createForTemperature(self.name)

        if variable is self.fluidDensity:
            return _HydraulicConnectionsData.createForFluidDensity(self.name)

        if variable is self.fluidHeatCapacity:
            return _HydraulicConnectionsData.createForFluidHeatCapacity(self.name)

        raise ValueError(f"Variable `{variable['name']}` is associated with port `{self.name}`.")

    def getVariableOrders(self) -> _tp.Sequence[int]:
        variables = [self.massFlowRate, self.temperature, self.fluidDensity, self.fluidHeatCapacity]
        orders = [v["order"] for v in variables if v]
        return orders


@_dc.dataclass
class _OutputPort(_PortBase):
    temperature: _Variable

    def getHydraulicConnectionsData(self, variable: _Variable) -> _HydraulicConnectionsData:
        if variable is self.temperature:
            return _HydraulicConnectionsData.createForTemperature(self.name)

        raise ValueError(f"Variable `{variable['name']}` is associated with port `{self.name}`.")

    def getVariableOrders(self) -> _tp.Sequence[int]:
        return [(self.temperature["order"])]


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


def convertXmlTmfStringToDdck(xmlTmfContent: str) -> str:
    schema = _xml.XMLSchema11(_SCHEMA_FILE_PATH)

    try:
        schema.validate(xmlTmfContent)
    except _xml.XMLSchemaValidationError as validationError:
        raise ValueError("Failed to validate schema.") from validationError

    proforma: _tp.Any = schema.to_dict(xmlTmfContent)

    variables = proforma["variables"]["variable"]
    hydraulicConnections = proforma["hydraulicConnections"]["connection"]

    connectionsDataByOrder = _createHydraulicConnectionDataByOrder(hydraulicConnections)

    parameters = _createProcessedVariables("parameter", variables, connectionsDataByOrder)
    inputs = _createProcessedVariables("input", variables, connectionsDataByOrder)
    outputs = _createProcessedVariables("output", variables, connectionsDataByOrder)

    ddckContent = _JINJA_TEMPLATE.render(type=proforma["type"], parameters=parameters, inputs=inputs, outputs=outputs)

    return ddckContent


def _createHydraulicConnectionDataByOrder(
    hydraulicConnections: _tp.Sequence[_StringMapping],
) -> _tp.Mapping[int, _HydraulicConnectionsData]:
    hydraulicConnectionDataByOrder: dict[int, _HydraulicConnectionsData] = {}
    for hydraulicConnection in hydraulicConnections:
        dataForInput = _getHydraulicConnectionDataByOrderForInput(hydraulicConnection["input"])
        dataByOrderForOutput = _getHydraulicConnectionDataByOrderForOutput(hydraulicConnection["output"])
        hydraulicConnectionDataByOrder |= dataForInput | dataByOrderForOutput

    return hydraulicConnectionDataByOrder


def _getHydraulicConnectionDataByOrderForInput(inputPort: _StringMapping) -> dict[int, _HydraulicConnectionsData]:
    portName = inputPort["@name"]
    mfrOrder = _getOrder(inputPort["massFlowRate"])
    tempOrder = _getOrder(inputPort["temperature"])

    densityVariableReference = inputPort.get("fluidDensity")
    densityOrder = _getOrder(densityVariableReference) if densityVariableReference else None

    heatCapacityReference = inputPort.get("fluidHeatCapacity")
    heatCapacityOrder = _getOrder(heatCapacityReference) if heatCapacityReference else None

    hydraulicConnectionDataByOrder = {
        mfrOrder: _HydraulicConnectionsData.createForMassFlowRate(portName),
        tempOrder: _HydraulicConnectionsData.createForTemperature(portName),
    }

    if densityOrder:
        hydraulicConnectionDataByOrder[densityOrder] = _HydraulicConnectionsData.createForFluidDensity(portName)

    if heatCapacityOrder:
        hydraulicConnectionDataByOrder[heatCapacityOrder] = _HydraulicConnectionsData.createForFluidHeatCapacity(
            portName
        )

    return hydraulicConnectionDataByOrder


def _getHydraulicConnectionDataByOrderForOutput(
    outputPort: _StringMapping,
) -> _tp.Mapping[int, _HydraulicConnectionsData]:
    portName = outputPort["@name"]
    tempOrder = _getOrder(outputPort["temperature"])
    hydraulicConnectionData = _HydraulicConnectionsData.createForTemperature(portName)

    return {tempOrder: hydraulicConnectionData}


def _getOrder(variableReference: _StringMapping) -> int:
    return variableReference["variableReference"]["order"]


def _getVariable(port: _StringMapping, tag: str, variablesByOrder: _tp.Mapping[int, _StringMapping]) -> _StringMapping:
    variable = _getOptionalVariable(port, tag, variablesByOrder)
    portName = port["@name"]
    assert variable, f"No associated `{tag}` variable for port {portName}"
    return variable


def _getOptionalVariable(
    port, tag: str, variablesByOrder: _tp.Mapping[int, _StringMapping]
) -> _tp.Optional[_StringMapping]:
    child = port.get(tag)
    if not child:
        return None

    order = child["variableReference"]["order"]
    variable = variablesByOrder[order]
    return variable


def _getVariablesWithRole(role: str, variables: _tp.Sequence[_StringMapping]) -> _tp.Sequence[_StringMapping]:
    return [v for v in variables if v["role"] == role]


def _getBounds(variable: _StringMapping) -> str:
    leftBracket, rightBracket = [b.strip() for b in variable["boundaries"].split(";")]
    minimum = variable["min"]
    maximum = variable["max"]
    bounds = f"{leftBracket}{minimum},{maximum}{rightBracket}"
    return bounds
