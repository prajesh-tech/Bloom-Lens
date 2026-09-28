# Security Policy

## Supported Versions

We provide security updates and patches for active major versions of BloomLens:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

---

## Reporting a Vulnerability

The BloomLens maintainers take the security of our platform and user data seriously. If you discover a security vulnerability, we appreciate your help in disclosing it responsibly.

### How to Report

> [!IMPORTANT]
> **Please DO NOT file public GitHub issues for security vulnerabilities.**

Instead, please report security issues through one of the following methods:

1. **GitHub Private Vulnerability Reporting**: Submit a private advisory report directly via the GitHub repository under the **Security** tab -> **Advisories** -> **Report a vulnerability**.
2. **Email**: Send a detailed report to the maintainers at `security@bloomlens.dev` (or open a direct private communication channel with the project maintainers).

### Information to Include

To help us triage and resolve the issue quickly, please provide:
- A clear description of the vulnerability and its potential impact.
- Step-by-step instructions to reproduce the issue (including sample payload, request headers, or test file).
- The affected component (e.g., Document parser, Auth dependency, API routes, database session lifecycle).
- Any proposed remediation or patch, if available.

---

## Response Timeline & Process

- **Initial Acknowledgment**: Within 48 hours of receiving your report.
- **Assessment & Triage**: Within 5 business days, confirming severity and reproducing the issue.
- **Fix & Disclosure**: We will prepare a patch and coordinate a release. Once released, public disclosure will take place in the release notes or a GitHub Security Advisory.

---

## Security Best Practices for Deployments

- **API Keys & Secrets**: Never commit `.env` files or API secrets into version control. Ensure `GEMINI_API_KEY`, `API_KEY`, and `DATABASE_URL` are supplied securely via environment variables.
- **Authentication**: Keep `AUTH_ENABLED=true` in production to enforce API key authentication across write routes and analytics.
- **File Upload Security**: Validate uploaded document extensions (`.pdf`, `.docx`) and file size limits before processing.
- **Database Safety**: Ensure database user credentials follow the principle of least privilege.
