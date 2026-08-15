# Detection engine

Rules live as YAML below `rules/` and are validated at startup. Duplicate IDs or invalid severity/threshold definitions stop loading rather than silently weakening coverage.

## Rule schema

```yaml
id: AUTH-001
title: SSH brute force
description: At least five SSH authentication failures from one source within two minutes.
severity: high
enabled: true
match:
  all:
    - event_type: authentication_failure
    - process_name: sshd
group_by: [source_ip]
threshold:
  count: 5
  timeframe_seconds: 120
mitre:
  tactic: Credential Access
  technique: T1110
```

Required fields are `id`, `title`, `description`, `severity`, and either `match` or `sequence`. Severities are informational, low, medium, high, or critical. `match` fields refer to normalized Event attributes. Values can be direct equality, a list, or `{contains: ...}`, `{regex: ...}`, `{in: [...]}`, or `{not_in: [...]}`. `all` and `any` combine clauses.

A threshold requires `group_by`, `count`, and `timeframe_seconds`. Optional `distinct_field` counts unique values—for example destination ports—rather than events. Sequence rules replace `match` with ordered `stages` and a timeframe:

```yaml
sequence:
  timeframe_seconds: 600
  stages:
    - event_type: authentication_failure
    - event_type: authentication_success
```

## Evaluation and alerts

Rules run after each event is flushed in the ingestion transaction. Threshold/sequence searches are time-bounded. Matching supporting Events are linked to an Alert; an active alert for the same rule/group is extended. Each alert includes timing, entity fields, count, evidence, ATT&CK context, raw-event access through linked events, analyst notes, and status.

`CORR-001` is code-backed correlation for a deliberately small multi-signal sequence: three or more authentication failures, a success, then suspicious PowerShell on the same host/identity within 15 minutes. More complex correlation is future work.

## Adding a rule

Choose the appropriate category directory, use a globally unique ID, test the rule on positive and negative synthetic records, validate threshold grouping, and cite only a defensible ATT&CK technique. Run `python -m pytest backend/tests/test_detection.py`. Rules are reloaded on API restart in V0.1.
