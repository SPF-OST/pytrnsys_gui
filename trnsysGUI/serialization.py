import dataclasses as _dc


@_dc.dataclass
class RequiredDecoderFieldsMixin:
    BlockName: str  # /NOSONAR  # pylint: disable=invalid-name
    BlockDisplayName: str  # /NOSONAR  # pylint: disable=invalid-name
