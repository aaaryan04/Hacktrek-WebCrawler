# Security Policy

Hacktrek WebCrawler is an educational reconnaissance dashboard. It is intended for authorized testing only.

## Supported Use

- Websites you own
- Websites you manage
- Lab targets
- Targets where you have explicit written permission

## Safety Boundaries

The API performs DNS-aware SSRF filtering: it resolves each target and blocks
localhost, loopback, private, link-local, multicast, and reserved addresses,
including IPv4 addresses smuggled inside IPv6 translation ranges. Optional
per-IP rate limiting (`RATE_LIMIT_PER_MINUTE`) can throttle abuse. These are
safety layers to reduce accidental misuse in public demos, not a complete SSRF
defense.

## Reporting Issues

If you find a security issue in this project, open a GitHub issue with:

- A short description
- Steps to reproduce
- Expected behavior
- Actual behavior
- Suggested fix, if known

Do not include secrets, credentials, or unauthorized target data in reports.
