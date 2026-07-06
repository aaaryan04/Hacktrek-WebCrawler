"""Hacktrek WebCrawler API.

FastAPI reconnaissance service. All fetch/parse/scoring logic is factored into
shared helpers (``fetch_url``, ``normalize_url``, ``SECURITY_HEADERS``,
``TECH_SIGNATURES`` ...) so endpoints stay thin and consistent.

Uvicorn entrypoint: ``api.server:app``.
"""

import concurrent.futures
import datetime
import ipaddress
import os
import socket
import ssl
from functools import lru_cache
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.logger import add_log, clear_logs, get_logs
from api.rate_limit import RateLimitMiddleware

try:
    import dns.resolver  # dnspython

    _DNS_AVAILABLE = True
except Exception:  # pragma: no cover - dnspython missing
    _DNS_AVAILABLE = False


# ============================================
# CONFIGURATION (env-driven settings object)
# ============================================


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


class Settings:
    """Lightweight settings object populated from environment variables."""

    def __init__(self):
        raw_origins = os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,"
            "http://localhost:3000,http://127.0.0.1:3000,"
            "https://hacktrek-web-crawler.vercel.app",
        )
        self.allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
        # Vercel gives every branch/preview deployment its own auto-generated
        # subdomain (e.g. hacktrek-web-crawler-git-main-<team>.vercel.app,
        # hacktrek-web-crawler-<hash>-<team>.vercel.app) in addition to the
        # stable production domain. An exact-match allowlist misses those, so
        # the dashboard's own "Visit" links can get silently CORS-blocked.
        # Match any of them by prefix instead of hardcoding each one.
        self.allowed_origin_regex = os.getenv(
            "ALLOWED_ORIGIN_REGEX",
            r"^https://hacktrek-web-crawler[a-z0-9-]*\.vercel\.app$",
        )
        # Credentials are never used with a "*" wildcard (invalid per CORS spec).
        self.allow_credentials = (
            os.getenv("ALLOW_CREDENTIALS", "false").lower() == "true"
            and "*" not in self.allowed_origins
        )
        self.request_timeout = _env_float("REQUEST_TIMEOUT", 10.0)
        self.dns_timeout = _env_float("DNS_TIMEOUT", 5.0)
        self.tls_timeout = _env_float("TLS_TIMEOUT", 6.0)
        self.user_agent = os.getenv("USER_AGENT", "Hacktrek-WebCrawler/2.1")
        self.max_redirects = _env_int("MAX_REDIRECTS", 10)
        # Reliable public resolvers by default (the host's own resolver is often
        # slow/unreachable in container/CI environments). Set to "system" to use
        # the OS-configured nameservers instead.
        raw_ns = os.getenv("DNS_NAMESERVERS", "8.8.8.8,1.1.1.1")
        if raw_ns.strip().lower() == "system":
            self.dns_nameservers = None
        else:
            self.dns_nameservers = [n.strip() for n in raw_ns.split(",") if n.strip()]


@lru_cache
def get_settings() -> "Settings":
    return Settings()


settings = get_settings()


# ============================================
# CREATE FASTAPI APP
# ============================================

app = FastAPI(
    title="Hacktrek WebCrawler API",
    version="2.1.0",
    description=(
        "Reconnaissance endpoints for headers, forms, technologies, robots, "
        "sitemap, subdomains, URL parameters, TLS, DNS, and full site "
        "assessments."
    ),
)

# ============================================
# ENABLE CORS (explicit origins; no wildcard+credentials)
# ============================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_origin_regex=settings.allowed_origin_regex,
    allow_credentials=settings.allow_credentials,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

# Per-IP rate limiting (disabled unless RATE_LIMIT_PER_MINUTE > 0; see api/rate_limit.py).
app.add_middleware(RateLimitMiddleware)


# ============================================
# SHARED SIGNATURES / CONSTANTS
# ============================================

SECURITY_HEADERS = {
    "Content-Security-Policy": {
        "severity": "high",
        "points": 18,
        "recommendation": "Add a Content-Security-Policy to reduce XSS and content injection risk.",
    },
    "Strict-Transport-Security": {
        "severity": "high",
        "points": 16,
        "recommendation": "Enable Strict-Transport-Security for HTTPS-only browser enforcement.",
    },
    "X-Frame-Options": {
        "severity": "medium",
        "points": 10,
        "recommendation": "Set X-Frame-Options or frame-ancestors to reduce clickjacking exposure.",
    },
    "X-Content-Type-Options": {
        "severity": "medium",
        "points": 8,
        "recommendation": "Set X-Content-Type-Options: nosniff to prevent MIME sniffing.",
    },
    "Referrer-Policy": {
        "severity": "low",
        "points": 6,
        "recommendation": "Set a Referrer-Policy to limit sensitive URL leakage.",
    },
    "Permissions-Policy": {
        "severity": "low",
        "points": 5,
        "recommendation": "Add Permissions-Policy to restrict browser features by default.",
    },
}


