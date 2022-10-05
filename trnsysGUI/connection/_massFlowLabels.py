def getFormattedMassFlowAndTemperature(massFlow: float, temperature: float) -> str:
    formattedMassFlow = _getFormattedMassFlow(massFlow)
    formattedMassFlowAndTemperature = f"M = {formattedMassFlow} kg/h, T: {temperature:.1f}°C"
    return formattedMassFlowAndTemperature


def _getFormattedMassFlow(massFlow: float) -> str:
    formattedMassFlow = f"{massFlow:,.1f}".replace(",", "'")
    return formattedMassFlow
