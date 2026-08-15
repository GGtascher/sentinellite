# Universal log parsing

“Universal” means safe acceptance and best-effort extraction—not perfect understanding. SentinelLite uses specialized parsers plus generic extraction and raw-event fallback for unknown formats. A submitted record is rejected only at an input boundary (empty, too large, disallowed/binary upload, malformed container file), not merely because its format is unfamiliar.

## Layer order

1. Detect a structured object (currently JSON).
2. Score known parsers: Windows/Sysmon JSON, SSH/auth, HTTP access, firewall, syslog.
3. Recognize `key=value` pairs.
4. Recognize generic comma/tab-delimited records.
5. Extract common timestamps, validated IPs, users, HTTP values, PIDs, event IDs, and obvious authentication outcomes.
6. Store a raw fallback with `parser_name=raw_fallback`, confidence `0`, and the original text.

Generic key-value/delimited results are augmented with deterministic heuristic fields when those fields are missing. Parser-specific values that do not map to the canonical model survive under `metadata`.

## Examples

Input:

```text
Aug 15 14:31:11 server01 sshd[1234]: Failed password for root from 10.0.0.5 port 55422 ssh2
```

Extracted then normalized:

```json
{"hostname":"server01","source_ip":"10.0.0.5","source_port":55422,"username":"root","process_name":"sshd","event_type":"authentication_failure","event_outcome":"failure","parser_name":"linux_auth"}
```

Input:

```text
src_ip=192.168.1.12 dst_ip=8.8.8.8 action=blocked severity=high
```

Normalizes aliases to `source_ip`, `destination_ip`, and `event_action`; the firewall parser also classifies it as `firewall_denied`.

Input:

```text
sensor::zephyr / node=alpha / signal chartreuse
```

No reliable structure is found. The event is stored with its entire text in `raw_event`, `parse_status=raw`, and no fabricated timestamp or address.

## Timestamps and addresses

ISO-8601, common syslog timestamps, Apache timestamps, numeric Unix seconds/milliseconds, and other dateutil-recognized formats are normalized to timezone-aware UTC. Naive values are treated as UTC; syslog timestamps use the current year because the source omits it. The original string is retained in `timestamp_original`. IPv4 and IPv6 candidates must pass Python's `ipaddress` validation; private and local addresses are accepted.

## Adding a parser

Implement the `LogParser` protocol with a stable `name`, deterministic `confidence(raw, structured)`, and `parse(...) -> ParseResult`. Register it in the appropriate `ParserEngine` layer and add fixed corpus examples plus malformed-input tests. Parsing must be side-effect free and preserve unknown values.