TECH_SIGNATURES = {
    "WordPress": "wp-content",
    "React": "react",
    "Vue.js": "vue",
    "Angular": "angular",
    "Bootstrap": "bootstrap",
    "jQuery": "jquery",
    "Laravel": "laravel",
    "Django": "csrftoken",
}


# Header/value signatures for common WAF / CDN providers.
WAF_CDN_SIGNATURES = {
    "Cloudflare": ["cf-ray", "cf-cache-status", "__cfduid", "server:cloudflare"],
    "AWS CloudFront": ["x-amz-cf-id", "via:cloudfront", "server:cloudfront"],
    "Akamai": ["x-akamai", "akamaighost", "x-akamai-transformed"],
    "Sucuri": ["x-sucuri-id", "x-sucuri-cache", "sucuri"],
    "Imperva Incapsula": ["x-iinfo", "incap_ses", "visid_incap", "x-cdn:incapsula"],
    "Fastly": ["x-served-by", "x-fastly", "fastly"],
    "Vercel": ["x-vercel-id", "server:vercel"],
    "Netlify": ["x-nf-request-id", "server:netlify"],
    "Microsoft Azure": ["x-azure-ref", "x-msedge-ref"],
    "Google Frontend": ["via:1.1 google", "server:gws", "server:gse"],
    "F5 BIG-IP": ["bigipserver", "x-waf-status"],
}


# ============================================
# URL NORMALIZATION + SSRF PROTECTION
# ============================================

_BLOCKED_HOSTNAMES = {"localhost", "0.0.0.0", "ip6-localhost", "ip6-loopback"}


_NAT64_PREFIX = ipaddress.ip_network("64:ff9b::/96")


def _is_blocked_ip(ip_str: str) -> bool:
    """Return True if an IP is private/loopback/link-local/reserved/etc.

    IPv4 addresses embedded in IPv6 (IPv4-mapped, 6to4, Teredo, NAT64) are
    unwrapped and checked against the real IPv4 destination, so a public host
    reachable via an IPv6 translation prefix is not falsely blocked, and a
    private IPv4 smuggled inside IPv6 is still caught. ``is_reserved`` is only
    applied to IPv4 (240.0.0.0/4); on IPv6 it flags many legitimate public
    translation ranges.
    """
    try:
        addr = ipaddress.ip_address(ip_str.split("%")[0])  # strip zone id
    except ValueError:
        return False

    if isinstance(addr, ipaddress.IPv6Address):
        embedded = addr.ipv4_mapped or addr.sixtofour
        if embedded is None and addr.teredo:
            embedded = addr.teredo[1]
        if embedded is None and addr in _NAT64_PREFIX:
            embedded = ipaddress.ip_address(int(addr) & 0xFFFFFFFF)
        if embedded is not None:
            addr = embedded

    blocked = (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_unspecified
    )
    if addr.version == 4 and addr.is_reserved:
        blocked = True
    return blocked


def _assert_public_host(hostname: str) -> None:
    """Block hosts that resolve to non-public addresses (DNS-based SSRF)."""
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise HTTPException(
            status_code=400,
            detail=f"Could not resolve host '{hostname}'.",
        )

    for info in infos:
        ip_str = info[4][0]
        if _is_blocked_ip(ip_str):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Target resolves to a private, loopback, link-local, or "
                    "reserved address and is blocked for safety."
                ),
            )


def normalize_url(url: str) -> str:
    """Validate, normalize, and SSRF-check a target URL."""
    if not url or not url.strip():
        raise HTTPException(status_code=400, detail="A target URL is required.")

    url = url.strip()

    if not url.startswith("http"):
        url = "https://" + url

    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=400, detail="Only HTTP and HTTPS URLs are supported."
        )

    if not parsed.netloc:
        raise HTTPException(status_code=400, detail="Enter a valid domain or URL.")

    hostname = (parsed.hostname or "").lower()

    if hostname in _BLOCKED_HOSTNAMES or hostname.endswith(".local"):
        raise HTTPException(
            status_code=400,
            detail="Localhost and local-network targets are blocked for public demo safety.",
        )

    # Literal IP target?
    try:
        ipaddress.ip_address(hostname)
        is_literal_ip = True
    except ValueError:
        is_literal_ip = False

    if is_literal_ip:
        if _is_blocked_ip(hostname):
            raise HTTPException(
                status_code=400,
                detail="Private, loopback, link-local, and reserved IP targets are blocked.",
            )
    else:
        # Domain name: resolve and verify every resolved address is public.
        _assert_public_host(hostname)

    return url


