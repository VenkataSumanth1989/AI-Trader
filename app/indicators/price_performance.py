import pandas as pd


def calculate_price_performance(
    intraday_data: pd.DataFrame,
    daily_data: pd.DataFrame,
) -> dict:
    """
    Compare current price against:
    - approximately 4 market hours ago
    - previous trading day close
    - approximately 1 trading week ago
    """

    current_price = float(
        intraday_data["Close"].iloc[-1]
    )

    current_time = intraday_data.index[-1]

    # --------------------------------------------------
    # 4 HOURS AGO
    # --------------------------------------------------

    target_time = (
        current_time
        - pd.Timedelta(hours=4)
    )

    earlier_intraday = intraday_data[
        intraday_data.index <= target_time
    ]

    price_4h = None

    if not earlier_intraday.empty:
        price_4h = float(
            earlier_intraday["Close"].iloc[-1]
        )

    # --------------------------------------------------
    # PREVIOUS TRADING DAY
    # --------------------------------------------------

    current_date = current_time.date()

    completed_daily = daily_data[
        daily_data.index.date < current_date
    ]

    price_1d = None

    if len(completed_daily) >= 1:
        price_1d = float(
            completed_daily["Close"].iloc[-1]
        )

    # --------------------------------------------------
    # ONE TRADING WEEK AGO
    # --------------------------------------------------

    price_1w = None

    if len(completed_daily) >= 5:
        price_1w = float(
            completed_daily["Close"].iloc[-5]
        )

    # --------------------------------------------------
    # HELPER
    # --------------------------------------------------

    def compare(reference_price):

        if reference_price is None:
            return {
                "price": None,
                "difference": None,
                "percent": None,
            }

        difference = (
            current_price
            - reference_price
        )

        percent = (
            difference
            / reference_price
            * 100
        )

        return {
            "price": reference_price,
            "difference": difference,
            "percent": percent,
        }

    # --------------------------------------------------
    # RETURN
    # --------------------------------------------------

    return {
        "current": current_price,
        "4h": compare(price_4h),
        "1d": compare(price_1d),
        "1w": compare(price_1w),
    }