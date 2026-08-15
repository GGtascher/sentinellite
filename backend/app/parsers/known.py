import re
from typing import Any

from app.parsers.base import ParseResult


class SSHAuthParser:
    name = "linux_auth"
    pattern = re.compile(
        r"^(?P<timestamp>[A-Z][a-z]{2}\s+\d{1,2}\s+\d\d:\d\d:\d\d)\s+"
        r"(?P<hostname>\S+)\s+sshd\[(?P<process_id>\d+)\]:\s+"
        r"(?P<result>Failed password|Accepted password|Accepted publickey)\s+for\s+"
        r"(?:invalid user\s+)?(?P<username>\S+)\s+from\s+(?P<source_ip>\S+)"
        r"(?:\s+port\s+(?P<source_port>\d+))?",
        re.IGNORECASE,
    )

    def confidence(self, raw: str, structured: dict[str, Any] | None = None) -> float:
        return 0.99 if self.pattern.search(raw) else 0.0

    def parse(self, raw: str, structured: dict[str, Any] | None = None) -> ParseResult:
        match = self.pattern.search(raw)
        fields = match.groupdict() if match else {}
        result = fields.pop("result", "").lower()
        fields.update(
            event_category="authentication",
            event_type="authentication_failure" if result.startswith("failed") else "authentication_success",
            event_outcome="failure" if result.startswith("failed") else "success",
            process_name="sshd",
            message=raw.split(": ", 1)[-1],
        )
        return ParseResult(self.name, 0.99, fields)


class AccessLogParser:
    name = "http_access"
    pattern = re.compile(
        r'^(?P<source_ip>\S+)\s+\S+\s+\S+\s+\[(?P<timestamp>[^]]+)]\s+"'
        r'(?P<http_method>[A-Z]+)\s+(?P<url>\S+)\s+(?P<protocol>HTTP/[^\"]+)"\s+'
        r"(?P<http_status>\d{3})(?:\s+\S+)?"
    )

    def confidence(self, raw: str, structured: dict[str, Any] | None = None) -> float:
        return 0.97 if self.pattern.search(raw) else 0.0

    def parse(self, raw: str, structured: dict[str, Any] | None = None) -> ParseResult:
        match = self.pattern.search(raw)
        fields = match.groupdict() if match else {}
        status = int(fields.get("http_status", 0))
        fields.update(
            event_category="web",
            event_type="http_request",
            event_outcome="failure" if status >= 400 else "success",
            message=f"{fields.get('http_method', '')} {fields.get('url', '')} returned {status}",
        )
        return ParseResult(self.name, 0.97, fields)


class SyslogParser:
    name = "syslog"
    pattern = re.compile(
        r"^(?:<(?P<priority>\d{1,3})>)?(?P<timestamp>[A-Z][a-z]{2}\s+\d{1,2}\s+\d\d:\d\d:\d\d)\s+"
        r"(?P<hostname>\S+)\s+(?P<process_name>[\w./-]+)(?:\[(?P<process_id>\d+)])?:\s*(?P<message>.*)$"
    )

    def confidence(self, raw: str, structured: dict[str, Any] | None = None) -> float:
        return 0.85 if self.pattern.search(raw) else 0.0

    def parse(self, raw: str, structured: dict[str, Any] | None = None) -> ParseResult:
        match = self.pattern.search(raw)
        fields = match.groupdict() if match else {}
        priority = fields.pop("priority", None)
        if priority is not None:
            fields["severity"] = str(int(priority) % 8)
        fields.setdefault("event_category", "system")
        fields.setdefault("event_type", "syslog_event")
        return ParseResult(self.name, 0.85, fields)


class WindowsEventParser:
    name = "windows_event"
    event_id_keys = ("eventid", "event_id", "EventID")

    def confidence(self, raw: str, structured: dict[str, Any] | None = None) -> float:
        if structured and any(key in structured for key in self.event_id_keys):
            return 0.94
        return 0.0

    def parse(self, raw: str, structured: dict[str, Any] | None = None) -> ParseResult:
        data = dict(structured or {})
        event_id = next((data.get(key) for key in self.event_id_keys if key in data), None)
        event_id_text = str(event_id) if event_id is not None else None
        event_type = {
            "4624": "authentication_success",
            "4625": "authentication_failure",
            "4688": "process_creation",
            "1": "process_creation",
            "4720": "account_created",
            "4698": "scheduled_task_created",
        }.get(event_id_text, "windows_event")
        outcome = "failure" if event_id_text == "4625" else "success" if event_id_text == "4624" else None
        fields: dict[str, Any] = dict(data)
        fields.update(event_id=event_id_text, event_type=event_type, event_outcome=outcome)
        fields.setdefault("event_category", "authentication" if "authentication" in event_type else "process")
        return ParseResult(self.name, 0.94, fields)


class FirewallParser:
    name = "firewall"

    def confidence(self, raw: str, structured: dict[str, Any] | None = None) -> float:
        lower = raw.lower()
        has_action = bool(re.search(r"\b(action=)?(deny|denied|drop|dropped|blocked|allow|allowed)\b", lower))
        has_network = bool(re.search(r"\b(src|src_ip|source_ip|dst|dst_ip|destination_ip)=", lower))
        return 0.9 if has_action and has_network else 0.0

    def parse(self, raw: str, structured: dict[str, Any] | None = None) -> ParseResult:
        pairs = dict(re.findall(r'([\w.-]+)=(?:"([^"]*)"|(\S+))', raw)) if False else {}
        for match in re.finditer(r'([\w.-]+)=(?:"([^"]*)"|(\S+))', raw):
            pairs[match.group(1)] = match.group(2) or match.group(3)
        action = next((pairs.get(k) for k in ("action", "act") if pairs.get(k)), None)
        if not action:
            action_match = re.search(r"\b(deny|denied|drop|dropped|blocked|allow|allowed)\b", raw, re.I)
            action = action_match.group(1) if action_match else None
        denied = bool(action and action.lower() in {"deny", "denied", "drop", "dropped", "blocked"})
        pairs.update(event_category="network", event_type="firewall_denied" if denied else "firewall_connection", event_action=action, event_outcome="failure" if denied else "success")
        return ParseResult(self.name, 0.9, pairs)
