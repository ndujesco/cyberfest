# Zer0day Saints — Security Scanner

Hackathon demo for **Cyberfest**. The concept: 10 individual open-source security tool ideas, clustered into 3 unified tools that share a domain, a target, and an operator workflow. Each cluster is a single tool with a coherent attack narrative — not a bundle of scripts.

---

## The Three Clusters

| # | Tool | Constituent tools | Domain |
|---|------|-------------------|--------|
| 1 | **SpecterAPI** | GhostRoutes · TokenHunt · IDORacle · SockPuppet | Web & API Security |
| 2 | **ChainBreak ★** *(recommended)* | KeyFlare · PipeBreak · ConfuseCheck | Supply Chain & DevSecOps |
| 3 | **PathForge** | TerraTarget · BlastMap · ReportForge | Cloud & Pentest Reporting |

### SpecterAPI — Full-spectrum API attack surface suite
Covers the three kinds of API attack surface every modern app has: hidden REST/GraphQL endpoints, broken identity flows, and real-time WebSocket channels. Workflow: **discover shadow endpoints → break auth → test object authorisation → fuzz WebSocket channels**. Closest existing tool is Burp Suite, but that requires manual work at each step with no IDOR-first or WebSocket-first mode.

### ChainBreak ★ — Developer supply chain & pipeline security auditor
A real supply chain attack hits three vectors at once: plants a malicious package (ConfuseCheck), injects into the CI workflow that installs it (PipeBreak), and exfiltrates the secrets that workflow had access to (KeyFlare). No existing tool covers all three. Workflow: **audit dependencies for confusion → scan CI/CD for injection → map secret blast radius**. Supply chain security is the industry's hottest topic post-SolarWinds and XZ Utils — judges immediately understand the stakes.

### PathForge — End-to-end attack path intelligence & reporting
Answers the same question from three vantage points: what can an attacker reach, and how bad is it? TerraTarget predicts attack paths *before* compromise (from IaC). BlastMap maps reachability *after* initial access (from a live host). ReportForge converts both into a professional deliverable. Think open-source BloodHound for the cloud era. Workflow: **predict paths from IaC → confirm paths post-access → generate narrative report**.

---

## What's in this repo

```
cyberfest/
├── index.html          # original standalone demo (no build step needed)
├── frontend/           # Vite + React port of the demo (mock data, same behaviour)
└── backend/            # Express API — fetches a real URI and analyses it with Claude
```

### Frontend (`frontend/`)

A pixel-perfect React port of `index.html`. It is a **mock** — all findings, scores, and scan timelines are hardcoded to demonstrate the full demo flow without making any network calls.

**Demo flow (keyboard-driven):**
1. Opens on the landing screen with a typewriter effect typing the target URL
2. Press `Space` → triggers the ChainBreak scan animation (3 phases with live progress bars)
3. Scan completes → dashboard with risk score gauge + findings for ChainBreak
4. `Space` again → reveals all ChainBreak findings
5. `Space` → switches to SpecterAPI tab with its findings
6. `Space` → switches to PathForge tab, animates the step-by-step attack path (S3 → Lambda → Secrets Manager → RDS), then shows findings
7. `Space` → opens the Full Report modal with PDF export and JSON copy

You can also click the nav tabs directly to switch tools at any time.

### Backend (`backend/`)

A real Express server with one endpoint:

```
POST /api/scan
Content-Type: application/json

{ "uri": "https://github.com/owner/repo" }
```

**What it actually does:**

1. **GitHub URLs** — uses the GitHub API to fetch the repository's file tree, filters to security-relevant files (CI/CD workflows, Terraform, Dockerfiles, dependency manifests, config files), and fetches up to 25 of them
2. **Any other URL** — fetches the raw HTTP response body
3. Sends the collected content to **Claude** (`claude-sonnet-4-6`) with a security analyst system prompt
4. Returns a structured JSON report:

```json
{
  "metadata": { "generated": "...", "scanner": "Zer0day Saints", "totalFindings": 4 },
  "summary": { "critical": 2, "high": 1, "medium": 1 },
  "tools": [{
    "id": "scan",
    "riskScore": 8.7,
    "findings": [{
      "id": "f1",
      "sev": "critical",
      "title": "...",
      "loc": "...",
      "what": "plain-English explanation",
      "impact": "business impact",
      "tech": "technical detail",
      "fix": "remediation steps"
    }]
  }]
}
```

The frontend and backend are **independent** — the frontend demo does not call the backend.

---

## Running locally

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### Backend

```bash
cp backend/.env.example backend/.env
# add your ANTHROPIC_API_KEY (and optionally GITHUB_TOKEN)

cd backend
npm install
npm run dev
# → http://localhost:3001
```

**Test the endpoint:**

```bash
curl -X POST http://localhost:3001/api/scan \
  -H "Content-Type: application/json" \
  -d '{"uri": "https://github.com/owner/repo"}'
```

### Health check

```bash
curl http://localhost:3001/health
# → {"ok":true}
```

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API key from console.anthropic.com |
| `GITHUB_TOKEN` | No | GitHub PAT — increases rate limit from 60 to 5000 req/hr |
| `PORT` | No | Backend port (default `3001`) |

---

## Philosophy

> *Every great open source security tool was built by one engineer who was frustrated — by a missing capability, an expensive tool, a broken standard, or wasted time. None started as a company. All became industry standards through community-driven development.*

| Pattern | Tools that embody it |
|---------|---------------------|
| Democratise expensive expertise | SpecterAPI, BlastMap, ReportForge |
| Scratch your own itch | KeyFlare, SockPuppet, IDORacle |
| Visibility before defence | SpecterAPI, TerraTarget, BlastMap |
| Make the abstract concrete | KeyFlare, ConfuseCheck, PipeBreak |
| Community compounds the tool | All three clusters |
