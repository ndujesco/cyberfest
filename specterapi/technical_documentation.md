# SpecterAPI — Technical Documentation

**Team:** Zer0day Saints  
**Event:** Cyberfest Hackathon  
**Tool:** SpecterAPI v0.1.0

---

## 1. Problem Statement

### What problem are we solving?

Modern APIs are the backbone of every web and mobile application, yet the most dangerous API vulnerabilities — Broken Object Level Authorization (BOLA/IDOR) and OAuth misconfiguration — remain systematically undetected by existing automated security tools.

This is not a knowledge gap. These vulnerability classes top the OWASP API Security Top 10 (A01 and A02) and have been confirmed in high-severity disclosures across major platforms:

| Vulnerability | Target | Impact | Payout |
|---|---|---|---|
| IDOR — cross-user resource access | PayPal | Account takeover | $10,500 |
| IDOR — GraphQL billing documents | Shopify | Financial data leak | $5,000 |
| OAuth redirect_uri open redirect | Badoo | Auth code theft | $4,000+ |
| CVE-2023-3128 — Azure AD email claim bypass | Grafana | Full account takeover | CVE |
| IDOR — PII exposure | MTN Business Africa | Mass user data exposure | Disclosed |
| Hidden debug endpoint via JS bundle | Undisclosed e-commerce | Admin access, no auth | Undisclosed |

### Why existing tools fail

There are three structural gaps in the current tooling landscape:

**Gap 1 — Single-identity testing.**  
Every mainstream scanner (Burp Suite passive scan, OWASP ZAP, Nikto) authenticates as one user and has no concept of resource ownership. BOLA requires testing *two* users against the same object — one who owns it, one who should not have access. A scanner with one session cannot make this determination. It will mark every 200 response as "accessible" and miss the ownership boundary entirely.

**Gap 2 — Disconnected toolchain.**  
An API security assessment currently requires at least four separate tools used in sequence: a JS endpoint extractor (LinkFinder), an OAuth tester (oauth2-token-hunter or manual Burp steps), a BOLA tester (custom script or manual Burp Intruder), and a report generator. Each tool has its own input format, output format, and context — a tester must manually copy endpoint lists between tools, re-authenticate per tool, and merge results by hand. This fragmentation costs time and introduces errors.

**Gap 3 — No endpoint-to-exploit continuity.**  
Hidden API paths extracted from JavaScript bundles are never automatically fed into an authorization or IDOR test. A tester who finds `/api/v2/admin/dashboard` in a JS bundle must manually carry that finding into a separate authorization check. No existing tool chains these steps.

### Who is affected?

- **Security engineers and penetration testers** who spend significant manual effort on tasks that should be automated.
- **Bug bounty hunters** who lose speed — and therefore money — to toolchain friction.
- **Product and engineering teams** whose APIs carry real BOLA and OAuth vulnerabilities that internal scans consistently miss before production.

---

## 2. Proposed Solution

SpecterAPI is a Python CLI security tool that solves all three gaps by chaining three attack modules into one continuous, session-aware workflow.

### Core concept: the session chain

A single SQLite session persists across all three attack phases. Endpoints discovered by the Ghost module are automatically available to the IDOR module — no copy-paste, no manual handoff. One command covers the full attack surface; one PDF documents every finding.

### The three modules

#### Module 1 — Ghost (Hidden Endpoint Discovery)

Ghost solves the problem of undocumented API exposure. Most production SPAs (React, Vue, Angular) bundle their entire API call surface into JavaScript files that are publicly downloadable.

Ghost crawls the target's HTML, collects every JS bundle URL, fetches each bundle, and runs a ten-pattern regex sweep across the raw JavaScript. It extracts paths referenced via `axios.get`, `fetch()`, template literals, string assignments, and generic API string literals. It then probes each discovered endpoint anonymously — no credentials — and classifies unauthenticated responses by severity:

- **CRITICAL** — unauthenticated 200 on `/admin/`, `/debug/`, `/internal/`, `/config/` paths
- **HIGH** — unauthenticated 200 on any other API endpoint
- **MEDIUM** — unexpected response codes on high-value paths