def extract_domain(url: str) -> str:
    return urlparse(normalize_url(url)).netloc


def get_hostname(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


# ============================================
# SHARED FETCH HELPERS
# ============================================


def fetch_url(url: str, timeout: float | None = None) -> requests.Response:
    """Perform a GET with the configured UA and timeout."""
    return requests.get(
        url,
        timeout=timeout or settings.request_timeout,
        headers={"User-Agent": settings.user_agent},
        allow_redirects=True,
    )


def safe_fetch(url: str, timeout: float | None = None) -> requests.Response:
    """Fetch a URL, translating requests exceptions into HTTP error codes."""
    try:
        return fetch_url(url, timeout=timeout)
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="The target timed out.")
    except requests.exceptions.TooManyRedirects:
        raise HTTPException(status_code=502, detail="The target returned too many redirects.")
    except requests.exceptions.SSLError as exc:
        raise HTTPException(status_code=502, detail=f"TLS error contacting target: {exc}")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=502, detail="Could not connect to the target host.")
    except requests.exceptions.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Request to target failed: {exc}")


def fetch_html(url: str):
    """Fetch a page and return (response, BeautifulSoup)."""
    response = safe_fetch(url)
    soup = BeautifulSoup(response.text, "html.parser")
    return response, soup


def build_finding(title, severity, description, recommendation, evidence=None):
    return {
        "title": title,
        "severity": severity,
        "description": description,
        "recommendation": recommendation,
        "evidence": evidence,
    }


# ============================================
# ANALYSIS HELPERS
# ============================================


def analyze_headers(headers):
    present, missing, findings = [], [], []
    penalty = 0

    for header, meta in SECURITY_HEADERS.items():
        if header in headers:
            present.append(header)
        else:
            missing.append(header)
            penalty += meta["points"]
            findings.append(
                build_finding(
                    f"Missing {header}",
                    meta["severity"],
                    f"The response does not include the {header} security header.",
                    meta["recommendation"],
                )
            )

    server = headers.get("Server")
    powered_by = headers.get("X-Powered-By")

    if server:
        penalty += 4
        findings.append(
            build_finding(
                "Server banner exposed",
                "low",
                "The Server header reveals implementation details.",
                "Reduce or normalize server banner information where possible.",
                server,
            )
        )

    if powered_by:
        penalty += 6
        findings.append(
            build_finding(
                "Technology header exposed",
                "low",
                "The X-Powered-By header can reveal framework or runtime details.",
                "Remove X-Powered-By from production responses.",
                powered_by,
            )
        )

    return {"present": present, "missing": missing, "findings": findings, "penalty": penalty}


def _iter_set_cookie(response: requests.Response):
    """Yield individual Set-Cookie header strings, even when multiple exist."""
    try:
        values = response.raw.headers.getlist("Set-Cookie")  # urllib3
        if values:
            return values
    except Exception:
        pass
    combined = response.headers.get("Set-Cookie")
    return [combined] if combined else []


def analyze_cookies(response: requests.Response):
    """Audit Set-Cookie flags (Secure, HttpOnly, SameSite)."""
    cookies, findings = [], []
    penalty = 0

    for raw in _iter_set_cookie(response):
        if not raw:
            continue
        parts = [p.strip() for p in raw.split(";") if p.strip()]
        if not parts:
            continue
        name = parts[0].split("=", 1)[0].strip()
        attrs = [p.lower() for p in parts[1:]]
        secure = any(a == "secure" for a in attrs)
        http_only = any(a == "httponly" for a in attrs)
        samesite = next(
            (p.split("=", 1)[1].strip() for p in attrs if p.startswith("samesite=")),
            None,
        )

        cookies.append(
            {
                "name": name,
                "secure": secure,
                "http_only": http_only,
                "samesite": samesite,
            }
        )

        missing_flags = []
        if not secure:
            missing_flags.append("Secure")
            penalty += 4
        if not http_only:
            missing_flags.append("HttpOnly")
            penalty += 4
        if not samesite:
            missing_flags.append("SameSite")
            penalty += 3

        if missing_flags:
            findings.append(
                build_finding(
                    f"Cookie '{name}' missing {', '.join(missing_flags)}",
                    "medium" if not secure or not http_only else "low",
                    "A Set-Cookie response is missing recommended security attributes.",
                    "Set Secure, HttpOnly, and SameSite on session and sensitive cookies.",
                    name,
                )
            )

    return {"cookies": cookies, "findings": findings, "penalty": min(penalty, 24)}


