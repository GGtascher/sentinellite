# Security Policy

## Project Status

SentinelLite is currently a development-stage cybersecurity portfolio project.

Until the first stable release, security fixes target the latest version of the default branch.

## Reporting a Vulnerability

Please do not publish sensitive vulnerability details in a public GitHub issue.

When available, use GitHub's private vulnerability reporting feature through the repository's **Security** tab.

A useful report should include:

- the affected version or commit;
- a description of the issue;
- the expected security impact;
- reproduction steps using synthetic or non-sensitive data;
- a suggested mitigation, if available.

Please do not include:

- real credentials;
- API keys;
- authentication tokens;
- personal logs;
- private infrastructure information;
- third-party confidential data.

## Security Model

SentinelLite processes potentially hostile log data.

The application is designed to:

- validate input at ingestion boundaries;
- limit upload and event sizes;
- preserve raw evidence without executing it;
- use ORM-based database access;
- render event content as text rather than trusted HTML;
- operate without sending logs to external services by default.

## Deployment Warning

SentinelLite 0.1 does not provide authentication or role-based access control.

Do not expose the development stack directly to an untrusted network.

If adapting the project for a shared or production-like environment, add appropriate:

- authentication;
- authorization;
- TLS;
- firewall restrictions;
- secure credential management;
- retention policies;
- backups;
- monitoring.

## Scope

Security research and contributions should remain defensive.

Do not submit real malware, stolen credentials, destructive payloads, or third-party sensitive data to the repository.
