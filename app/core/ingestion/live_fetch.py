"""Live fetch helpers for source adapters."""

from __future__ import annotations

import json
import os
import subprocess
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


def live_fetch_enabled(force: bool = False) -> bool:
    """Return whether live fetch is enabled for ingestion adapters."""
    return force or os.getenv("CAREERCOPILOT_ENABLE_LIVE_FETCH", "0") == "1"


def fetch_text_via_curl(url: str, timeout_seconds: int = 20) -> str:
    """Fetch a URL via curl while ignoring local proxy environment variables."""
    env = os.environ.copy()
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        env.pop(key, None)

    result = subprocess.run(
        [
            "curl",
            "--max-time",
            str(timeout_seconds),
            "-L",
            "-A",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            url,
        ],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )
    return result.stdout


def build_url_with_query(base_url: str, **updates: str) -> str:
    """Return a URL with query parameters overwritten by provided values."""
    parsed = urlparse(base_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.update(updates)
    return urlunparse(parsed._replace(query=urlencode(query)))


def fetch_dewu_job_posts_via_playwright(url: str, timeout_ms: int = 60000) -> dict:
    """Load the Dewu page in Playwright and capture the signed job-post JSON response."""
    env = os.environ.copy()
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        env.pop(key, None)

    script = f"""
const {{ chromium }} = require('playwright');
(async() => {{
  const browser = await chromium.launch({{ headless: true }});
  const page = await browser.newPage();
  let payload = null;
  page.on('response', async (res) => {{
    const url = res.url();
    if (url.includes('/api/v1/search/job/posts')) {{
      try {{
        payload = await res.text();
      }} catch (e) {{}}
    }}
  }});
  await page.goto({json.dumps(url)}, {{ waitUntil: 'networkidle', timeout: {timeout_ms} }});
  await page.waitForTimeout(3000);
  await browser.close();
  if (!payload) {{
    process.stderr.write('Dewu job-post response not captured\\n');
    process.exit(2);
  }}
  process.stdout.write(payload);
}})().catch((err) => {{
  process.stderr.write(String(err));
  process.exit(1);
}});
"""
    result = subprocess.run(
        ["node", "-e", script],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )
    return json.loads(result.stdout)
