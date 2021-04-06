import pkgutil as _pu
import logging as _log

import PyQt5.QtGui as _qtg

_logger = _log.getLogger("root")


class ImageLoader:
    def __init__(self, relativeFilePath: str, logger: _log.Logger = _logger) -> None:
        self.relativeFilePath = relativeFilePath

        parts = relativeFilePath.split(".")
        self.fileExtension = parts[-1].lower() if parts else None

        self._logger = logger

    def bitmap(self) -> _qtg.QBitmap:
        imageBytes = self._loadBytes()

        bitmap = _qtg.QBitmap()
        bitmap.loadFromData(imageBytes)

        return bitmap

    def icon(self) -> _qtg.QIcon:
        bitmap = self.bitmap()

        return _qtg.QIcon(bitmap)

    def image(self) -> _qtg.QImage:
        bitmap = self.bitmap()

        return bitmap.toImage()

    def _loadBytes(self) -> bytes:
        try:
            imageBytes = _pu.get_data("trnsysGUI", self.relativeFilePath)
            if not imageBytes:
                raise AssertionError("Image data is empty.")
        except Exception as e:
            self._logger.exception(
                "An exception occurred loading image data for '%s'.",
                self.relativeFilePath,
                exc_info=True,
                stack_info=True,
            )
            raise e
        return imageBytes


AIR_SOURCE_HP_PNG = ImageLoader("images/AirSourceHP.png")
AIR_SOURCE_HP_SVG = ImageLoader("images/AirSourceHP.svg")
BOILER_PNG = ImageLoader("images/Boiler.png")
BOILER_SVG = ImageLoader("images/Boiler.svg")
BVI_PNG = ImageLoader("images/Bvi.png")
COLLECTOR_PNG = ImageLoader("images/Collector.png")
COLLECTOR_SVG = ImageLoader("images/Collector.svg")
CONNECTOR_PNG = ImageLoader("images/Connector.png")
CONNECTOR_SVG = ImageLoader("images/Connector.svg")
ELECTRIC_ROD_SVG = ImageLoader("images/ElectricRod.svg")
EXPORT_DCK_PNG = ImageLoader("images/exportDck.png")
EXPORT_DCK_SVG = ImageLoader("images/exportDck.svg")
EXPORT_HYDRAULIC_CONTROL_PNG = ImageLoader("images/exportHydraulicControl.png")
EXPORT_HYDRAULIC_CONTROL_SVG = ImageLoader("images/exportHydraulicControl.svg")
EXPORT_HYDRAULICS_PNG = ImageLoader("images/exportHydraulics.png")
EXPORT_HYDRAULICS_SVG = ImageLoader("images/exportHydraulics.svg")
EXTERNAL_HX_PNG = ImageLoader("images/ExternalHx.png")
EXTERNAL_HX_SVG = ImageLoader("images/ExternalHx.svg")
GEAR_PNG = ImageLoader("images/gear.png")
GEAR_SVG = ImageLoader("images/gear.svg")
GENERIC_BLOCK_PNG = ImageLoader("images/GenericBlock.png")
GENERIC_ITEM_PNG = ImageLoader("images/GenericItem.png")
GROUND_SOURCE_HX_PNG = ImageLoader("images/GroundSourceHx.png")
GROUND_SOURCE_HX_SVG = ImageLoader("images/GroundSourceHx.svg")
HP_PNG = ImageLoader("images/HP.png")
HP_SVG = ImageLoader("images/HP.svg")
HP_DOUBLE_DUAL_PNG = ImageLoader("images/HPDoubleDual.png")
HP_DOUBLE_DUAL_SVG = ImageLoader("images/HPDoubleDual.svg")
HP_TWO_HX_PNG = ImageLoader("images/HPTwoHx.png")
HP_TWO_HX_SVG = ImageLoader("images/HPTwoHx.svg")
ICE_STORAGE_PNG = ImageLoader("images/IceStorage.png")
ICE_STORAGE_SVG = ImageLoader("images/IceStorage.svg")
ICE_STORAGE_TWO_HX_PNG = ImageLoader("images/IceStorageTwoHx.png")
ICE_STORAGE_TWO_HX_SVG = ImageLoader("images/IceStorageTwoHx.svg")
INBOX_PNG = ImageLoader("images/inbox.png")
LABEL_TOGGLE_PNG = ImageLoader("images/labelToggle.png")
OUTBOX_PNG = ImageLoader("images/outbox.png")
PIT_STORAGE_PNG = ImageLoader("images/PitStorage.png")
PIT_STORAGE_SVG = ImageLoader("images/PitStorage.svg")
PROCESS_SIMULATION_PNG = ImageLoader("images/processSimulation.png")
PROCESS_SIMULATION_SVG = ImageLoader("images/processSimulation.svg")
PUMP_PNG = ImageLoader("images/Pump.png")
PUMP_SVG = ImageLoader("images/Pump.svg")
PV_PNG = ImageLoader("images/PV.png")
PV_SVG = ImageLoader("images/PV.svg")
RADIATOR_PNG = ImageLoader("images/Radiator.png")
RADIATOR_SVG = ImageLoader("images/Radiator.svg")
ROTATE_LEFT_PNG = ImageLoader("images/rotate-left.png")
ROTATE_TO_RIGHT_PNG = ImageLoader("images/rotate-to-right.png")
RUN_MFS_PNG = ImageLoader("images/runMfs.png")
RUN_MFS_SVG = ImageLoader("images/runMfs.svg")
RUN_SIMULATION_PNG = ImageLoader("images/runSimulation.png")
RUN_SIMULATION_SVG = ImageLoader("images/runSimulation.svg")
STORAGE_TANK_PNG = ImageLoader("images/StorageTank.PNG")
STORAGE_TANK_SVG = ImageLoader("images/StorageTank.svg")
TEE_PIECE_PNG = ImageLoader("images/TeePiece.png")
TEE_PIECE_SVG = ImageLoader("images/TeePiece.svg")
TRASH_PNG = ImageLoader("images/trash.png")
T_VENTIL_PNG = ImageLoader("images/TVentil.png")
T_VENTIL_SVG = ImageLoader("images/TVentil.svg")
UPDATE_CONFIG_PNG = ImageLoader("images/updateConfig.png")
UPDATE_CONFIG_SVG = ImageLoader("images/updateConfig.svg")
VIS_MFS_PNG = ImageLoader("images/visMfs.png")
VIS_MFS_SVG = ImageLoader("images/visMfs.svg")
W_TAP_PNG = ImageLoader("images/WTap.png")
W_TAP_SVG = ImageLoader("images/WTap.svg")
W_TAP_MAIN_PNG = ImageLoader("images/WTap_main.png")
W_TAP_MAIN_SVG = ImageLoader("images/WTap_main.svg")
ZOOM_0_PNG = ImageLoader("images/zoom-0.png")
ZOOM_IN_PNG = ImageLoader("images/zoom-in.png")
ZOOM_OUT_PNG = ImageLoader("images/zoom-out.png")
