import dataclasses as _dc

import trnsysGUI.imageAccessor as _ia

from . import _paths


@_dc.dataclass
class Size:
    _: _dc.KW_ONLY
    width: int
    height: int


@_dc.dataclass
class Graphics:
    accessor: _ia.SvgImageAccessor
    size: Size

    @classmethod
    def createForTypeNameAndSize(
        cls, typeName: str, *, width: int, height: int
    ) -> "Graphics":
        componentResourcePath = _paths.getComponentResourcePath(typeName)
        imageResourcePath = f"{componentResourcePath}/image.svg"
        accessor = _ia.createForPackageResource(
            _ia.SvgImageAccessor, imageResourcePath
        )

        size = Size(width=width, height=height)

        graphics = Graphics(accessor, size)
        return graphics
