#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOKEN = secrets.token_urlsafe(32)
COMPOSE = ["docker", "compose", "-f", "compose.yml", "-f", "compose.dev.yml"]
BLOCKED_EXACT = {".env", ".env.local", ".env.production", ".env.development"}
BLOCKED_SUFFIXES = {".gguf", ".safetensors", ".onnx", ".pt", ".pth", ".pkl", ".key", ".pem", ".p12"}


def run(cmd: list[str], *, timeout: int = 1200, check: bool = False, cwd: Path = ROOT) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            env=os.environ.copy(),
        )
        output = (proc.stdout or "").strip()
        if check and proc.returncode != 0:
            raise RuntimeError(output or f"Command failed: {' '.join(cmd)}")
        return proc.returncode, output
    except FileNotFoundError:
        return 127, f"Command not found: {cmd[0]}"
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or ""
        if isinstance(out, bytes):
            out = out.decode(errors="replace")
        return 124, f"Timed out after {timeout}s\n{out}"


def git(*args: str, timeout: int = 180) -> tuple[int, str]:
    return run(["git", *args], timeout=timeout)


def current_branch() -> str:
    code, out = git("branch", "--show-current")
    return out.strip() if code == 0 else "unknown"


def status_data() -> dict[str, Any]:
    _, branch = git("branch", "--show-current")
    _, porcelain = git("status", "--porcelain")
    _, last = git("log", "-1", "--pretty=%h %s")
    _, remote = git("remote", "get-url", "origin")
    gh_code, gh_out = run(["gh", "auth", "status"], timeout=15)
    docker_code, docker_out = run(["docker", "version", "--format", "{{.Server.Version}}"], timeout=15)
    return {
        "branch": branch or "—",
        "changes": len([line for line in porcelain.splitlines() if line.strip()]),
        "last_commit": last or "—",
        "remote": remote or "—",
        "gh": "ready" if gh_code == 0 else "not authenticated",
        "docker": docker_out if docker_code == 0 else "not available",
    }


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-._")
    return value[:60]


def ensure_clean() -> None:
    code, out = git("status", "--porcelain")
    if code != 0:
        raise RuntimeError(out or "Not a Git repository")
    if out.strip():
        raise RuntimeError("Working tree is not clean. Ship or stash the current changes first.")


def start_task(name: str) -> str:
    slug = slugify(name)
    if not slug:
        raise RuntimeError("Enter a task name, for example: frontend-chat")
    ensure_clean()
    logs: list[str] = []
    for cmd in (
        ["git", "fetch", "origin"],
        ["git", "switch", "dev"],
        ["git", "pull", "--ff-only", "origin", "dev"],
    ):
        code, out = run(cmd, timeout=300)
        logs.append(f"$ {' '.join(cmd)}\n{out}")
        if code != 0:
            raise RuntimeError("\n\n".join(logs))
    branch = f"feature/{slug}"
    code, _ = git("show-ref", "--verify", "--quiet", f"refs/heads/{branch}")
    cmd = ["git", "switch", branch] if code == 0 else ["git", "switch", "-c", branch]
    code, out = run(cmd)
    logs.append(f"$ {' '.join(cmd)}\n{out}")
    if code != 0:
        raise RuntimeError("\n\n".join(logs))
    logs.append(f"\nREADY: {branch}")
    return "\n\n".join(logs)


