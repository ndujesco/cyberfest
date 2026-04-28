import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import axios from 'axios';
import Anthropic from '@anthropic-ai/sdk';

const app = express();
app.use(cors());
app.use(express.json());

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

// ── GitHub helpers ───────────────────────────────────────────────────────────

function parseGitHubUrl(uri) {
  const match = uri.match(/github\.com[/:]([^/]+)\/([^/.]+)/);
  return match ? { owner: match[1], repo: match[2] } : null;
}

const SECURITY_RELEVANT = [
  'package.json', 'package-lock.json', 'requirements.txt', 'pipfile',
  'gemfile', 'go.mod', 'pom.xml', 'build.gradle', 'cargo.toml',
  'dockerfile', 'docker-compose', '.env.example', '.env.sample',
  '.github/workflows', '.gitlab-ci', 'main.tf', 'variables.tf',
  'iam.tf', 'network.tf', 'security.tf', 'nginx.conf', 'apache',
  'config.yml', 'config.yaml', 'settings.py', 'config.js',
];

function isSecurityRelevant(path) {
  const p = path.toLowerCase();
  return SECURITY_RELEVANT.some(k => p.includes(k));
}

async function fetchGitHubFiles(owner, repo) {
  const headers = { 'Accept': 'application/vnd.github.v3+json', 'User-Agent': 'zer0day-saints' };
  if (process.env.GITHUB_TOKEN) headers['Authorization'] = `token ${process.env.GITHUB_TOKEN}`;

  // Try main then master as default branch
  let tree;
  for (const branch of ['HEAD', 'main', 'master']) {
    try {
      const res = await axios.get(
        `https://api.github.com/repos/${owner}/${repo}/git/trees/${branch}?recursive=1`,
        { headers, timeout: 10000 }
      );
      tree = res.data.tree || [];
      break;
    } catch { /* try next */ }
  }
  if (!tree) throw new Error(`Could not fetch repo tree for ${owner}/${repo}`);

  const relevant = tree
    .filter(f => f.type === 'blob' && isSecurityRelevant(f.path))
    .slice(0, 25);

  const results = await Promise.allSettled(
    relevant.map(async f => {
      const res = await axios.get(
        `https://api.github.com/repos/${owner}/${repo}/contents/${f.path}`,
        { headers, timeout: 8000 }
      );
      const raw = Buffer.from(res.data.content || '', 'base64').toString('utf-8');
      return { path: f.path, content: raw.slice(0, 4000) };
    })
  );

  return results
    .filter(r => r.status === 'fulfilled')
    .map(r => r.value);
}

// ── Generic URL fetch ────────────────────────────────────────────────────────

async function fetchUrl(uri) {
  const res = await axios.get(uri, {
    timeout: 12000,
    headers: { 'User-Agent': 'zer0day-saints-scanner/1.0' },
    maxRedirects: 5,
    responseType: 'text',
  });
  return String(res.data).slice(0, 30000);
}

// ── Claude analysis ──────────────────────────────────────────────────────────

const SYSTEM_PROMPT = `You are an expert security analyst specialising in supply-chain attacks, API security, cloud misconfiguration, and CI/CD hardening. You receive raw source content fetched from a target URI and must return a structured JSON security report. Be thorough but precise — only report genuine issues, not theoretical ones.`;

async function analyzeWithClaude(uri, content) {
  const today = new Date().toISOString().split('T')[0];

  const userPrompt = `Analyze the following content fetched from "${uri}" for security vulnerabilities.

<content>
${content}
</content>

Return ONLY a raw JSON object matching this schema exactly (no markdown, no explanation):

{
  "metadata": {
    "generated": "${today}",
    "scanner": "Zer0day Saints",
    "version": "1.0.0",
    "tools": 1,
    "totalFindings": <integer>
  },
  "summary": {
    "critical": <integer>,
    "high": <integer>,
    "medium": <integer>
  },
  "tools": [
    {
      "id": "scan",
      "name": "SecurityScan",
      "icon": "🔍",
      "sub": "<category e.g. Supply Chain | API Security | Cloud Config>",
      "target": "${uri}",
      "riskScore": <number 0-10 one decimal>,
      "scanTime": "<Xs>",
      "stats": { "critical": <n>, "high": <n>, "medium": <n> },
      "findings": [
        {
          "id": "f1",
          "sev": "critical|high|medium|low",
          "title": "<short imperative title>",
          "loc": "<file · line N or endpoint>",
          "what": "<plain-English explanation of what was found>",
          "impact": "<concrete business impact>",
          "tech": "<precise technical detail>",
          "fix": "<actionable remediation steps>"
        }
      ]
    }
  ]
}

Rules:
- sev must be exactly: critical, high, medium, or low
- riskScore reflects the worst-case business impact (0 = no risk, 10 = complete compromise)
- findings array must be sorted critical → high → medium → low
- Include at least 3 findings if issues exist; if the target looks clean, return 0 findings with riskScore 1.0
- totalFindings must equal findings.length`;

  const message = await anthropic.messages.create({
    model: 'claude-sonnet-4-6',
    max_tokens: 4096,
    system: SYSTEM_PROMPT,
    messages: [{ role: 'user', content: userPrompt }],
  });

  const text = message.content[0].text.trim();

  // Strip accidental markdown fences
  const cleaned = text.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '').trim();
  return JSON.parse(cleaned);
}

// ── Route ────────────────────────────────────────────────────────────────────

app.post('/api/scan', async (req, res) => {
  const { uri } = req.body;
  if (!uri || typeof uri !== 'string') {
    return res.status(400).json({ error: '`uri` (string) is required in the request body' });
  }

  console.log(`[scan] starting → ${uri}`);

  try {
    let content = '';
    const gh = parseGitHubUrl(uri);

    if (gh) {
      console.log(`[scan] GitHub repo detected: ${gh.owner}/${gh.repo}`);
      const files = await fetchGitHubFiles(gh.owner, gh.repo);
      if (files.length === 0) {
        return res.status(422).json({ error: 'No security-relevant files found in repo' });
      }
      content = files.map(f => `=== ${f.path} ===\n${f.content}`).join('\n\n');
      console.log(`[scan] fetched ${files.length} files (${content.length} chars)`);
    } else {
      console.log(`[scan] generic URL fetch`);
      content = await fetchUrl(uri);
      console.log(`[scan] fetched ${content.length} chars`);
    }

    const result = await analyzeWithClaude(uri, content);
    console.log(`[scan] analysis done — ${result.metadata?.totalFindings ?? '?'} findings`);
    res.json(result);
  } catch (err) {
    console.error('[scan] error:', err.message);
    const status = err.response?.status ?? 500;
    res.status(status >= 400 && status < 600 ? status : 500).json({ error: err.message });
  }
});

app.get('/health', (_req, res) => res.json({ ok: true }));

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => console.log(`[server] listening on http://localhost:${PORT}`));
