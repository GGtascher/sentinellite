from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(slots=True)
class ParseResult:
    parser_name: str
    confidence: float
    fields: dict[str, Any] = field(default_factory=dict)
    status: str = "parsed"


class LogParser(Protocol):
    name: str

    def confidence(self, raw: str, structured: dict[str, Any] | None = None) -> float: ...

    def parse(self, raw: str, structured: dict[str, Any] | None = None) -> ParseResult: ...
