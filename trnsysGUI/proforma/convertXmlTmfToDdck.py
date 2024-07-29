import collections.abc as _cabc
import dataclasses as _dc
import pathlib as _pl
import typing as _tp
import xml.etree.ElementTree as _etree

import jinja2 as _jj
import xmlschema as _xs

import pytrnsys.utils.result as _res
import trnsysGUI.common.cancelled as _cancel
import trnsysGUI.proforma.dialogs.editHydraulicConnectionsDialog as _ehcd
from . import createModelConnections as _cmcs
from . import models as _models

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


def convertXmltmfToDdck(
    xmlTmfFilePath: _pl.Path,
    suggestedHydraulicConnections: _cabc.Sequence[_models.Connection] | None,
    ddckFilePath: _pl.Path,
) -> _cancel.MaybeCancelled[_res.Result[None]]:
    xmlTmfContent = xmlTmfFilePath.read_text(encoding="utf8")
    maybeCancelled = convertXmlTmfStringToDdck(xmlTmfContent, suggestedHydraulicConnections)
    if _cancel.isCancelled(maybeCancelled):
        return _cancel.CANCELLED
    result = _cancel.value(maybeCancelled)
    if _res.isError(result):
        return _res.error(result).withContext(f"Converting proforma `{xmlTmfFilePath}`")
    ddckContent = _res.value(result)

    assert isinstance(ddckContent, str)
    ddckFilePath.write_text(ddckContent, encoding="utf8")

    return None


_StringMapping = _tp.Mapping[str, _tp.Any]


@_dc.dataclass
class _HydraulicConnectionsData:
    name: str | None
    portName: str
    stringConstants: _models.VariableStringConstants

    @property
    def variableName(self) -> str:
        capitalizedPortName = self.portName.capitalize()
        return f":{self.stringConstants.variableNamePrefix}{capitalizedPortName}"

    @property
    def rhs(self) -> str:
        return f"@{self.stringConstants.propertyName}({self.portName})"

    @staticmethod
    def createForTemperature(connectionName: str | None, portName: str) -> "_HydraulicConnectionsData":
        return _HydraulicConnectionsData(connectionName, portName, _models.AllVariableStringConstants.TEMPERATURE)

    @staticmethod
    def createForReverseTemperature(connectionName: str | None, portName: str):
        return _HydraulicConnectionsData(
            connectionName, portName, _models.AllVariableStringConstants.REVERSE_TEMPERATURE
        )

    @staticmethod
    def createForMassFlowRate(connectionName: str | None, portName: str) -> "_HydraulicConnectionsData":
        return _HydraulicConnectionsData(connectionName, portName, _models.AllVariableStringConstants.MASS_FLOW_RATE)

    @staticmethod
    def createForFluidHeatCapacity(connectionName: str | None, portName: str) -> "_HydraulicConnectionsData":
        return _HydraulicConnectionsData(connectionName, portName, _models.AllVariableStringConstants.HEAT_CAPACITY)

    @staticmethod
    def createForFluidDensity(connectionName: str | None, portName: str) -> "_HydraulicConnectionsData":
        return _HydraulicConnectionsData(connectionName, portName, _models.AllVariableStringConstants.DENSITY)


@_dc.dataclass
class _VariableWithHydraulicConnectionsData(_models.Variable):
    hydraulicConnectionsData: _HydraulicConnectionsData | None

    @staticmethod
    def fromVariable(
        variable: _models.Variable, connectionsDataByOrder: _tp.Mapping[int, _HydraulicConnectionsData]
    ) -> "_VariableWithHydraulicConnectionsData":
        hydraulicConnectionsData = connectionsDataByOrder.get(variable.order)
        variableWithData = _VariableWithHydraulicConnectionsData(
            **vars(variable), hydraulicConnectionsData=hydraulicConnectionsData
        )
        return variableWithData


def _createProcessedVariables(
    variables: _cabc.Sequence[_models.Variable],
    connectionsDataByOrder: _tp.Mapping[int, _HydraulicConnectionsData],
) -> _cabc.Sequence[_VariableWithHydraulicConnectionsData]:

    processedVariables = [
        _VariableWithHydraulicConnectionsData.fromVariable(v, connectionsDataByOrder) for v in variables
    ]

    return processedVariables


def _createVariablesByRole(
    serializedVariables: _cabc.Sequence[_StringMapping],
) -> _models.VariablesByRole:
    def getOrder(serializedVariable: _StringMapping) -> int:
        return serializedVariable["order"]

    sortedSerializedVariables = sorted(serializedVariables, key=getOrder)

    parameterVariables = _createVariablesForRole("parameter", sortedSerializedVariables)
    inputVariables = _createVariablesForRole("input", sortedSerializedVariables)
    outputVariables = _createVariablesForRole("output", sortedSerializedVariables)

    return _models.VariablesByRole(parameterVariables, inputVariables, outputVariables)


