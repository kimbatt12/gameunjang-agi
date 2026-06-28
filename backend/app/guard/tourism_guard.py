from dataclasses import dataclass


@dataclass(frozen=True)
class ScopeClassification:
    label: str
    reason: str = ""

    @property
    def is_tourism_related(self) -> bool:
        return self.label == "domestic_tourism"
