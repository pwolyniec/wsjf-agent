"""tools/export.py — Write ranked CSV and markdown report."""
import pandas as pd
from pathlib import Path

OUTPUT_COLS = [
    "rank", "id", "name",
    "business_value", "time_criticality", "risk_reduction", "job_size",
    "cod", "wsjf", "confidence", "flags", "rationale"
]

def export_csv(df: pd.DataFrame, path: Path):
    cols = [c for c in OUTPUT_COLS if c in df.columns]
    df[cols].to_csv(path, index=False)

def export_report(df: pd.DataFrame, path: Path):
    top5 = df.head(5)
    lines = [
        "# WSJF Prioritized Backlog Report\n",
        f"**Total items scored:** {len(df)}  ",
        f"**Items with low confidence:** {(df.get('confidence','') == 'low').sum()}  ",
        f"**Large high-priority items (consider splitting):** "
        f"{df['flags'].str.contains('large-high-priority', na=False).sum()}\n",
        "---\n",
        "## Top 5 Items\n",
    ]
    for _, row in top5.iterrows():
        lines += [
            f"### {row['rank']}. {row.get('name', row['id'])}",
            f"**WSJF:** {row['wsjf']}  |  "
            f"BV: {row.get('business_value','?')}  "
            f"TC: {row.get('time_criticality','?')}  "
            f"RR: {row.get('risk_reduction','?')}  "
            f"Size: {row.get('job_size','?')}",
            f"_{row.get('rationale', '')}_",
            f"Flags: `{row.get('flags', 'none')}`\n",
        ]
    lines += [
        "---\n",
        "## Full Ranking\n",
        df[["rank","name","wsjf","confidence","flags"]].to_markdown(index=False),
    ]
    path.write_text("\n".join(lines))
