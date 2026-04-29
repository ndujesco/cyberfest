# SpecterAPI — Full-spectrum API Attack Surface Suite

**Zer0day Saints · Cyberfest Hackathon**

SpecterAPI is a Python CLI security tool that chains three attack modules — ghost endpoint discovery, OAuth exploitation, and dual-session BOLA/IDOR testing — into one continuous, session-aware workflow. What takes a manual tester an hour with four separate tools takes SpecterAPI one command.

---

## The Three Modules

| Module | Name | What it does |
|--------|------|-------------|
| `ghost` | GhostRoutes | Crawls JS bundles, extracts hidden API paths via regex sweep, probes each endpoint anonymously to detect unauthenticated access |
| `token` | TokenHunt | Walks the full OAuth 2.0 attack tree: OIDC discovery, redirect_uri bypass, PKCE enforcement, subdomain injection |
| `idor` | IDORacle | Dual-session BOLA testing — records User A's object IDs, replays every request as User B, diffs responses to confirm cross-user access |

The `chain` command runs all three in sequence, passing Ghost's discovered endpoints directly into Token and IDOR — no manual steps between modules.

---

## Why it exists

Traditional scanners test as a single identity and have no concept of resource ownership — so they miss BOLA entirely. Existing OAuth testers run one check at a time. JS endpoint extraction tools don't connect to an auth or IDOR test. SpecterAPI's core innovation is the **continuous session chain**: one SQLite session persists discovered endpoints, object IDs, and findings across all three modules.

Research basis: HackerOne disclosed reports — PayPal IDOR ($10,500), Grafana CVE-2023-3128, Badoo OAuth redirect_uri, Shopify GraphQL BOLA — confirm this three-phase workflow is how real vulnerabilities are found in practice.

---

## Usage

### Install

```bash
cd specterapi
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

### One-liner mode

```bash
# Discover hidden endpoints from JS bundles
specterapi ghost -t https://app.target.com --probe --output json

# Walk the OAuth attack tree
specterapi token -t https://auth.target.com --output pdf

# Dual-session BOLA test
specterapi idor -t https://api.target.com --user-a <tokenA> --user-b <tokenB>

# Full attack chain — ghost → token → idor in one run
specterapi chain -t https://app.target.com --user-a <tokenA> --user-b <tokenB> --output pdf
```

### Interactive REPL

```bash
specterapi
```

```
specter > use ghost
specter[ghost] > set target https://app.target.com
specter[ghost] > set depth 3
specter[ghost] > run
specter[ghost] > show endpoints
specter[ghost] > report pdf
```

### Options

| Flag | Description |
|------|-------------|
| `-t / --target` | Target base URL (required) |
| `--user-a` | User A (victim) Bearer token — required for IDOR |
| `--user-b` | User B (attacker) Bearer token — required for IDOR |
| `--depth` | JS crawl depth (default: 2) |
| `--probe` | Probe discovered endpoints anonymously |
| `--proxy` | Route through proxy, e.g. `http://127.0.0.1:8080` |
| `--delay` | Delay between requests in seconds |
| `--output` | `table` (default) · `json` · `pdf` |
| `--out-file` | Custom output file path |

---

## What each module checks

### ghost
- Crawls the target HTML for JS bundle URLs
- Regex sweep across all bundles: `fetch(`, `axios.`, `XMLHttpRequest`, template literals, string assignments — targeting `/api/`, `/v1/`, `/admin/`, `/debug/` paths
- Probes each discovered endpoint anonymously — flags unauthenticated 200s on admin/debug paths as CRITICAL, other exposed paths as HIGH

### token
- Probes `/.well-known/openid-configuration` and 5 common variants
- **redirect_uri open redirect** — sends `redirect_uri=https://attacker.example.com/catch`, confirms if server follows it
- **redirect_uri path traversal** — sends `/callback/../evil` and URL-encoded variant
- **redirect_uri subdomain injection** — sends `evil.<target-domain>/callback`
- **PKCE missing** — omits `code_challenge` entirely, checks if server still proceeds
- **PKCE plain downgrade** — sends `code_challenge_method=plain`, checks if server accepts weaker method
- **Token endpoint PKCE skip** — sends token exchange without `code_verifier`

### idor
- Records all endpoints from the session (or runs ghost inline)
- Makes GET requests as User A, extracts object IDs from path segments and JSON response bodies
- Replays each request as User B
- Diffs responses: similar body + User B 200 = read BOLA; User B DELETE 200 = destructive BOLA; User B 200 when User A got 401/403 = auth bypass

---

## Output

Every finding has a consistent schema:

```json
{
  "id": "A3F2B1C4",
  "module": "idor",
  "severity": "critical",
  "title": "BOLA — GET /api/orders/1042 accessible cross-user",
  "endpoint": "GET /api/orders/1042",
  "evidence": "User B (HTTP 200, 1,842B) accessed User A's resource. Body similarity: 94%.",
  "cwe": "CWE-639"
}
```

PDF reports are generated with ReportLab and saved to `~/.specterapi/reports/`.

---

## File structure

```
specterapi/
├── specterapi.py           # Click CLI entry point — ghost, token, idor, chain, sessions
├── core/
│   ├── session.py          # SQLite session — endpoints, objects, findings
│   ├── http_client.py      # DualClient — anon, User A, User B httpx sessions
│   ├── output.py           # Rich terminal output, banner, findings table
│   ├── finding.py          # Finding dataclass + Severity enum
│   └── repl.py             # prompt_toolkit REPL (msfconsole style)
├── modules/
│   ├── ghost/
│   │   ├── crawler.py      # Fetch HTML, extract JS bundle URLs
│   │   ├── regex_sweep.py  # Multi-pattern API path extraction from JS
│   │   └── prober.py       # Probe endpoints, classify unauthenticated access
│   ├── token/
│   │   ├── discovery.py    # OIDC/.well-known probing
│   │   ├── redirect_uri.py # Open redirect, path traversal, subdomain injection
│   │   └── pkce.py         # PKCE presence, plain downgrade, token endpoint check
│   └── idor/
│       ├── recorder.py     # Record User A's object IDs from responses
│       ├── replayer.py     # Replay requests as User B
│       └── differ.py       # Response comparison — read/delete BOLA, auth bypass
├── wordlists/
│   ├── api-endpoints.txt   # 80 common API/admin/actuator paths
│   ├── african-telco.txt   # USSD, M-Pesa, MoMo, Airtel, Paystack, Flutterwave
│   └── oauth-paths.txt     # OIDC discovery, authorize, token, JWKS, SAML paths
└── reports/
    └── pdf_renderer.py     # ReportLab PDF with severity-coloured findings
```

---

## Research basis

The attack methodology is drawn from:

| Report | Target | Severity | Bounty |
|--------|--------|----------|--------|
| IDOR — add secondary users | PayPal | Critical | $10,500 |
| IDOR — delete certifications (GraphQL) | HackerOne | Critical | $12,500 |
| IDOR — GraphQL BillingDocumentDownload | Shopify | High | $5,000 |
| CVE-2023-3128 — Azure AD OAuth email claim | Grafana | Critical | CVE |
| OAuth redirect_uri path traversal | Badoo | Critical | $4,000+ |
| PKCE optional enforcement | Multiple | High | Multiple |
| IDOR — MTN Business Africa PII | MTN Group | High | disclosed |
| Debug endpoint via JS bundle | E-commerce | High | undisclosed |

Sources: HackerOne disclosed reports · PortSwigger Web Security Academy · OWASP API Security Top 10 · Doyensec · TrustedSec · YesWeHack
