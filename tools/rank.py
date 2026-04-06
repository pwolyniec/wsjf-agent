"""tools/rank.py — Merge scores into DataFrame, compute WSJF, apply flags."""
import pandas as pd

def rank(df: pd.DataFrame, scores: list[dict]) -> pd.DataFrame:
    scores_df = pd.DataFrame(scores)
    scores_df["id"] = scores_df["id"].astype(str)

    # Drop overlapping WSJF columns from input so scored values take precedence
    score_cols = {"business_value", "time_criticality", "risk_reduction", "job_size",
                  "confidence", "rationale"}
    drop_cols = [c for c in df.columns if c in score_cols]
    df_clean = df.drop(columns=drop_cols)

    merged = df_clean.merge(scores_df, on="id", how="left")

    merged["cod"] = (
        merged["business_value"] +
        merged["time_criticality"] +
        merged["risk_reduction"]
    )
    merged["wsjf"] = (merged["cod"] / merged["job_size"]).round(2)
    merged = merged.sort_values("wsjf", ascending=False).reset_index(drop=True)
    merged.insert(0, "rank", merged.index + 1)

    merged["flags"] = merged.apply(_apply_flags, axis=1)
    return merged

def _apply_flags(row) -> str:
    flags = []
    if row.get("confidence") == "low":
        flags.append("low_confidence")
    if row.get("job_size", 0) >= 8 and row.get("wsjf", 0) >= 7:
        flags.append("large-high-priority: consider splitting")
    # Near-tie detection handled post-sort in export
    return "; ".join(flags) if flags else ""