Each finding carries the source JS file it was extracted from, the HTTP method, status code, response size, and a CWE reference (CWE-284 — Improper Access Control).

#### Module 2 — Token (OAuth 2.0 Attack Tree)

Token solves the problem of manual OAuth assessment. OAuth 2.0 misconfiguration is subtle — a server may enforce PKCE on some flows but not others; redirect_uri validation may block full domains but accept path traversal or subdomain variants.

Token begins by probing the OIDC discovery endpoint (`/.well-known/openid-configuration`) across six common URL variants to map the authorization server's configuration. It then walks six distinct attack nodes against the live authorization endpoint:

1. **Open redirect** — sends `redirect_uri=https://attacker.example.com/catch`, confirms if the server follows it (CWE-601)
2. **Path traversal** — sends `/callback/../evil` and URL-encoded variant `%2F..%2F`, checks for non-4xx responses (CWE-22)
3. **Subdomain injection** — sends `evil.<target-domain>/callback`, checks if the wildcard is accepted (CWE-601)
4. **PKCE absence** — omits `code_challenge` entirely from the authorization request, checks if the server still proceeds (CWE-308)
5. **PKCE plain downgrade** — sends `code_challenge_method=plain` instead of `S256`, checks if the weaker method is accepted (CWE-916)
6. **Token endpoint PKCE skip** — sends a token exchange request without `code_verifier`, checks if the server completes the exchange (CWE-308)

#### Module 3 — IDOR / IDORacle (Dual-Session BOLA Detection)

IDOR solves the core single-identity problem. It operates two independent HTTP sessions simultaneously.

The recorder makes GET requests as User A (the victim), captures every object ID found in URL path segments and JSON response bodies — UUIDs, integers, slugs — and stores them in the session database. The replayer then iterates those object IDs and replays each request as User B (the attacker). The differ compares the two responses:

- **Read BOLA** — User B receives HTTP 200 with a response body structurally similar (>50% key overlap in JSON) to User A's response, or with response size ≥ 70% of User A's
- **Destructive BOLA** — User B's DELETE request on User A's object returns HTTP 200 or 204
- **Auth bypass** — User B receives HTTP 200 on an endpoint that returned 401 or 403 for User A

All three finding types are tagged CWE-639 (Authorization Bypass Through User-Controlled Key).

#### The `chain` command

`specterapi chain` runs Ghost → Token → IDOR in sequence within a single session and client. Ghost's discovered endpoints are directly consumed by IDOR. The full attack surface is documented in one PDF report.

### Output and reporting

Every finding from every module shares a consistent schema:

```json
{
  "id": "A3F2B1C4",
  "module": "idor",
  "severity": "critical",
  "title": "BOLA — GET /api/orders/1042 accessible cross-user",
  "endpoint": "GET /api/orders/1042",
  "evidence": "User B (HTTP 200, 1,842B) accessed User A's resource. Body similarity: 94%.",
  "cwe": "CWE-639",
  "cvss": 9.0
}
```

CVSS scores are assigned by severity tier: Critical → 9.0, High → 7.0, Medium → 5.0, Low → 3.0.

Reports export to **JSON** (structured, pipeable) or **PDF** (styled, severity-colour-coded, client-ready). PDF reports are generated with ReportLab and saved to `~/.specterapi/reports/`.

### Interactive REPL mode

For manual engagements, SpecterAPI includes an msfconsole-style REPL built on `prompt_toolkit`. Testers can load modules, set options interactively, run, inspect findings, and generate reports — all from a persistent shell with tab completion and session resumption.

---

## 3. Solution Architecture

### Technology stack

| Layer | Technology | Purpose |
|---|---|---|
| Language | Python 3.11+ | Core implementation |
| CLI framework | Click 8.x | Command parsing, subcommands, option validation |
| HTTP client | httpx (with HTTP/2) | Async, concurrent requests; supports proxy routing |
| Terminal UI | Rich 13.x | Coloured output, findings tables, progress display |
| REPL | prompt_toolkit 3.x | Interactive shell with tab completion |
| Persistence | SQLite (stdlib) | Session storage — endpoints, objects, findings |
| Report generation | ReportLab 4.x | PDF rendering with severity-colour-coded layout |
| HTML parsing | BeautifulSoup4 | JS bundle URL extraction from HTML |

