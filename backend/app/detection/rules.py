from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, model_validator


class Threshold(BaseModel):
    count: int = Field(ge=1, le=100_000)
    timeframe_seconds: int = Field(ge=1, le=2_592_000)
    distinct_field: str | None = None


class Sequence(BaseModel):
    stages: list[dict[str, Any]] = Field(min_length=2, max_length=10)
    timeframe_seconds: int = Field(ge=1, le=2_592_000)


class Rule(BaseModel):
    id: str = Field(pattern=r"^[A-Z][A-Z0-9_-]{2,63}$")
    title: str
    description: str
    severity: Literal["informational", "low", "medium", "high", "critical"]
    enabled: bool = True
    match: dict[str, Any] = {}
    group_by: list[str] = []
    threshold: Threshold | None = None
    sequence: Sequence | None = None
    mitre: dict[str, str] = {}

    @model_validator(mode="after")
    def threshold_has_groups(self) -> "Rule":
        if self.threshold and not self.group_by:
            raise ValueError("threshold rules require group_by")
        if self.sequence and self.match:
            raise ValueError("sequence rules use sequence.stages instead of match")
        if not self.sequence and not self.match:
            raise ValueError("a rule requires match or sequence")
        return self


def load_rules(path: Path) -> list[Rule]:
    rules: list[Rule] = []
    if not path.exists():
        return rules
    for rule_file in sorted(path.rglob("*.yml")) + sorted(path.rglob("*.yaml")):
        with rule_file.open(encoding="utf-8") as handle:
            document = yaml.safe_load(handle)
        documents = document if isinstance(document, list) else [document]
        rules.extend(Rule.model_validate(item) for item in documents if item)
    ids = [rule.id for rule in rules]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate detection rule IDs")
    return rules
