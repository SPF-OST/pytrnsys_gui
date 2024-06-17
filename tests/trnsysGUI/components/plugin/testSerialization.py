import pathlib as _pl

import yaml as _yaml

import trnsysGUI.components.plugin.serialization as _ser


class TestSerialization:
    def test(self) -> None:
        specFilePath = _pl.Path(__file__).parent / "data" / "thermallyDrivenHeatPump" / "spec.yaml"
        with specFilePath.open() as file:
            data = _yaml.safe_load(file)

        _ = _ser.Specification(**data)