def detect_waf_cdn(headers):
    joined = " ".join(f"{k}:{v}".lower() for k, v in headers.items())
    detected = []
    for name, sigs in WAF_CDN_SIGNATURES.items():
        if any(sig in joined for sig in sigs):
            detected.append(name)
    return detected


def detect_technologies(html):
    normalized = html.lower()
    return [tech for tech, sig in TECH_SIGNATURES.items() if sig in normalized]


def analyze_forms(soup, base_url):
    forms, findings = [], []
    penalty = 0

    for form in soup.find_all("form"):
        method = (form.get("method") or "get").lower()
        action = urljoin(base_url, form.get("action") or "")
        inputs = []
        has_password = False

        for tag in form.find_all("input"):
            input_type = tag.get("type") or "text"
            has_password = has_password or input_type == "password"
            inputs.append({"name": tag.get("name"), "type": input_type})

        forms.append({"action": action, "method": method, "inputs": inputs})

        if method == "get" and has_password:
            penalty += 18
            findings.append(
                build_finding(
                    "Password form uses GET",
                    "high",
                    "A password input appears in a form submitted with GET.",
                    "Submit sensitive forms with POST over HTTPS.",
                    action,
                )
            )
        elif method == "get" and inputs:
            penalty += 4
            findings.append(
                build_finding(
                    "Interactive form uses GET",
                    "low",
                    "A form submits input through the URL query string.",
                    "Use POST for forms that may carry user or business data.",
                    action,
                )
            )

    return {"forms": forms, "findings": findings, "penalty": penalty}


def extract_parameter_urls(soup, base_url):
    urls = []
    for link in soup.find_all("a"):
        href = link.get("href")
        if href and "?" in href:
            urls.append(urljoin(base_url, href))
    return list(dict.fromkeys(urls))


def extract_sitemap_urls(content):
    soup = BeautifulSoup(content, "xml")
    return [
        loc.get_text(strip=True)
        for loc in soup.find_all("loc")
        if loc.get_text(strip=True)
    ]


# ============================================
# TLS / DNS / SUBDOMAIN HELPERS
# ============================================


def _parse_cert_name(name_tuples):
    """Turn cert subject/issuer tuple structure into a flat dict."""
    result = {}
    for rdn in name_tuples or ():
        for key, value in rdn:
            result[key] = value
    return result


def inspect_tls(hostname: str, port: int = 443):
    """Inspect the TLS certificate and negotiated protocol for a host."""
    context = ssl.create_default_context()
    try:
        with socket.create_connection(
            (hostname, port), timeout=settings.tls_timeout
        ) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as tls_sock:
                cert = tls_sock.getpeercert()
                version = tls_sock.version()
                cipher = tls_sock.cipher()
    except ssl.SSLCertVerificationError as exc:
        raise HTTPException(status_code=502, detail=f"Certificate verification failed: {exc}")
    except (socket.timeout, TimeoutError):
        raise HTTPException(status_code=504, detail="TLS handshake timed out.")
    except (socket.gaierror, ConnectionRefusedError, OSError) as exc:
        raise HTTPException(status_code=502, detail=f"Could not establish TLS connection: {exc}")

    subject = _parse_cert_name(cert.get("subject"))
    issuer = _parse_cert_name(cert.get("issuer"))

    not_after_raw = cert.get("notAfter")
    not_before_raw = cert.get("notBefore")
    days_to_expiry = None
    expired = None
    if not_after_raw:
        try:
            not_after = datetime.datetime.strptime(
                not_after_raw, "%b %d %H:%M:%S %Y %Z"
            ).replace(tzinfo=datetime.timezone.utc)
            now = datetime.datetime.now(datetime.timezone.utc)
            days_to_expiry = (not_after - now).days
            expired = now > not_after
        except ValueError:
            pass

    san = [entry[1] for entry in cert.get("subjectAltName", ()) if entry]

    return {
        "host": hostname,
        "port": port,
        "tls_version": version,
        "cipher": cipher[0] if cipher else None,
        "issuer": issuer.get("organizationName") or issuer.get("commonName"),
        "issuer_details": issuer,
        "subject": subject.get("commonName"),
        "subject_alt_names": san,
        "valid_from": not_before_raw,
        "valid_until": not_after_raw,
        "days_to_expiry": days_to_expiry,
        "expired": expired,
    }


