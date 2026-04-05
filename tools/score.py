"""tools/score.py — Call Claude API to infer WSJF scores from descriptions."""
from __future__ import annotations
import json
import anthropic

client = anthropic.Anthropic()

def score_items(prompt_template: str, items_json: str) -> list[dict]:
    prompt = prompt_template.replace("{items_json}", items_json)
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text.strip()
    # Strip markdown fences if present
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(raw)