def test_all() -> tuple[bool, str]:
    uid = str(os.getuid())
    gid = str(os.getgid())

    steps = [
        ("Compose validation", COMPOSE + ["config", "-q"], 120),
        ("Build backend + frontend", COMPOSE + ["build", "backend", "frontend"], 1800),
        (
            "Backend Ruff + Pytest",
            COMPOSE
            + [
                "run",
                "--rm",
                "--no-deps",
                "--user",
                f"{uid}:{gid}",
                "-e",
                "RUFF_CACHE_DIR=/tmp/ruff_cache",
                "-e",
                "PYTHONPATH=/app",
                "backend",
                "sh",
                "-lc",
                "ruff check app tests && python -m pytest -q -o cache_dir=/tmp/pytest_cache",
            ],
            1200,
        ),
        (
            "Frontend production build",
            COMPOSE + ["run", "--rm", "--no-deps", "frontend", "npm", "run", "build"],
            1200,
        ),
    ]

    logs: list[str] = []
    for title, cmd, timeout in steps:
        logs.append(f"=== {title} ===")
        code, out = run(cmd, timeout=timeout)
        logs.append(out or "OK")
        if code != 0:
            logs.append(f"\nFAILED: {title} (exit {code})")
            return False, "\n".join(logs)
        logs.append("PASS\n")

    # Runtime checks help when the shared stack is already running, but a stopped
    # stack does not make the source-code test suite fail.
    for url in ("http://127.0.0.1:8080/healthz", "http://127.0.0.1:8080/api/ready"):
        try:
            with urllib.request.urlopen(url, timeout=3) as response:
                logs.append(f"Runtime {url}: HTTP {response.status}")
        except Exception:
            logs.append(f"Runtime {url}: skipped (shared/local stack is not reachable)")

    return True, "\n".join(logs)

def staged_files() -> list[str]:
    code, out = git("diff", "--cached", "--name-only")
    if code != 0:
        raise RuntimeError(out)
    return [line.strip() for line in out.splitlines() if line.strip()]


def validate_staged(files: list[str]) -> None:
    blocked: list[str] = []
    huge: list[str] = []
    for name in files:
        path = Path(name)
        if name in BLOCKED_EXACT or path.suffix.lower() in BLOCKED_SUFFIXES or "models/" in name.replace("\\", "/"):
            blocked.append(name)
            continue
        full = ROOT / path
        try:
            if full.is_file() and full.stat().st_size > 50 * 1024 * 1024:
                huge.append(name)
        except OSError:
            pass
    if blocked or huge:
        git("reset")
        parts = []
        if blocked:
            parts.append("Blocked sensitive/model files:\n- " + "\n- ".join(blocked))
        if huge:
            parts.append("Files larger than 50 MB:\n- " + "\n- ".join(huge))
        raise RuntimeError("\n\n".join(parts))


def ensure_gh() -> None:
    code, out = run(["gh", "auth", "status"], timeout=20)
    if code != 0:
        raise RuntimeError("GitHub CLI is not authenticated. Run `gh auth login` once.\n" + out)


