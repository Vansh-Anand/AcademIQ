from enum import Enum

class ExecutionMode(str, Enum):
    REAL_RUNTIME = "REAL_RUNTIME"
    SIMULATED = "SIMULATED"
    BENCHMARK = "BENCHMARK"
    SYNTHETIC = "SYNTHETIC"
    UNAVAILABLE = "UNAVAILABLE"
