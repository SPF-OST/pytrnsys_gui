class SinglePipes:
    INITIAL_TEMPERATURE = "spTIni"


class DoublePipes:
    INITIAL_COLD_TEMPERATURE = "dpTIniCold"
    INITIAL_HOT_TEMPERATURE = "dpTIniHot"
    REFERENCE_LENGTH = "dpLengthRef"
    N_AXIAL_SOIL_NODES_AT_REFERENCE_LENGTH = "dpNrSlAxRef"
    FLUID_TO_SOIL_NODES_RATIO = "dpNrFlNdsToNrSlAxRatio"
    N_CIRCUMFERENTIAL_SOIL_NODES = "dpNrSlCirc"


class MassFlowSolver:
    ABSOLUTE_TOLERANCE = "mfrSolverAbsTol"
    RELATIVE_TOLERANCE = "mfrSolverRelTol"
    SWITCHING_THRESHOLD = "mfrTolSwitchThreshold"