def ship(message: str, auto_merge: bool = False) -> str:
    message = message.strip()
    if not message:
        raise RuntimeError("Commit message is required.")
    branch = current_branch()
    if branch in {"main", "dev", "master", "unknown", ""} or not branch.startswith("feature/"):
        raise RuntimeError(f"Shipping is allowed only from feature/* branches. Current branch: {branch}")

    ok, test_log = test_all()
    if not ok:
        raise RuntimeError("Tests failed. Nothing was pushed.\n\n" + test_log)

    logs = [test_log, "\n=== Git ship ==="]
    code, out = git("add", "-A")
    logs.append(out)
    if code != 0:
        raise RuntimeError("\n".join(logs))
    files = staged_files()
    if not files:
        raise RuntimeError("There are no changes to ship.")
    validate_staged(files)
    code, out = git("diff", "--cached", "--check")
    logs.append(out)
    if code != 0:
        git("reset")
        raise RuntimeError("git diff --cached --check failed.\n" + out)

    code, out = git("commit", "-m", message, timeout=300)
    logs.append(f"$ git commit -m ...\n{out}")
    if code != 0:
        raise RuntimeError("\n".join(logs))

    code, out = git("push", "-u", "origin", branch, timeout=600)
    logs.append(f"$ git push -u origin {branch}\n{out}")
    if code != 0:
        raise RuntimeError("\n".join(logs))

    ensure_gh()
    code, out = run(
        ["gh", "pr", "list", "--head", branch, "--base", "dev", "--state", "open", "--json", "number,url", "--jq", '.[0] | "\\(.number) \\(.url)"'],
        timeout=60,
    )
    if code != 0:
        raise RuntimeError("\n".join(logs) + "\n" + out)

    if out.strip():
        first = out.strip().split(maxsplit=1)
        pr_number = first[0]
        pr_url = first[1] if len(first) > 1 else ""
        logs.append(f"Existing PR #{pr_number}: {pr_url}")
    else:
        code, out = run(
            ["gh", "pr", "create", "--base", "dev", "--head", branch, "--title", message, "--body", "Created by HackAlem Developer Center after local checks."],
            timeout=120,
        )
        logs.append(out)
        if code != 0:
            raise RuntimeError("\n".join(logs))
        pr_url = out.strip().splitlines()[-1]
        code, num = run(["gh", "pr", "view", pr_url, "--json", "number", "--jq", ".number"], timeout=60)
        if code != 0:
            raise RuntimeError("\n".join(logs) + "\n" + num)
        pr_number = num.strip()
        logs.append(f"PR #{pr_number}: {pr_url}")

    if auto_merge:
        logs.append("\n=== Waiting for GitHub CI ===")
        code, out = run(["gh", "pr", "checks", pr_number, "--watch", "--fail-fast"], timeout=1800)
        logs.append(out)
        if code != 0:
            raise RuntimeError("GitHub CI did not pass. PR was NOT merged.\n\n" + "\n".join(logs))
        code, out = run(["gh", "pr", "merge", pr_number, "--squash", "--delete-branch"], timeout=180)
        logs.append(out)
        if code != 0:
            raise RuntimeError("CI passed, but automatic merge failed. Merge the PR manually.\n\n" + "\n".join(logs))
        logs.append("AUTO MERGE COMPLETE: PR merged into dev.")

        # Return the local workspace to the shared dev branch automatically.
        code, out = git("switch", "dev", timeout=120)
        logs.append(f"$ git switch dev\n{out}")
        if code != 0:
            raise RuntimeError("PR was merged, but switching back to dev failed.\n\n" + "\n".join(logs))

        code, out = git("pull", "--ff-only", "origin", "dev", timeout=300)
        logs.append(f"$ git pull --ff-only origin dev\n{out}")
        if code != 0:
            raise RuntimeError("PR was merged, but updating local dev failed.\n\n" + "\n".join(logs))

        # The remote feature branch was deleted by gh; remove stale refs and the
        # now-merged local feature branch so the next task starts cleanly.
        git("fetch", "--prune", "origin", timeout=180)
        git("branch", "-D", branch, timeout=120)
        logs.append("LOCAL WORKSPACE READY: switched to updated dev and cleaned the merged feature branch.")
    else:
        logs.append("SHIP COMPLETE: pushed and PR is ready for review/CI.")

    return "\n".join(logs)


HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HackAlem Developer Center</title>
<style>
:root{font-family:Inter,system-ui,sans-serif;color:#eef2fa;background:#090b10}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 85% 0,rgba(72,105,255,.16),transparent 30rem),#090b10}.shell{max-width:1160px;margin:auto;padding:32px 20px 70px}.top{display:flex;justify-content:space-between;gap:20px;align-items:flex-start}.eyebrow{font-size:11px;letter-spacing:.15em;color:#6f8fff;font-weight:800}.top h1{margin:7px 0 8px;font-size:38px}.muted{color:#858fa3;font-size:13px}.badge{border:1px solid #28513b;background:#0d2116;color:#91e4ad;border-radius:999px;padding:7px 10px;font-size:11px}.status{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:24px 0}.card,.panel{border:1px solid #1f2635;background:#0f131a;border-radius:15px;padding:16px}.card span{display:block;color:#778196;font-size:11px}.card strong{display:block;margin-top:5px;font-size:14px;word-break:break-word}.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.panel h2{font-size:16px;margin:0 0 6px}.panel p{color:#7d879a;font-size:12px;line-height:1.55}.field{display:grid;gap:7px;margin-top:14px}.field label{font-size:11px;color:#8590a5}.field input{border:1px solid #273147;background:#0a0e15;color:#edf2ff;border-radius:10px;padding:11px 12px;outline:none}.row{display:flex;flex-wrap:wrap;gap:9px;margin-top:14px}button{border:1px solid #31406b;background:#18264e;color:#f3f6ff;border-radius:10px;padding:10px 13px;font:inherit;font-size:12px;cursor:pointer}button:hover{background:#213267}button.secondary{background:#111722;border-color:#293247}button.danger{background:#35191d;border-color:#633038;color:#ffb5b5}button:disabled{opacity:.55;cursor:wait}.terminal{margin-top:14px;border:1px solid #1c2432;background:#070a0f;border-radius:12px;min-height:280px;max-height:520px;overflow:auto;padding:14px;color:#b9c4d7;font:12px/1.55 ui-monospace,SFMono-Regular,Consolas,monospace;white-space:pre-wrap}.ok{color:#80e4a2}.warn{color:#f0ca75}.footer{margin-top:15px;color:#596478;font-size:11px}@media(max-width:800px){.grid,.status{grid-template-columns:1fr}.top{flex-direction:column}}
</style>
</head><body><main class="shell">
<div class="top"><div><div class="eyebrow">LOCAL AUTOMATION · 127.0.0.1 ONLY</div><h1>HackAlem Developer Center</h1><div class="muted">One local control panel for branch creation, tests, commit, push and Pull Requests.</div></div><div class="badge">Local-only control</div></div>
<section class="status"><div class="card"><span>Branch</span><strong id="branch">—</strong></div><div class="card"><span>Changes</span><strong id="changes">—</strong></div><div class="card"><span>GitHub CLI</span><strong id="gh">—</strong></div><div class="card"><span>Docker</span><strong id="docker">—</strong></div></section>
<section class="grid">
<article class="panel"><h2>Start task</h2><p>Requires a clean working tree. Syncs <b>dev</b> and creates <b>feature/&lt;name&gt;</b>.</p><div class="field"><label>Task name</label><input id="taskName" placeholder="frontend-chat"></div><div class="row"><button onclick="startTask()">Start task</button><button class="secondary" onclick="refreshStatus()">Refresh</button></div></article>
<article class="panel"><h2>Test & Ship</h2><p>Runs Docker validation, backend Ruff/Pytest and frontend production build before Git is touched.</p><div class="field"><label>Commit / PR message</label><input id="message" placeholder="feat: add AI chat"></div><div class="row"><button class="secondary" onclick="runTest()">Run tests</button><button onclick="ship(false)">Ship → PR</button><button class="danger" onclick="ship(true)">Ship + auto merge</button></div></article>
</section>
<div class="terminal" id="terminal">Ready.</div><div class="footer">The tool does not expose Docker through Team Console. Mutating requests require a per-launch local token.</div>
</main><script>
const TOKEN='__TOKEN__';
const term=document.getElementById('terminal');
const branchEl=document.getElementById('branch');
const changesEl=document.getElementById('changes');
const ghEl=document.getElementById('gh');
const dockerEl=document.getElementById('docker');
function setBusy(v){document.querySelectorAll('button').forEach(b=>b.disabled=v)}
async function refreshStatus(){try{const r=await fetch('/api/status');const d=await r.json();branchEl.textContent=d.branch;changesEl.textContent=d.changes;ghEl.textContent=d.gh;dockerEl.textContent=d.docker}catch(e){term.textContent=String(e)}}
async function post(path,payload={}){setBusy(true);term.textContent='Working...';try{const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-Dev-Center-Token':TOKEN},body:JSON.stringify(payload)});const d=await r.json();term.textContent=(d.ok?'✅ SUCCESS\n\n':'❌ FAILED\n\n')+(d.output||d.error||'');await refreshStatus()}catch(e){term.textContent='❌ '+String(e)}finally{setBusy(false)}}
function startTask(){post('/api/task',{name:document.getElementById('taskName').value})}
function runTest(){post('/api/test')}
function ship(autoMerge){if(autoMerge&&!confirm('Auto-merge into dev after GitHub CI passes?'))return;post('/api/ship',{message:document.getElementById('message').value,auto_merge:autoMerge})}
refreshStatus();setInterval(refreshStatus,10000);
</script></body></html>'''


class Handler(BaseHTTPRequestHandler):
    server_version = "HackAlemDevCenter/1.0"

    def _safe_host(self) -> bool:
        host = self.headers.get("Host", "")
        return host.startswith("127.0.0.1:") or host.startswith("localhost:") or host in {"127.0.0.1", "localhost"}

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        if not self._safe_host():
            self._json(403, {"error": "Host not allowed"})
            return
        if self.path == "/":
            raw = HTML.replace("__TOKEN__", TOKEN).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if self.path == "/api/status":
            self._json(200, status_data())
            return
        self._json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        if not self._safe_host():
            self._json(403, {"error": "Host not allowed"})
            return
        if self.headers.get("X-Dev-Center-Token") != TOKEN:
            self._json(403, {"error": "Invalid local token"})
            return
        try:
            size = min(int(self.headers.get("Content-Length", "0") or "0"), 64 * 1024)
            body = self.rfile.read(size) if size else b"{}"
            data = json.loads(body.decode("utf-8") or "{}")
        except Exception:
            self._json(400, {"error": "Invalid JSON"})
            return
        try:
            if self.path == "/api/task":
                output = start_task(str(data.get("name", "")))
            elif self.path == "/api/test":
                ok, output = test_all()
                if not ok:
                    self._json(200, {"ok": False, "output": output})
                    return
            elif self.path == "/api/ship":
                output = ship(str(data.get("message", "")), bool(data.get("auto_merge", False)))
            else:
                self._json(404, {"error": "Not found"})
                return
            self._json(200, {"ok": True, "output": output})
        except Exception as exc:
            self._json(200, {"ok": False, "error": str(exc)})

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("[dev-center] " + (fmt % args) + "\n")


def serve(host: str, port: int) -> None:
    if host not in {"127.0.0.1", "localhost"}:
        raise SystemExit("For safety, Developer Center can only bind to localhost.")
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"HackAlem Developer Center: http://{host}:{port}")
    print("Local-only automation service. Press Ctrl+C to stop.")
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="HackAlem Developer Center")
    sub = parser.add_subparsers(dest="command")
    serve_p = sub.add_parser("serve")
    serve_p.add_argument("--host", default="127.0.0.1")
    serve_p.add_argument("--port", type=int, default=8766)
    task_p = sub.add_parser("task")
    task_p.add_argument("name")
    sub.add_parser("test")
    ship_p = sub.add_parser("ship")
    ship_p.add_argument("message")
    ship_p.add_argument("--auto-merge", action="store_true")
    sub.add_parser("status")
    args = parser.parse_args()

    command = args.command or "serve"
    if command == "serve":
        serve(getattr(args, "host", "127.0.0.1"), getattr(args, "port", 8766))
    elif command == "status":
        print(json.dumps(status_data(), indent=2, ensure_ascii=False))
    elif command == "task":
        print(start_task(args.name))
    elif command == "test":
        ok, output = test_all()
        print(output)
        raise SystemExit(0 if ok else 1)
    elif command == "ship":
        print(ship(args.message, args.auto_merge))


if __name__ == "__main__":
    main()