def tls_findings(tls: dict):
    findings = []
    penalty = 0
    version = (tls.get("tls_version") or "").upper()
    days = tls.get("days_to_expiry")

    if version in ("TLSV1", "TLSV1.0", "TLSV1.1", "SSLV3"):
        penalty += 14
        findings.append(
            build_finding(
                "Outdated TLS protocol",
                "high",
                f"The server negotiated {tls.get('tls_version')}, which is deprecated.",
                "Disable TLS 1.1 and below; require TLS 1.2 or 1.3.",
                tls.get("tls_version"),
            )
        )

    if tls.get("expired"):
        penalty += 20
        findings.append(
            build_finding(
                "Expired TLS certificate",
                "high",
                "The presented certificate has already expired.",
                "Renew the certificate immediately.",
                tls.get("valid_until"),
            )
        )
    elif days is not None and days <= 14:
        penalty += 8
        findings.append(
            build_finding(
                "TLS certificate expiring soon",
                "medium",
                f"The certificate expires in {days} day(s).",
                "Renew the certificate before it expires and automate renewal.",
                tls.get("valid_until"),
            )
        )

    return {"findings": findings, "penalty": penalty}


def _build_resolver():
    resolver = dns.resolver.Resolver()
    resolver.lifetime = settings.dns_timeout
    resolver.timeout = settings.dns_timeout
    if settings.dns_nameservers:
        resolver.nameservers = settings.dns_nameservers
    return resolver


def lookup_dns(domain: str, record_types=("A", "AAAA", "MX", "NS", "TXT")):
    if not _DNS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="DNS lookups are unavailable (dnspython is not installed).",
        )

    resolver = _build_resolver()

    records = {}
    for rtype in record_types:
        try:
            answers = resolver.resolve(domain, rtype)
            records[rtype] = sorted(r.to_text() for r in answers)
        except (
            dns.resolver.NoAnswer,
            dns.resolver.NXDOMAIN,
            dns.resolver.NoNameservers,
            dns.resolver.LifetimeTimeout,
            Exception,
        ):
            records[rtype] = []
    return records


def _resolves(hostname: str) -> str | None:
    """Return the first A address for a host, or None. Strict timeout."""
    if _DNS_AVAILABLE:
        try:
            resolver = _build_resolver()
            # Short per-candidate budget so a sweep stays responsive.
            resolver.lifetime = min(settings.dns_timeout, 3.0)
            resolver.timeout = min(settings.dns_timeout, 3.0)
            answers = resolver.resolve(hostname, "A")
            return answers[0].to_text() if answers else None
        except Exception:
            return None

    original = socket.getdefaulttimeout()
    socket.setdefaulttimeout(min(settings.dns_timeout, 3.0))
    try:
        return socket.gethostbyname(hostname)
    except (socket.gaierror, OSError):
        return None
    finally:
        socket.setdefaulttimeout(original)


def resolve_subdomains(candidates):
    """Resolve subdomain candidates concurrently; return list of resolved ones."""
    resolved = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        results = pool.map(lambda h: (h, _resolves(h)), candidates)
        for host, ip in results:
            if ip:
                resolved.append({"subdomain": host, "ip": ip})
    return resolved


# ============================================
# BASIC ROUTES
# ============================================

MODULE_LIST = [
    {"endpoint": "assessment", "name": "Full Assessment", "description": "Complete recon pass with scoring, findings, TLS, cookies, and recommendations."},
    {"endpoint": "headers", "name": "Header Audit", "description": "Collects HTTP response headers, cookie flags, and WAF/CDN hints."},
    {"endpoint": "forms", "name": "Form Mapper", "description": "Extracts forms and inputs."},
    {"endpoint": "tech", "name": "Tech Fingerprint", "description": "Detects common technology signatures."},
    {"endpoint": "robots", "name": "Robots Review", "description": "Fetches robots.txt."},
    {"endpoint": "sitemap", "name": "Sitemap Pull", "description": "Fetches sitemap.xml."},
    {"endpoint": "subdomains", "name": "Subdomain Sweep", "description": "Generates and resolves common subdomain candidates."},
    {"endpoint": "params", "name": "Parameter Finder", "description": "Finds links containing query parameters."},
    {"endpoint": "tls", "name": "TLS Inspector", "description": "Inspects the TLS certificate, expiry, and protocol version."},
    {"endpoint": "dns", "name": "DNS Records", "description": "Resolves A, AAAA, MX, NS, and TXT records."},
]


@app.get("/")
def home():
    return {
        "message": "Hacktrek WebCrawler API running",
        "version": app.version,
        "modules": [m["endpoint"] for m in MODULE_LIST],
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "Hacktrek WebCrawler API",
        "version": app.version,
        "dns_available": _DNS_AVAILABLE,
    }


@app.get("/modules")
def modules():
    return {"modules": MODULE_LIST}


