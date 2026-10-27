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
4. `UpgradableJsonSchemaMixinVersion0` is the base of a model's first versioned version. That version also
   covers the step from unversioned dicts, so it doesn't require `__version__` (but checks it when present).
   A new model's first version builds on it as well (`BlockItemUpgradableJsonSchemaMixinVersion0` for blocks).
   Overriding `_doesRequireVersion` to require the version doesn't work: `from_dict` removes it before
   validating.
5. Models forbid additional properties. Don't extend a model by subclassing its dataclass: `dataclasses_jsonschema`
   combines the schemas with `allOf`, and the base schema forbids the new fields. Declare the fields again
   instead.
