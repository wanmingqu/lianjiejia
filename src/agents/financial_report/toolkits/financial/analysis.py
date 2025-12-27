from typing import Dict, List, Optional, Tuple


def compute_yoy(current: float, prior: float) -> Optional[float]:
    """Compute Year-over-Year growth (as fraction, e.g., 0.1 for 10%).

    Returns None if prior is None or 0.
    """
    try:
        if prior is None or current is None:
            return None
        if prior == 0:
            return None
        return (current - prior) / abs(prior)
    except Exception:
        return None


def compute_qoq(current: float, prior_quarter: float) -> Optional[float]:
    """Compute Quarter-over-Quarter growth.
    Returns None if prior_quarter is None or 0.
    """
    try:
        if prior_quarter is None or current is None:
            return None
        if prior_quarter == 0:
            return None
        return (current - prior_quarter) / abs(prior_quarter)
    except Exception:
        return None


def safe_div(n: Optional[float], d: Optional[float]) -> Optional[float]:
    try:
        if n is None or d is None:
            return None
        if d == 0:
            return None
        return n / d
    except Exception:
        return None


def compute_ratios(row: Dict[str, Optional[float]]) -> Dict[str, Optional[float]]:
    """Compute a set of common financial ratios from a row dict.

    Expected keys in row: revenue, cost_of_goods_sold, gross_profit, net_income, total_assets, total_liabilities, current_assets, current_liabilities
    The function will compute: gross_margin, net_margin, current_ratio, debt_to_asset
    """
    revenue = row.get("revenue")
    cogs = row.get("cost_of_goods_sold")
    gross_profit = row.get("gross_profit") if row.get("gross_profit") is not None else (None if revenue is None or cogs is None else revenue - cogs)
    net_income = row.get("net_income")
    total_assets = row.get("total_assets")
    total_liabilities = row.get("total_liabilities")
    current_assets = row.get("current_assets")
    current_liabilities = row.get("current_liabilities")

    gross_margin = safe_div(gross_profit, revenue)
    net_margin = safe_div(net_income, revenue)
    current_ratio = safe_div(current_assets, current_liabilities)
    debt_to_asset = safe_div(total_liabilities, total_assets)

    return {
        "gross_margin": gross_margin,
        "net_margin": net_margin,
        "current_ratio": current_ratio,
        "debt_to_asset": debt_to_asset,
    }


def timeseries_from_rows(rows: List[Dict], period_keys: List[str]) -> Dict[str, List[Tuple[str, Optional[float]]]]:
    """Convert table rows into timeseries keyed by label.

    rows: list of {"label": str, "values": {period: value}}
    period_keys: ordered list of periods to extract

    Returns mapping: label -> list of (period, value)
    """
    out = {}
    for r in rows:
        label = r.get("label")
        vals = []
        for p in period_keys:
            vals.append((p, r.get("values", {}).get(p)))
        out[label] = vals
    return out
