# Security Policy

## Supported versions

| Version | Supported |
| --- | --- |
| 1.0.x | Yes |
| < 1.0 | No |

## Reporting a vulnerability

Please do not open a public issue for a security problem. Use the repository's
**Security → Report a vulnerability** flow (GitHub Security Advisories) so the
maintainers can investigate privately and coordinate a fix. Maintainers should
enable **Private vulnerability reporting** in Settings → Code security.

Include, when possible:

- The app version and macOS version.
- A description of the impact and the steps to reproduce.
- A sample PDF or file that triggers the issue, if it is safe to share.
- Whether the issue is in this app or in an upstream dependency.

## Scope

Resume Screener processes untrusted PDF files locally with PyMuPDF. Malformed
PDFs or dependency vulnerabilities may be reportable upstream as well. The app
does not upload resume text or contact a network service.

The distributed macOS app is ad-hoc signed but not Developer ID-signed or
notarized; Gatekeeper warnings are expected. This is a distribution limitation
rather than a security vulnerability, but reports of unsafe behavior are still
welcome.