@app.get("/logs")
def logs(url: str | None = Query(None, description="Target URL of the scan to stream logs for")):
    # Scoping by the raw target string (the same value the frontend polls with)
    # keeps concurrent scans for different targets from leaking into each other.
    return {"logs": get_logs(scan_id=url)}


# ============================================
# FULL ASSESSMENT
# ============================================


@app.get("/assessment")
def full_assessment(url: str = Query(..., description="Target URL or domain")):
    try:
        clear_logs(scan_id=url)
        add_log("[+] Starting full reconnaissance assessment...")

        target_url = normalize_url(url)
        domain = extract_domain(target_url)
        hostname = get_hostname(target_url)
        add_log(f"[+] Target normalized: {target_url}")

        response, soup = fetch_html(target_url)
        headers = dict(response.headers)
        html = response.text
        add_log(f"[+] Base response collected: {response.status_code}")

        header_analysis = analyze_headers(headers)
        cookie_analysis = analyze_cookies(response)
        form_analysis = analyze_forms(soup, target_url)
        technologies = detect_technologies(html)
        parameter_urls = extract_parameter_urls(soup, target_url)
        waf_cdn = detect_waf_cdn(headers)
        add_log(f"[+] WAF/CDN detected: {', '.join(waf_cdn) or 'none'}")

        # ---- TLS summary (best effort) ---------------------------------- #
        tls_summary = None
        tls_extra = {"findings": [], "penalty": 0}
        if urlparse(target_url).scheme == "https":
            try:
                tls_summary = inspect_tls(hostname)
                tls_extra = tls_findings(tls_summary)
                add_log(f"[+] TLS: {tls_summary.get('tls_version')} "
                        f"(expires in {tls_summary.get('days_to_expiry')} days)")
            except HTTPException as tls_err:
                tls_summary = {"error": tls_err.detail}
                add_log(f"[-] TLS inspection failed: {tls_err.detail}")

        robots_url = target_url.rstrip("/") + "/robots.txt"
        sitemap_url = target_url.rstrip("/") + "/sitemap.xml"
        robots_result = {"url": robots_url, "status_code": None, "available": False, "content_preview": ""}
        sitemap_result = {"url": sitemap_url, "status_code": None, "available": False, "urls": []}
        findings = []
        penalty = (
            header_analysis["penalty"]
            + form_analysis["penalty"]
            + cookie_analysis["penalty"]
            + tls_extra["penalty"]
        )

        try:
            robots_response = safe_fetch(robots_url)
            robots_result = {
                "url": robots_url,
                "status_code": robots_response.status_code,
                "available": robots_response.status_code == 200,
                "content_preview": robots_response.text[:1200],
            }
            if robots_response.status_code == 200 and "Disallow:" in robots_response.text:
                findings.append(
                    build_finding(
                        "robots.txt exposes disallowed paths",
                        "info",
                        "The robots file lists paths that may be worth reviewing.",
                        "Treat robots.txt entries as public metadata and avoid exposing sensitive path names.",
                        robots_url,
                    )
                )
        except HTTPException as robots_error:
            robots_result["error"] = robots_error.detail

        try:
            sitemap_response = safe_fetch(sitemap_url)
            sitemap_urls = extract_sitemap_urls(sitemap_response.text)
            sitemap_result = {
                "url": sitemap_url,
                "status_code": sitemap_response.status_code,
                "available": sitemap_response.status_code == 200,
                "urls": sitemap_urls[:50],
            }
        except HTTPException as sitemap_error:
            sitemap_result["error"] = sitemap_error.detail

        if parameter_urls:
            penalty += min(len(parameter_urls) * 2, 14)
            findings.append(
                build_finding(
                    "Parameterized URLs discovered",
                    "medium",
                    "The crawler found links with query parameters that may need validation testing.",
                    "Review parameter handling for input validation, authorization checks, and reflected output.",
                    f"{len(parameter_urls)} URLs",
                )
            )

        if response.status_code >= 500:
            penalty += 16
            findings.append(
                build_finding(
                    "Server error response",
                    "high",
                    "The target returned a 5xx response during assessment.",
                    "Review server logs and error handling for the requested route.",
                    str(response.status_code),
                )
            )
        elif response.status_code >= 400:
            penalty += 8
            findings.append(
                build_finding(
                    "Client error response",
                    "medium",
                    "The target returned a 4xx response during assessment.",
                    "Confirm the scanned URL is correct and that public routes respond as expected.",
                    str(response.status_code),
                )
            )

        findings = (
            header_analysis["findings"]
            + cookie_analysis["findings"]
            + tls_extra["findings"]
            + form_analysis["findings"]
            + findings
        )
        risk_score = max(0, 100 - penalty)

        if risk_score >= 85:
            risk_level = "Low"
        elif risk_score >= 65:
            risk_level = "Moderate"
        elif risk_score >= 40:
            risk_level = "High"
        else:
            risk_level = "Critical"

        recommendations = list(
            dict.fromkeys(
                f["recommendation"] for f in findings if f.get("recommendation")
            )
        )

        add_log(f"[+] Findings generated: {len(findings)}")
        add_log(f"[+] Assessment score: {risk_score}/100")
        add_log("[+] Full assessment completed")

        return {
            "module": "Full Assessment",
            "target": target_url,
            "domain": domain,
            "status_code": response.status_code,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "summary": {
                "headers_present": len(header_analysis["present"]),
                "headers_missing": len(header_analysis["missing"]),
                "forms_found": len(form_analysis["forms"]),
                "technologies_found": len(technologies),
                "parameterized_urls": len(parameter_urls),
                "sitemap_urls": len(sitemap_result["urls"]),
                "cookies_found": len(cookie_analysis["cookies"]),
                "waf_cdn_found": len(waf_cdn),
                "findings": len(findings),
            },
            "security_headers": {
                "present": header_analysis["present"],
                "missing": header_analysis["missing"],
            },
            "cookies": cookie_analysis["cookies"],
            "waf_cdn": waf_cdn,
            "tls": tls_summary,
            "technologies": technologies,
            "forms": form_analysis["forms"],
            "parameter_urls": parameter_urls[:50],
            "robots": robots_result,
            "sitemap": sitemap_result,
            "findings": findings,
            "recommendations": recommendations,
        }

    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - safety net
        add_log(f"[-] Error: {exc}")
        return JSONResponse(status_code=500, content={"error": str(exc)})


