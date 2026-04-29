# SpecterAPI — Demo Guide

**What to record:** A 3–5 minute screen capture showing SpecterAPI finding real security issues across its three attack phases, ending with a PDF report.

---

## What the MVP does

SpecterAPI is a Python CLI security tool that chains three attack modules in one session:

| Phase | Module | What it does |
|-------|--------|-------------|
| 1 | `ghost` | Crawls the target's JS bundles, extracts hidden API endpoint paths using regex patterns, then probes each one anonymously to detect unauthenticated access |
| 2 | `token` | Probes OIDC discovery endpoints, then walks the OAuth 2.0 attack tree: open redirect in `redirect_uri`, path traversal, subdomain injection, PKCE absence, PKCE plain-method downgrade |
| 3 | `idor` | Takes two Bearer tokens (User A = victim, User B = attacker), records every object ID from User A's responses, replays each request as User B, and diffs the responses to confirm cross-user access |

The `chain` command runs all three in sequence, passing Ghost's discovered endpoints directly into IDOR — no copy-paste between tools.

Every finding has: severity (CRITICAL / HIGH / MEDIUM / LOW), CWE ID, endpoint, and evidence string. Results export to **JSON** or a styled **PDF report**.

---

## Setup (do this before recording)

### 1. Install SpecterAPI

```bash
cd specterapi
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Verify:
```bash
specterapi --help
```

### 2. Spin up a vulnerable local target

We use **crAPI** (Completely Ridiculous API) — a Docker-composed vulnerable API built specifically for BOLA/IDOR and OAuth demos.

```bash
# requires Docker Desktop running
curl -o docker-compose.yml \
  https://raw.githubusercontent.com/OWASP/crAPI/main/deploy/docker/docker-compose.yml

docker compose pull
docker compose -f docker-compose.yml --compatibility up -d
```

Wait ~60 seconds for all services to start, then open `http://localhost:8888` in your browser.

**Create two accounts** (User A = victim, User B = attacker):
1. Open `http://localhost:8888` → Sign Up → create `alice@demo.com` / `Password1!`
2. Open another browser or incognito → Sign Up → create `bob@demo.com` / `Password1!`
3. Log in as Alice, click around (add a vehicle, create a post, check the community) to generate objects
4. Copy Alice's JWT from DevTools → Application → Local Storage → `token` — this is `USER_A_TOKEN`
5. Log in as Bob, copy Bob's JWT — this is `USER_B_TOKEN`

> **Shortcut for demo only:** you can export the tokens directly:
> ```bash
> # replace with tokens copied from browser DevTools
> export USER_A="eyJhbGciOi..."
> export USER_B="eyJhbGciOi..."
> ```

---

## Demo script (screen record this)

### Step 1 — Show the banner (10 seconds)

```bash
specterapi --help
```

Point out: ghost, token, idor, chain. Two modes — one-liner and REPL.

---

### Step 2 — Ghost: find hidden endpoints (60 seconds)

```bash
specterapi ghost -t http://localhost:8888 --probe --output json --out-file ghost_findings.json
```

**What to narrate:** "Ghost crawls the React frontend, extracts API paths from the JS bundles using regex patterns — the same technique researchers use with LinkFinder — then probes each one without any credentials."

Expected output:
```
[*] Ghost — crawling http://localhost:8888
[+] Found N JS chunks
[+] Extracted M unique endpoint candidates
[!] Unauthenticated endpoint — GET /api/v2/admin/dashboard
[!] Unauthenticated endpoint — GET /api/v2/community/posts/...
FINDINGS SUMMARY
  CRITICAL  1
  HIGH      2
```

Show the JSON file:
```bash
cat ghost_findings.json | python3 -m json.tool | head -40
```

---

### Step 3 — Token: walk the OAuth attack tree (60 seconds)

```bash
specterapi token -t http://localhost:8888 --output pdf --out-file token_report.pdf
```

**What to narrate:** "Token probes the OIDC discovery endpoint, maps the authorization server's capabilities, then walks six distinct attack nodes: redirect\_uri bypass, PKCE enforcement, state parameter CSRF. This is the same checklist from the PortSwigger OAuth research and the Badoo redirect\_uri bug that paid $4,000."

