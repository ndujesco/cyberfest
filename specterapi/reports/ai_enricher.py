import json
import os
from pathlib import Path


def _load_env():
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


_load_env()

from core.finding import Finding


def _get_client():
    from google import genai
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY environment variable not set. "
            "Get a free key at https://aistudio.google.com/app/apikey"
        )
    return genai.Client(api_key=api_key)


def enrich_findings(findings: list[Finding], target: str) -> dict:
    """
    Returns a dict with:
      - "executive_summary": str
      - "findings": {finding_id: {description, business_impact, technical_details, remediation}}
    Falls back to empty dict if GEMINI_API_KEY is not set or call fails.
    """
    if not findings:
        return {}

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {}

    findings_payload = [
        {
            "id": f.id,
            "title": f.title,
            "severity": f.severity.value,
            "module": f.module,
            "endpoint": f.endpoint,
            "evidence": f.evidence,
            "cwe": f.cwe or "unknown",
            "cvss": f.cvss,
        }
        for f in findings
    ]

    prompt = f"""You are a professional API security analyst writing a penetration testing report.
Target: {target}

Below are security findings from an automated scan. For each finding, provide a JSON response with:
1. An overall "executive_summary" (2-3 sentences, non-technical, suitable for management)
2. Per-finding enrichment under "findings" keyed by finding ID, each containing:
   - "description": Clear explanation of what was found (2-3 sentences)
   - "business_impact": Real-world risk to the business (1-2 sentences)
   - "technical_details": Technical explanation for developers (2-3 sentences)
   - "remediation": Concrete fix steps (2-4 bullet points as a single string, use • as separator)

Findings:
{json.dumps(findings_payload, indent=2)}

Respond ONLY with valid JSON in this exact format:
{{
  "executive_summary": "...",
  "findings": {{
    "<id>": {{
      "description": "...",
      "business_impact": "...",
      "technical_details": "...",
      "remediation": "• step1 • step2 • step3"
    }}
  }}
}}"""

    try:
        client = _get_client()
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        text = response.text.strip()

        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        return json.loads(text)
    except Exception as e:
        print(f"[AI enrichment skipped: {e}]")
        return {}
