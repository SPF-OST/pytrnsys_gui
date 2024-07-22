import dataclasses as _dc


@_dc.dataclass
class Connection:
    name: str | None
    inputPort: "InputPort"
    outputPort: "OutputPort"

    @staticmethod
    def createEmpty() -> "Connection":
        return Connection(name=None, inputPort=InputPort.createEmpty(), outputPort=OutputPort.createEmpty())


@_dc.dataclass
class InputPort:
    name: str
    temperature: "Variable" | None
    massFlowRate: "Variable" | None
    fluidDensity: "Variable" | None
    heatCapacity: "Variable" | None

    @staticmethod
    def createEmpty() -> "InputPort":
        return InputPort(None, None, None, None)


@_dc.dataclass
class OutputPort:
    temperature: "Variable" | None
    reverseTemperature: "Variable" | None

    @staticmethod
    def createEmpty() -> "OutputPort":
        return OutputPort(None, None)


@_dc.dataclass
class Variable:
    description: str
    role: str
    roleOrder: int