### Module and file structure

```
specterapi/
├── specterapi.py           # Click CLI entry point — ghost, token, idor, chain, sessions
├── core/
│   ├── session.py          # SQLite session — endpoints, objects, findings (4 tables)
│   ├── http_client.py      # DualClient — anon, User A, User B httpx sessions
│   ├── output.py           # Rich terminal output, banner, findings table
│   ├── finding.py          # Finding dataclass + Severity enum + CVSS mapping
│   └── repl.py             # prompt_toolkit REPL (msfconsole style)
├── modules/
│   ├── ghost/
│   │   ├── crawler.py      # Async HTML crawler — extracts JS bundle URLs
│   │   ├── regex_sweep.py  # 10-pattern regex sweep across raw JS content
│   │   └── prober.py       # Anonymous endpoint probing and severity classification
│   ├── token/
│   │   ├── discovery.py    # OIDC /.well-known probing across 6 URL variants
│   │   ├── redirect_uri.py # Open redirect, path traversal, subdomain injection tests
│   │   └── pkce.py         # PKCE presence, plain downgrade, token endpoint skip tests
│   └── idor/
│       ├── recorder.py     # User A session — object ID extraction from paths + JSON bodies
│       ├── replayer.py     # User B session — replays recorded requests
│       └── differ.py       # Response comparison — read BOLA, delete BOLA, auth bypass
├── reports/
│   └── pdf_renderer.py     # ReportLab PDF generation with severity-coloured findings
└── wordlists/
    ├── api-endpoints.txt   # 80 common API/admin/actuator paths
    ├── african-telco.txt   # USSD, M-Pesa, MoMo, Airtel, Paystack, Flutterwave endpoints
    └── oauth-paths.txt     # OIDC discovery, authorize, token, JWKS, SAML paths
```

### Data model

The SQLite session database has four tables:

- **sessions** — session ID, target URL, timestamp, status
- **endpoints** — path, HTTP method, status code, auth_required flag, response size, source JS file
- **objects** — endpoint, object ID value, ID type (integer/UUID/slug), raw value
- **findings** — finding ID, module, severity, title, endpoint, evidence string, CVSS, CWE, timestamp

This schema is what enables the chain: Ghost writes to `endpoints`, IDOR reads from `endpoints` and writes to `objects` and `findings`, and the PDF renderer reads from `findings`.

### DualClient design

`DualClient` wraps three independent `httpx.AsyncClient` instances within one async context manager:

- **anon** — no credentials, used by Ghost and Token
- **client_a** — `Authorization: Bearer <USER_A_TOKEN>`, used by IDORacle recorder
- **client_b** — `Authorization: Bearer <USER_B_TOKEN>`, used by IDORacle replayer

All three share the same proxy configuration, delay, and timeout settings. This ensures the dual-session comparison is controlled — the only variable between User A and User B requests is the identity token.

### Async execution model

All HTTP operations are `async`/`await` with `asyncio`. Ghost's crawler uses `asyncio.gather` to fetch multiple HTML pages and JS bundles concurrently. The IDOR recorder and replayer operate sequentially per object ID to avoid race conditions in response comparison. The CLI entry points use `asyncio.run()` as the synchronous bridge.

### Severity and CVSS mapping

```
Severity   CVSS   Examples
CRITICAL   9.0    Unauthenticated admin access, auth code theft via open redirect
HIGH       7.0    BOLA read access, PKCE absent, path traversal not rejected
MEDIUM     5.0    PKCE plain downgrade, insufficient redirect_uri validation
LOW        3.0    Information disclosure, non-sensitive endpoint exposure
INFO       0.0    OIDC configuration enumerated (expected behaviour)
```

### Installation and invocation

```bash
# Install
cd specterapi
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

# One-liner — full attack chain
specterapi chain \
  -t https://target.com \
  --user-a <victim_token> \
  --user-b <attacker_token> \
  --output pdf \
  --out-file report.pdf

# Interactive REPL
specterapi
```

---

*SpecterAPI — Zer0day Saints · Cyberfest Hackathon*