Expected output:
```
[*] TOKEN — OAuth 2.0 attack surface analysis
[+] OIDC discovery found: 12 keys
[!] redirect_uri accepts arbitrary domains — auth code theft possible
[!] PKCE not enforced — authorization code interception risk
FINDINGS SUMMARY
  HIGH    2
  MEDIUM  1
```

---

### Step 4 — IDOR: dual-session BOLA test (60 seconds)

```bash
specterapi idor \
  -t http://localhost:8888 \
  --user-a "$USER_A" \
  --user-b "$USER_B"
```

**What to narrate:** "IDOR is why traditional scanners fail — they test as a single user and have no concept of resource ownership. SpecterAPI runs two simultaneous sessions: User A owns the objects, User B tries to access them. This is exactly how the PayPal IDOR was found — the $10,500 bug — and the MTN Business Africa PII leak."

Expected output:
```
[*] IDOR — dual-session test across N endpoints
[+] Captured M object references from User A
[!] BOLA — GET /api/v2/vehicle/... accessible cross-user
[!] BOLA — GET /api/v2/community/posts/... accessible cross-user
FINDINGS SUMMARY
  HIGH  2
```

---

### Step 5 — Chain: full attack in one command (30 seconds)

```bash
specterapi chain \
  -t http://localhost:8888 \
  --user-a "$USER_A" \
  --user-b "$USER_B" \
  --output pdf \
  --out-file specter_full_report.pdf
```

**What to narrate:** "One command. Ghost discovers the endpoints, Token walks the auth tree, IDOR confirms the ownership boundary. The session persists across all three modules — IDOR reuses every endpoint Ghost found. No other tool does this."

After it completes:
```bash
open specter_full_report.pdf    # macOS
# or
xdg-open specter_full_report.pdf  # Linux
```

Show the PDF on screen.

---

### Step 6 — REPL mode (optional, 30 seconds)

```bash
specterapi
```

```
specter > use ghost
specter[ghost] > set target http://localhost:8888
specter[ghost] > set depth 3
specter[ghost] > options
specter[ghost] > run
specter[ghost] > show findings
specter[ghost] > report pdf
specter[ghost] > back
specter > sessions
```

**What to narrate:** "For manual engagements — the msfconsole-style REPL. Tab completion, persistent sessions, load a previous session and keep testing."

---

### Step 7 — Review saved sessions (15 seconds)

```bash
specterapi sessions
```

Shows every session with target, timestamp, and finding count. Sessions persist to `~/.specterapi/sessions/` as SQLite files.

---

## Alternative targets (no Docker required)

If Docker isn't available, these public targets demonstrate individual modules:

| Target | Module | What it shows |
|--------|--------|---------------|
| `https://accounts.google.com` | `token` | 4 real OAuth findings (PKCE, redirect\_uri) — **verified working** |
| `https://github.com` | `ghost` | JS bundle crawling on a production SPA |
| `https://reqres.in` | `idor` | Needs two accounts — open test API |

```bash
# Token demo against Google OAuth (no accounts needed)
specterapi token -t https://accounts.google.com --output pdf --out-file google_oauth.pdf
```

This finds real issues on a live production system — powerful for a demo without needing a local environment.

---

## What to say in 30 seconds (elevator pitch)

> "Most API scanners test as a single user and miss BOLA entirely — the #1 API vulnerability since 2019. SpecterAPI chains three phases: Ghost extracts hidden endpoints from JS bundles, Token walks the full OAuth attack tree, and IDOR cross-checks resource access between two accounts. These are the exact techniques behind the PayPal $10,500 bug, the Grafana CVE-2023-3128, and the Badoo redirect_uri ATO. One command, one PDF, continuous session. That's SpecterAPI."

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `specterapi: command not found` | `source .venv/bin/activate` first |
| Ghost finds no endpoints | Target may not be a React/Vue/Angular SPA — try `https://github.com` |
| IDOR skipped | Must provide `--user-a` and `--user-b` tokens |
| PDF empty | Run at least one module first so session has findings |
| crAPI not loading | `docker compose logs` — mailhog and mongodb need to start first, ~60s |
