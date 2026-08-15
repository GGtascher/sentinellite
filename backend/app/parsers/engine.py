from app.parsers.base import LogParser, ParseResult
from app.parsers.generic import (
    DelimitedParser,
    HeuristicParser,
    JSONParser,
    KeyValueParser,
    decode_json,
)
from app.parsers.known import (
    AccessLogParser,
    FirewallParser,
    SSHAuthParser,
    SyslogParser,
    WindowsEventParser,
)


class ParserEngine:
    """Deterministic, layered best-effort parser selection."""

    def __init__(self) -> None:
        self.structured: list[LogParser] = [WindowsEventParser(), JSONParser()]
        self.specialized: list[LogParser] = [SSHAuthParser(), AccessLogParser(), FirewallParser(), SyslogParser()]
        self.generic: list[LogParser] = [KeyValueParser(), DelimitedParser(), HeuristicParser()]

    def parse(self, raw: str) -> ParseResult:
        structured = decode_json(raw)
        candidates = self.structured if structured is not None else self.specialized
        result = self._best(candidates, raw, structured)
        if result and result.confidence >= 0.6:
            return result
        result = self._best(self.generic, raw, structured)
        if result and result.confidence > 0:
            if result.parser_name in {"key_value", "delimited"}:
                heuristic = HeuristicParser().parse(raw)
                result.fields = {**heuristic.fields, **result.fields}
            return result
        return ParseResult("raw_fallback", 0.0, {"message": raw}, "raw")

    @staticmethod
    def _best(parsers: list[LogParser], raw: str, structured: dict | None) -> ParseResult | None:
        scored = [(parser.confidence(raw, structured), parser) for parser in parsers]
        confidence, parser = max(scored, key=lambda value: value[0])
        return parser.parse(raw, structured) if confidence > 0 else None