_Role = _tp.Literal["parameter", "input", "output"]


def _createVariablesForRole(
    role: _Role, sortedSerializedVariables: _cabc.Sequence[_StringMapping]
) -> _cabc.Sequence[_models.Variable]:
    sortedSerializedVariablesForRole = _getSerializedVariablesWithRole(role, sortedSerializedVariables)

    variables = []
    for roleOrder, serializedVariable in enumerate(sortedSerializedVariablesForRole, start=1):
        order = serializedVariable["order"]
        bounds = _getBounds(serializedVariable)
        variable = _models.Variable(
            serializedVariable["name"],
            order,
            role,
            roleOrder,
            serializedVariable["unit"],
            bounds,
            serializedVariable["default"],
        )
        variables.append(variable)

    return variables


def convertXmlTmfStringToDdck(
    xmlTmfContent: str, suggestedHydraulicConnections: _cabc.Sequence[_models.Connection] | None
) -> _cancel.MaybeCancelled[_res.Result[str]]:
    schema = _xs.XMLSchema11(_SCHEMA_FILE_PATH)

    try:
        schema.validate(xmlTmfContent)
    except (_etree.ParseError, _xs.XMLSchemaException) as error:
        return _res.Error(f"Error reading or validating the proforma file: {error}")

    proforma: _tp.Any = schema.to_dict(xmlTmfContent)

    serializedVariables = proforma["variables"]["variable"]
    variablesByRole = _createVariablesByRole(serializedVariables)

    if "hydraulicConnections" in proforma:
        serializedHydraulicConnections = proforma["hydraulicConnections"]["connection"]
        result = _cmcs.createModelConnectionsFromProforma(serializedHydraulicConnections, variablesByRole.allVariables)
        if _res.isError(result):
            return _res.error(result)
        hydraulicConnections = _res.value(result)
    elif suggestedHydraulicConnections is not None:
        hydraulicConnections = suggestedHydraulicConnections
    else:
        hydraulicConnections = []

    if hydraulicConnections:
        maybeCancelled = _ehcd.EditHydraulicConnectionsDialog.showDialogAndGetResults(
            hydraulicConnections, variablesByRole
        )
        if _cancel.isCancelled(maybeCancelled):
            return _cancel.CANCELLED
        hydraulicConnections = _cancel.value(maybeCancelled)

    trnsysType = proforma["type"]

    return _convertXmlTmfStringToDdck(trnsysType, hydraulicConnections, variablesByRole)


def _convertXmlTmfStringToDdck(
    trnsysType: int, hydraulicConnections: _cabc.Sequence[_models.Connection], variablesByRole: _models.VariablesByRole
) -> str:
    connectionsDataByOrder = _createHydraulicConnectionDataByOrder(hydraulicConnections)
    parameters = _createProcessedVariables(variablesByRole.parameters, connectionsDataByOrder)
    inputs = _createProcessedVariables(variablesByRole.inputs, connectionsDataByOrder)
    outputs = _createProcessedVariables(variablesByRole.outputs, connectionsDataByOrder)
    ddckContent = _JINJA_TEMPLATE.render(type=trnsysType, parameters=parameters, inputs=inputs, outputs=outputs)
    return ddckContent


def _createHydraulicConnectionDataByOrder(
    hydraulicConnections: _cabc.Sequence[_models.Connection],
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


def _getHydraulicConnectionDataByOrderForFluid(
    connectionName: str | None, hydraulicConnection: _models.Connection, inputPort: _models.InputPort
) -> dict[int, _HydraulicConnectionsData]:
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
    connectionName: str | None, inputPort: _models.InputPort
) -> dict[int, _HydraulicConnectionsData]:
    portName = inputPort.name

    mfrOrder = inputPort.massFlowRateSet.order
    tempOrder = inputPort.temperatureSet.order

    hydraulicConnectionData = {
        mfrOrder: _HydraulicConnectionsData.createForMassFlowRate(connectionName, portName),
        tempOrder: _HydraulicConnectionsData.createForTemperature(connectionName, portName),
    }

    return hydraulicConnectionData


def _getHydraulicConnectionDataByOrderForOutput(
    connectionName: str | None,
    outputPort: _models.OutputPort,
) -> dict[int, _HydraulicConnectionsData]:
    portName = outputPort.name
    tempOrder = outputPort.temperatureSet.order
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


def _getSerializedVariablesWithRole(
    role: _Role, variables: _tp.Sequence[_StringMapping]
) -> _tp.Sequence[_StringMapping]:
    return [v for v in variables if v["role"] == role]


def _getBounds(variable: _StringMapping) -> str:
    leftBracket, rightBracket = [b.strip() for b in variable["boundaries"].split(";")]
    minimum = variable["min"]
    maximum = variable["max"]
    bounds = f"{leftBracket}{minimum},{maximum}{rightBracket}"
    return bounds
