from enum import Enum

class PairingAlgorithm(Enum):
    adaptive = "adaptive"
    random = "random"
    adaptive_min_delta = "adaptive_min_delta"
