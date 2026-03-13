"""
ml/forecasting.py
═══════════════════════════════════════════════════════════════
Demand Forecasting for Smart Cafe.

Uses:
  - Simple Exponential Smoothing (SES) for short-term forecast
  - Day-of-week seasonality adjustment
  - Moving average baseline

No external ML library required — pure Python + basic maths.
"""
from __future__ import annotations
from datetime import date, timedelta
from typing import List, Dict, Tuple
from collections import defaultdict
import math


def exponential_smoothing(series: List[float], alpha: float = 0.3) -> List[float]:
    """Simple Exponential Smoothing."""
    if not series:
        return []
    smoothed = [series[0]]
    for val in series[1:]:
        smoothed.append(alpha * val + (1 - alpha) * smoothed[-1])
    return smoothed


def day_of_week_seasonality(historical_by_day: Dict[str, float]) -> Dict[int, float]:
    """
    Compute average scaling factor per weekday (0=Mon … 6=Sun).
    Returns {weekday: scale_factor} where 1.0 = average day.
    """
    weekday_totals: Dict[int, list] = defaultdict(list)
    for date_str, value in historical_by_day.items():
        try:
            d = date.fromisoformat(date_str)
            weekday_totals[d.weekday()].append(value)
        except Exception:
            pass

    weekday_avgs = {wd: sum(vals) / len(vals) for wd, vals in weekday_totals.items() if vals}
    if not weekday_avgs:
        return {i: 1.0 for i in range(7)}

    global_avg = sum(weekday_avgs.values()) / len(weekday_avgs)
    if global_avg == 0:
        return {i: 1.0 for i in range(7)}

    return {wd: avg / global_avg for wd, avg in weekday_avgs.items()}


def forecast_next_n_days(
    daily_orders: Dict[str, int],   # {date_str: order_count}
    n: int = 7
) -> List[Dict]:
    """
    Forecast order volume for the next n days.

    Returns list of:
      {"date": "YYYY-MM-DD", "projected_orders": int,
       "confidence_low": int, "confidence_high": int}
    """
    if not daily_orders:
        return [{"date": (date.today() + timedelta(days=i+1)).isoformat(),
                 "projected_orders": 20, "confidence_low": 15, "confidence_high": 25}
                for i in range(n)]

    # Sort series
    sorted_days = sorted(daily_orders.items())
    values = [v for _, v in sorted_days]

    # Smoothed series
    smoothed = exponential_smoothing(values, alpha=0.35)
    last_smooth = smoothed[-1] if smoothed else sum(values) / len(values)

    # Trend (last 3 data points slope)
    if len(smoothed) >= 3:
        slope = (smoothed[-1] - smoothed[-3]) / 2
    else:
        slope = 0

    # Std-dev for confidence interval
    residuals = [abs(values[i] - smoothed[i]) for i in range(len(values))]
    std_dev = math.sqrt(sum(r**2 for r in residuals) / len(residuals)) if residuals else 5

    # Day-of-week seasonality
    dow_factors = day_of_week_seasonality(dict(sorted_days))

    forecast = []
    for i in range(1, n + 1):
        future_date = date.today() + timedelta(days=i)
        dow = future_date.weekday()
        base = last_smooth + slope * i
        seasonal_base = base * dow_factors.get(dow, 1.0)
        projected = max(0, round(seasonal_base))
        ci = max(2, round(std_dev * 1.5))
        forecast.append({
            "date":              future_date.isoformat(),
            "day_name":          future_date.strftime("%A"),
            "projected_orders":  projected,
            "confidence_low":    max(0, projected - ci),
            "confidence_high":   projected + ci,
            "seasonality_factor": round(dow_factors.get(dow, 1.0), 2),
        })
    return forecast


def forecast_revenue(
    daily_revenue: Dict[str, float],   # {date_str: total_revenue}
    avg_order_value: float,
    n: int = 7
) -> List[Dict]:
    """Forecast revenue using order count forecast × avg order value."""
    # Convert to order counts (approx) by dividing by avg_order_value
    if avg_order_value <= 0:
        avg_order_value = 500.0

    daily_counts = {
        d: max(1, round(rev / avg_order_value))
        for d, rev in daily_revenue.items()
    }
    order_forecast = forecast_next_n_days(daily_counts, n)

    return [{
        **f,
        "projected_revenue":        round(f["projected_orders"] * avg_order_value, 2),
        "revenue_confidence_low":   round(f["confidence_low"]   * avg_order_value, 2),
        "revenue_confidence_high":  round(f["confidence_high"]  * avg_order_value, 2),
    } for f in order_forecast]


def peak_hour_forecast(hourly_data: Dict[int, int]) -> List[Dict]:
    """
    Given historical orders per hour, classify each hour's expected load.
    """
    if not hourly_data:
        return []
    max_val = max(hourly_data.values()) or 1
    result = []
    for h in range(24):
        count = hourly_data.get(h, 0)
        ratio = count / max_val
        level = "peak" if ratio > 0.7 else "high" if ratio > 0.45 else "medium" if ratio > 0.2 else "low"
        result.append({
            "hour":       f"{h:02d}:00",
            "avg_orders": count,
            "load_level": level,
            "load_pct":   round(ratio * 100),
        })
    return result