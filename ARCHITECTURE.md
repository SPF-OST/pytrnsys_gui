# Architecture notes

## Saved diagrams

1. Diagrams are saved as JSON. Most blocks and connections are written and read by a dataclass model based on
   `pytrnsys.utils.serialization`, e.g. `BlockItemModel`, `ValveModel` or `GenericBlockModel`. Some older blocks
   (e.g. `HeatPump`) still build their dicts by hand.
2. Models are versioned so that older projects still load: each model has a fixed `__version__` UUID. When a
   saved format changes, keep the old model, add a new one with a new UUID, return the old one from
   `getSupersededClass()` and convert it in `upgrade()`. `from_dict` falls back through these versions
   automatically.
3. Block dicts carry the `.__BlockDict__` key and connection dicts the `.__ConnectionDict__` key, so that
   `Decoder` can tell them apart. It also reads `BlockName` and `BlockDisplayName` (`RequiredDecoderFieldsMixin`)
   before any model is involved. For models, the `*UpgradableJsonSchemaMixin*` classes in
   `trnsysGUI/serialization.py` add and remove the key.
4. A new model's first version builds on `BlockItemUpgradableJsonSchemaMixinVersion0` (blocks). For what
   version 0 means and why `__version__` is optional, see `UpgradableJsonSchemaMixinVersion0` in
   `pytrnsys/utils/serialization.py`.
5. Models forbid additional properties. Don't extend one by subclassing its dataclass; see the docstring of
   `UpgradableJsonSchemaMixinVersion0` in `pytrnsys/utils/serialization.py` for why.
6. Annotate model fields with `typing.Optional` and `typing.Union`, not `X | Y`: `dataclasses_jsonschema` doesn't
   support PEP 604 unions, so such a field gets an empty schema (no validation) and every load warns. SonarCloud
   flags the old style; for suppressing that, see "SonarCloud" in `DEVELOPER-README.md`. For replacing the library,
   see #646.
