"""
WSJF Backlog Prioritization Agent
Usage:
  python agent.py --input path/or/url [--output-dir output/]
"""
import argparse, json, sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from tools.ingest import ingest
from tools.score import score_items
from tools.rank import rank
from tools.export import export_csv, export_report

CALIBRATION_QUESTIONS = [
    "Which item's final rank surprised you most, and why?",
    "Were any descriptions too vague for reliable scoring? How should we handle them next time?",
    "Did any scores feel systematically off (e.g., Job Size always too low)?",
    "Were there domain-specific terms I should learn for this team's context?",
]

def load_prompt(name: str) -> str:
    return (Path("prompts") / name).read_text()

def calibration_question(session_num: int) -> str:
    return CALIBRATION_QUESTIONS[session_num % len(CALIBRATION_QUESTIONS)]

def log_calibration(question: str, answer: str, session_id: str):
    log_path = Path("docs/calibration/session_log.md")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = f"\n## {session_id}\n**Q:** {question}\n**A:** {answer}\n"
    with open(log_path, "a") as f:
        f.write(entry)

def main():
    parser = argparse.ArgumentParser(description="WSJF Backlog Prioritizer")
    parser.add_argument("--input", required=True, help="Path to CSV/Excel/text file or URL")
    parser.add_argument("--output-dir", default="output", help="Directory for output files")
    args = parser.parse_args()

    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.output_dir)
    out_dir.mkdir(exist_ok=True)

    # 1. Ingest
    print(f"[1/4] Ingesting: {args.input}")
    df = ingest(args.input)
    print(f"      Found {len(df)} items.")

    # 2. Score
    print("[2/4] Scoring items with Claude...")
    score_prompt = load_prompt("score_items.txt")
    items_json = df[["id", "name", "description"]].to_json(orient="records", indent=2)
    scores = score_items(score_prompt, items_json)

    # 3. Rank
    print("[3/4] Computing WSJF and ranking...")
    ranked_df = rank(df, scores)

    # Print preview
    print("\n── Top 5 items by WSJF ──────────────────────────────")
    preview = ranked_df[["rank", "name", "wsjf", "confidence", "flags"]].head(5)
    print(preview.to_string(index=False))
    print()

    # 4. Export
    print("[4/4] Exporting results...")
    csv_path = out_dir / f"ranked_backlog_{session_id}.csv"
    report_path = out_dir / f"report_{session_id}.md"
    export_csv(ranked_df, csv_path)
    export_report(ranked_df, report_path)
    print(f"      CSV:    {csv_path}")
    print(f"      Report: {report_path}")

    # 5. Continuous improvement loop
    session_num = len(list(Path("docs/calibration").glob("*.md"))) if Path("docs/calibration").exists() else 0
    q = calibration_question(session_num)
    print(f"\n── Calibration ─────────────────────────────────────")
    print(f"{q}")
    answer = input("Your answer (or press Enter to skip): ").strip()
    if answer:
        log_calibration(q, answer, session_id)
        print("Logged. Thank you — this will improve future scoring.")

    print("\nDone.")

if __name__ == "__main__":
    main()
