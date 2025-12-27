from typing import List, Dict, Any

try:
    from src.utils import logger
except Exception:
    # fallback logger for environments without full package imports
    import types as _types
    logger = _types.SimpleNamespace(info=lambda *a, **k: None, error=lambda *a, **k: None)


def format_timeseries_for_mcp(series: Dict[str, List[tuple]], metric: str = "value") -> Dict[str, Any]:
    """Format multiple labeled timeseries into MCP chart payload (simple format).

    Input: {label: [(period, value), ...], ...}
    Output: {"series": [{"name": label, "data": [{"x": period, "y": value}, ...]}, ...], "metadata": {...}}
    """
    out = {"series": [], "metadata": {"type": "line"}}
    for label, seq in series.items():
        data = []
        for period, val in seq:
            data.append({"x": period, "y": val})
        out["series"].append({"name": label, "data": data})
    return out


def generate_chart_payload(rows: List[Dict], period_keys: List[str], top_n: int = 5) -> Dict[str, Any]:
    """Pick top_n labels by latest period value and build a timeseries payload."""
    # build timeseries
    try:
        # Try to import the helper from the package
        from src.agents.reporter.toolkits.financial.analysis import timeseries_from_rows
    except Exception:
        # Fallback: define a local timeseries_from_rows
        def timeseries_from_rows(rows_local, period_keys_local):
            out = {}
            for r in rows_local:
                label = r.get("label")
                vals = []
                for p in period_keys_local:
                    vals.append((p, r.get("values", {}).get(p)))
                out[label] = vals
            return out

    ts = timeseries_from_rows(rows, period_keys)

    # compute latest values
    latest_period = period_keys[-1] if period_keys else None
    ranked = []
    for label, seq in ts.items():
        # find latest value
        latest_val = None
        for p, v in seq:
            if p == latest_period:
                latest_val = v
                break
        ranked.append((label, latest_val))

    ranked_sorted = sorted(ranked, key=lambda x: (x[1] is None, -x[1] if x[1] is not None else 0))[:top_n]
    selected_labels = [r[0] for r in ranked_sorted]

    selected_series = {label: ts[label] for label in selected_labels}
    payload = format_timeseries_for_mcp(selected_series)
    payload["metadata"]["title"] = "Top metrics over time"
    return payload