# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in OST Linker, please report it responsibly by opening an issue on the [ost-linker repository](https://github.com/opensource-together/ost-linker/issues) with the label `security`.

**Please do NOT include exploit details in public issues.** Use a vague title (e.g., "Security issue in authentication") and a maintainer will follow up privately.

## What to Report

- SQL injection or command injection vulnerabilities
- Credential or secret exposure (API keys, tokens, passwords)
- Authentication or authorization bypass
- Denial of service vulnerabilities
- Dependency vulnerabilities (known CVEs)

## Response Timeline

- **Acknowledgment**: within 48 hours
- **Assessment**: within 1 week
- **Fix**: depends on severity, critical issues are prioritized

## Supported Versions

Only the latest version on the `staging` branch is actively maintained. We do not backport security fixes to older versions.
