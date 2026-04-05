"""tools/rank.py — Merge scores into DataFrame, compute WSJF, apply flags."""
import pandas as pd

def rank(df: pd.DataFrame, scores: list[dict]) -> pd.DataFrame:
    scores_df = pd.DataFrame(scores)
    scores_df["id"] = scores_df["id"].astype(str)

    merged = df.merge(scores_df, on="id", how="left")

    # Use pre-existing columns if provided in source data
    for col in ["business_value", "time_criticality", "risk_reduction", "job_size"]:
        src_col = f"{col}_src"
        if src_col in merged.columns:
            merged[col] = merged[src_col].combine_first(merged[col])

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
