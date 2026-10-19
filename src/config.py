"""Central project configuration values with explicit analytical meaning."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CleaningConfig:
    """Phase 3 rules; categories describe evidence volume and do not filter rows."""

    low_volume_max_tests: int = 4
    medium_volume_max_tests: int = 19
    coordinate_tolerance: float = 1e-9


CLEANING = CleaningConfig()
