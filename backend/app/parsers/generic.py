import ipaddress
import json
import re
from typing import Any

from app.parsers.base import ParseResult

KEY_VALUE = re.compile(r'(?P<key>[A-Za-z_][\w.-]*)=(?:"(?P<quoted>[^"]*)"|(?P<plain>[^\s,;]+))')
IP_CANDIDATE = re.compile(r"(?<![\w:])(?:\d{1,3}(?:\.\d{1,3}){3}|[0-9A-Fa-f]*:[0-9A-Fa-f:]+)(?![\w:])")
TIMESTAMPS = [
    re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?\b"),
    re.compile(r"\b[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\b"),
    re.compile(r"\b\d{1,2}/[A-Z][a-z]{2}/\d{4}:\d{2}:\d{2}:\d{2}\s+[+-]\d{4}\b"),
]


class JSONParser:
    name = "json"

    def confidence(self, raw: str, structured: dict[str, Any] | None = None) -> float:
        # Structured fallback; specialized structured parsers score higher.
        return 0.9 if structured is not None else 0.0

    def parse(self, raw: str, structured: dict[str, Any] | None = None) -> ParseResult:
        return ParseResult(self.name, 0.9, dict(structured or {}))


class KeyValueParser:
    name = "key_value"

    def confidence(self, raw: str, structured: dict[str, Any] | None = None) -> float:
        count = len(KEY_VALUE.findall(raw))
        return min(0.92, 0.45 + count * 0.08) if count >= 2 else 0.0

    def parse(self, raw: str, structured: dict[str, Any] | None = None) -> ParseResult:
        fields = {m.group("key"): m.group("quoted") or m.group("plain") for m in KEY_VALUE.finditer(raw)}
        remainder = KEY_VALUE.sub("", raw).strip(" ,;-")
        if remainder:
            fields.setdefault("message", remainder)
        return ParseResult(self.name, self.confidence(raw), fields, "partial")


class DelimitedParser:
    name = "delimited"

    def confidence(self, raw: str, structured: dict[str, Any] | None = None) -> float:
        if "\t" in raw and len(raw.split("\t")) >= 3:
            return 0.42
        if raw.count(",") >= 3:
            return 0.35
        return 0.0

    def parse(self, raw: str, structured: dict[str, Any] | None = None) -> ParseResult:
        delimiter = "\t" if "\t" in raw else ","
        values = [value.strip() for value in raw.split(delimiter)]
        return ParseResult(self.name, self.confidence(raw), {"message": raw, "columns": values}, "partial")


class HeuristicParser:
    name = "heuristic"

    def confidence(self, raw: str, structured: dict[str, Any] | None = None) -> float:
        return 0.3 if self.extract(raw) else 0.0

    @staticmethod
    def extract(raw: str) -> dict[str, Any]:
        fields: dict[str, Any] = {}
        for pattern in TIMESTAMPS:
            match = pattern.search(raw)
            if match:
                fields["timestamp"] = match.group(0)
                break
        ips: list[str] = []
        for candidate in IP_CANDIDATE.findall(raw):
            try:
                normalized = str(ipaddress.ip_address(candidate))
            except ValueError:
                continue
            if normalized not in ips:
                ips.append(normalized)
        if ips:
            fields["source_ip"] = ips[0]
        if len(ips) > 1:
            fields["destination_ip"] = ips[1]
        user = re.search(r"\b(?:user|username|account)[:=\s]+([\w.@\\-]+)", raw, re.I)
        if user:
            fields["username"] = user.group(1)
        method = re.search(r"\b(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(\S+)", raw)
        if method:
            fields.update(http_method=method.group(1), url=method.group(2), event_category="web")
        status = re.search(r"\b(?:status|http_status)[=: ](\d{3})\b", raw, re.I)
        if status:
            fields["http_status"] = status.group(1)
        pid = re.search(r"\bpid[=: ](\d+)\b", raw, re.I)
        if pid:
            fields["process_id"] = pid.group(1)
        event_id = re.search(r"\b(?:event[_ ]?id)[=: ](\d+)\b", raw, re.I)
        if event_id:
            fields["event_id"] = event_id.group(1)
        lower = raw.lower()
        if "failed login" in lower or "authentication failed" in lower:
            fields.update(event_category="authentication", event_type="authentication_failure", event_outcome="failure")
        elif "successful login" in lower or "authentication success" in lower:
            fields.update(event_category="authentication", event_type="authentication_success", event_outcome="success")
        if fields:
            fields["message"] = raw
        return fields

    def parse(self, raw: str, structured: dict[str, Any] | None = None) -> ParseResult:
        fields = self.extract(raw)
        status = "partial" if fields else "raw"
        return ParseResult(self.name if fields else "raw_fallback", 0.3 if fields else 0.0, fields, status)


def decode_json(raw: str) -> dict[str, Any] | None:
    stripped = raw.strip()
    if not stripped.startswith("{"):
        return None
    try:
        value = json.loads(stripped)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return value if isinstance(value, dict) else None