# ============================================
# HEADER SCANNER
# ============================================


@app.get("/headers")
def header_scanner(url: str = Query(..., description="Target URL or domain")):
    try:
        clear_logs(scan_id=url)
        add_log("[+] Starting header scan...")

        url = normalize_url(url)
        add_log(f"[+] Connecting to {url}")

        response = safe_fetch(url)
        headers = dict(response.headers)
        add_log("[+] Headers collected")

        header_analysis = analyze_headers(headers)
        cookie_analysis = analyze_cookies(response)
        waf_cdn = detect_waf_cdn(headers)
        add_log("[+] Scan completed")

        return {
            "url": url,
            "status_code": response.status_code,
            "headers": headers,
            "security_headers": {
                "present": header_analysis["present"],
                "missing": header_analysis["missing"],
            },
            "cookies": cookie_analysis["cookies"],
            "waf_cdn": waf_cdn,
        }

    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        add_log(f"[-] Error: {exc}")
        return JSONResponse(status_code=500, content={"error": str(exc)})


# ============================================
# FORM EXTRACTOR
# ============================================


@app.get("/forms")
def form_extractor(url: str = Query(..., description="Target URL or domain")):
    try:
        clear_logs(scan_id=url)
        add_log("[+] Starting form extraction...")

        url = normalize_url(url)
        response, soup = fetch_html(url)
        add_log("[+] Parsing HTML...")

        result = analyze_forms(soup, url)
        add_log(f"[+] Forms found: {len(result['forms'])}")
        add_log("[+] Extraction completed")

        return {
            "url": url,
            "forms_found": len(result["forms"]),
            "forms": result["forms"],
        }

    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        add_log(f"[-] Error: {exc}")
        return JSONResponse(status_code=500, content={"error": str(exc)})


# ============================================
# TECHNOLOGY DETECTOR
# ============================================


@app.get("/tech")
def tech_detector(url: str = Query(..., description="Target URL or domain")):
    try:
        clear_logs(scan_id=url)
        add_log("[+] Starting technology detection...")

        url = normalize_url(url)
        response = safe_fetch(url)
        technologies = detect_technologies(response.text)
        for tech in technologies:
            add_log(f"[+] Detected: {tech}")
        add_log("[+] Detection completed")

        return {"url": url, "technologies": technologies}

    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        add_log(f"[-] Error: {exc}")
        return JSONResponse(status_code=500, content={"error": str(exc)})


# ============================================
# ROBOTS.TXT
# ============================================


@app.get("/robots")
def robots_scanner(url: str = Query(..., description="Target URL or domain")):
    try:
        clear_logs(scan_id=url)
        add_log("[+] Fetching robots.txt...")

        url = normalize_url(url)
        robots_url = url.rstrip("/") + "/robots.txt"
        response = safe_fetch(robots_url)
        add_log(f"[+] Status Code: {response.status_code}")
        add_log("[+] robots.txt fetched")

        return {
            "robots_url": robots_url,
            "status_code": response.status_code,
            "content": response.text,
        }

    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        add_log(f"[-] Error: {exc}")
        return JSONResponse(status_code=500, content={"error": str(exc)})


