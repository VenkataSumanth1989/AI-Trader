import pandas as pd


def _last_close_at_or_before(
    data: pd.DataFrame,
    target_time,
):
    if data is None or data.empty:
        return None

    eligible = data[data.index <= target_time]

    if eligible.empty:
        return None

    return float(eligible["Close"].iloc[-1])


def calculate_price_performance(
    intraday_data: pd.DataFrame,
    daily_data: pd.DataFrame,
) -> dict:
    """
    Compare current price against:
    - approximately 4 clock hours ago
    - previous completed trading-day close
    - approximately 7 calendar days ago

    Calendar-time lookup avoids assuming that five rows always equals one week.
    """
    current_price = float(
        intraday_data["Close"].iloc[-1]
    )

    current_time = intraday_data.index[-1]

    # 4 hours ago.
    price_4h = _last_close_at_or_before(
        intraday_data,
        current_time - pd.Timedelta(hours=4),
    )

    # Completed daily candles only.
    current_date = current_time.date()
    completed_daily = daily_data[
        daily_data.index.date < current_date
    ]

    price_1d = (
        float(completed_daily["Close"].iloc[-1])
        if not completed_daily.empty
        else None
    )

    # True 7-calendar-day comparison, using the latest available completed
    # market close at or before that timestamp.
    one_week_ago = current_time - pd.Timedelta(days=7)
    price_1w = _last_close_at_or_before(
        completed_daily,
        one_week_ago,
    )

    def compare(reference_price):
        if reference_price is None or reference_price == 0:
            return {
                "price": None,
                "difference": None,
                "percent": None,
            }

        difference = current_price - reference_price
        percent = difference / reference_price * 100

        return {
            "price": reference_price,
            "difference": difference,
            "percent": percent,
        }

    return {
        "current": current_price,
        "4h": compare(price_4h),
        "1d": compare(price_1d),
        "1w": compare(price_1w),
    }
