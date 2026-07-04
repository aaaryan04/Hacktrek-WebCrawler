# Hacktrek WebCrawler Project Report

## Abstract

Hacktrek WebCrawler is a full-stack web reconnaissance dashboard for authorized website assessment. It combines a React interface with a FastAPI backend to collect response metadata, analyze common web exposure signals, calculate an educational risk score, and produce exportable JSON evidence.

## Problem Statement

Small teams and students often need a simple way to understand a website's visible attack surface without jumping directly into heavy security tooling. Hacktrek WebCrawler provides a controlled dashboard for learning reconnaissance workflows, interpreting common findings, and presenting results clearly.

## Objectives

- Build a full-stack reconnaissance dashboard
- Automate common passive web checks
- Present findings in a report-ready format
- Provide an educational risk score
- Support responsible, authorized usage only

## Methodology

1. Normalize and validate the target URL.
2. Fetch the target homepage with a custom user agent.
3. Analyze HTTP headers against common security controls.
4. Parse HTML for forms, inputs, technologies, and parameterized links.
5. Fetch robots.txt and sitemap.xml.
6. Generate findings with severity and recommendations.
7. Calculate a score from weighted penalties.
8. Render an executive dashboard and exportable JSON report.

## Core Modules

| Module | Description |
| --- | --- |
| Full Assessment | Runs the combined workflow and produces scoring |
| Header Audit | Checks response headers and missing security controls |
| Form Mapper | Extracts forms, methods, actions, and inputs |
| Tech Fingerprint | Detects common web technology signatures |
| Robots Review | Fetches robots.txt for public crawler metadata |
| Sitemap Pull | Fetches sitemap.xml and extracts listed URLs |
| Parameter Finder | Finds links that contain query parameters |
| Subdomain Sweep | Generates and DNS-resolves common subdomain candidates |
| TLS Inspector | Inspects the certificate, expiry, and negotiated protocol |
| DNS Records | Resolves A, AAAA, MX, NS, and TXT records |

The assessment workflow additionally audits cookie flags (Secure, HttpOnly,
SameSite) and fingerprints common WAF / CDN providers.

## Scoring

The risk score starts at 100 and subtracts weighted penalties for missing headers, exposed banners, risky form methods, parameterized URLs, and error responses. The score is mapped to Low, Moderate, High, or Critical risk.

## Limitations

- The scanner is educational and does not replace penetration testing.
- Technology detection uses simple signatures.
- Subdomain discovery is candidate-based; only common names are resolved.
- SSRF blocking is DNS-aware but remains a safety layer, not a complete SSRF
  protection boundary.

## Future Enhancements

- Certificate transparency / passive subdomain enumeration
- Crawl depth controls in the web UI
- PDF report export
- Historical scan comparison and diffing
- Authentication-aware scanning for lab environments

## Responsible Use

Only run this project against systems you own, manage, or have explicit permission to test.