# ============================================
# SITEMAP
# ============================================


@app.get("/sitemap")
def sitemap_scanner(url: str = Query(..., description="Target URL or domain")):
    try:
        clear_logs(scan_id=url)
        add_log("[+] Fetching sitemap.xml...")

        url = normalize_url(url)
        sitemap_url = url.rstrip("/") + "/sitemap.xml"
        response = safe_fetch(sitemap_url)
        add_log(f"[+] Status Code: {response.status_code}")
        add_log("[+] Sitemap fetched")

        return {
            "sitemap_url": sitemap_url,
            "status_code": response.status_code,
            "content": response.text,
            "urls": extract_sitemap_urls(response.text)[:100],
        }

    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        add_log(f"[-] Error: {exc}")
        return JSONResponse(status_code=500, content={"error": str(exc)})


# ============================================
# SUBDOMAIN SCANNER (now resolves candidates)
# ============================================


@app.get("/subdomains")
def subdomain_scanner(url: str = Query(..., description="Target URL or domain")):
    try:
        clear_logs(scan_id=url)
        add_log("[+] Starting subdomain sweep...")

        domain = extract_domain(url)
        common = ["www", "mail", "admin", "api", "dev", "test", "beta", "blog", "shop", "support"]
        candidates = [f"{sub}.{domain}" for sub in common]
        add_log(f"[+] Candidate subdomains generated: {len(candidates)}")

        add_log("[+] Resolving candidates...")
        resolved = resolve_subdomains(candidates)
        add_log(f"[+] Resolved subdomains: {len(resolved)}")

        return {
            "target": domain,
            "subdomains_found": len(candidates),
            "subdomains": candidates,
            "resolved": resolved,
            "resolved_count": len(resolved),
        }

    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        add_log(f"[-] Error: {exc}")
        return JSONResponse(status_code=500, content={"error": str(exc)})


# ============================================
# URL PARAMETER EXTRACTOR
# ============================================


@app.get("/params")
def parameter_extractor(url: str = Query(..., description="Target URL or domain")):
    try:
        clear_logs(scan_id=url)
        add_log("[+] Starting parameter extraction...")

        url = normalize_url(url)
        response, soup = fetch_html(url)
        found = extract_parameter_urls(soup, url)
        add_log(f"[+] URLs with parameters found: {len(found)}")
        add_log("[+] Extraction completed")

        return {
            "url": url,
            "parameters_found": len(found),
            "parameter_urls": found,
        }

    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        add_log(f"[-] Error: {exc}")
        return JSONResponse(status_code=500, content={"error": str(exc)})


# ============================================
# TLS / SSL INSPECTOR
# ============================================


@app.get("/tls")
@app.get("/ssl")
def tls_inspector(url: str = Query(..., description="Target URL or domain")):
    try:
        clear_logs(scan_id=url)
        add_log("[+] Starting TLS inspection...")

        target_url = normalize_url(url)
        hostname = get_hostname(target_url)
        parsed = urlparse(target_url)
        port = parsed.port or 443
        add_log(f"[+] Connecting to {hostname}:{port} over TLS...")

        tls = inspect_tls(hostname, port)
        extra = tls_findings(tls)
        add_log(f"[+] TLS {tls.get('tls_version')} negotiated")
        add_log("[+] TLS inspection completed")

        return {
            "url": target_url,
            "host": hostname,
            "tls": tls,
            "findings": extra["findings"],
        }

    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        add_log(f"[-] Error: {exc}")
        return JSONResponse(status_code=500, content={"error": str(exc)})


# ============================================
# DNS RECORDS
# ============================================


@app.get("/dns")
def dns_records(url: str = Query(..., description="Target URL or domain")):
    try:
        clear_logs(scan_id=url)
        add_log("[+] Starting DNS lookup...")

        domain = extract_domain(url)
        # extract_domain may include a port; strip it for DNS.
        hostname = domain.split(":")[0]
        add_log(f"[+] Resolving records for {hostname}...")

        records = lookup_dns(hostname)
        total = sum(len(v) for v in records.values())
        add_log(f"[+] DNS records found: {total}")
        add_log("[+] DNS lookup completed")

        return {
            "domain": hostname,
            "records": records,
            "records_found": total,
        }

    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        add_log(f"[-] Error: {exc}")
        return JSONResponse(status_code=500, content={"error": str(exc)})
