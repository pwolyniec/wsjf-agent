"""tools/score.py — Call Claude via Claude Code CLI to infer WSJF scores from descriptions."""
from __future__ import annotations
import json
import os
import shutil
import subprocess


def _find_node_bin_dir() -> str | None:
    """Find the fnm-managed Node bin directory."""
    fnm_dir = os.path.expanduser("~/Library/Application Support/fnm/node-versions")
    if os.path.isdir(fnm_dir):
        for version in sorted(os.listdir(fnm_dir), reverse=True):
            bin_dir = os.path.join(fnm_dir, version, "installation", "bin")
            if os.path.isdir(bin_dir):
                return bin_dir
    return None


def _find_claude() -> tuple[str, dict]:
    """Resolve the claude CLI binary and return (path, env) with Node on PATH."""
    env = os.environ.copy()
    node_bin = _find_node_bin_dir()
    if node_bin:
        env["PATH"] = node_bin + os.pathsep + env.get("PATH", "")
    found = shutil.which("claude", path=env.get("PATH"))
    if found:
        return found, env
    raise FileNotFoundError(
        "claude CLI not found. Install it with: npm install -g @anthropic-ai/claude-code"
    )


def score_items(prompt_template: str, items_json: str) -> list[dict]:
    claude_bin, env = _find_claude()
    prompt = prompt_template.replace("{items_json}", items_json)
    result = subprocess.run(
        [claude_bin, "-p", prompt, "--model", "claude-haiku-4-5-20251001",
         "--output-format", "json"],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    response = json.loads(result.stdout)
    raw = response.get("result", result.stdout).strip()
    # Strip markdown fences if present
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    # Extract first JSON array from response
    start = raw.index("[")
    depth = 0
    for i, ch in enumerate(raw[start:], start):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                raw = raw[start : i + 1]
                break
    return json.loads(raw)
