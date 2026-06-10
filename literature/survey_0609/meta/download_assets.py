#!/usr/bin/env python3
"""Download survey PDFs and shallow-clone official code repositories.

All outputs stay under literature/survey_0609/.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SELECTED = ROOT / "meta" / "selected_papers.json"
PDF_DIR = ROOT / "papers"
REPO_DIR = ROOT / "repos"


def download_pdf(row: dict) -> dict:
    url = row.get("pdf_url") or ""
    out = Path(row.get("local_pdf") or "")
    result = {"id": row["id"], "title": row["title"], "url": url, "path": str(out), "status": "skipped"}
    if not url or not out:
        result["status"] = "missing_url"
        return result
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and out.stat().st_size > 1024:
        result["status"] = "exists"
        result["bytes"] = out.stat().st_size
        return result
    try:
        req = Request(url, headers={"User-Agent": "research-survey/0609 (academic literature review)"})
        with urlopen(req, timeout=90) as resp:
            data = resp.read()
        if len(data) < 1024:
            raise RuntimeError(f"too small: {len(data)} bytes")
        out.write_bytes(data)
        result["status"] = "downloaded"
        result["bytes"] = len(data)
    except Exception as exc:  # noqa: BLE001
        result["status"] = "failed"
        result["error"] = str(exc)
    time.sleep(0.25)
    return result


def clone_repo(row: dict) -> dict:
    url = row.get("code_url") or ""
    out = Path(row.get("local_repo") or "")
    result = {"id": row["id"], "title": row["title"], "url": url, "path": str(out), "status": "skipped"}
    if not url or "github.com" not in url.lower() or not out:
        result["status"] = "missing_url"
        return result
    out.parent.mkdir(parents=True, exist_ok=True)
    if (out / ".git").exists():
        result["status"] = "exists"
        return result
    cmd = ["git", "clone", "--depth", "1", "--filter=blob:none", url, str(out)]
    env = os.environ.copy()
    env.update({"GIT_ASKPASS": "", "SSH_ASKPASS": "", "GIT_TERMINAL_PROMPT": "0"})
    try:
        proc = subprocess.run(cmd, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=240, env=env)
        result["returncode"] = proc.returncode
        result["log_tail"] = proc.stdout[-1200:]
        result["status"] = "cloned" if proc.returncode == 0 else "failed"
    except Exception as exc:  # noqa: BLE001
        result["status"] = "failed"
        result["error"] = str(exc)
    return result


def main(argv: list[str]) -> int:
    mode = argv[1] if len(argv) > 1 else "all"
    rows = json.loads(SELECTED.read_text(encoding="utf-8"))
    if mode in {"all", "pdfs"}:
        manifest = [download_pdf(row) for row in rows]
        (ROOT / "meta" / "download_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print("pdfs", len(manifest), "ok", sum(x["status"] in {"downloaded", "exists"} for x in manifest))
    if mode in {"all", "repos"}:
        manifest = [clone_repo(row) for row in rows if row.get("code_url")]
        (ROOT / "meta" / "repo_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print("repos", len(manifest), "ok", sum(x["status"] in {"cloned", "exists"} for x in manifest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
