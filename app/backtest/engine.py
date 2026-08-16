import pandas as pd


def run_backtest(
    data: pd.DataFrame,
    entry_score: int = 80,
    exit_score: int = 65,
    stop_loss_pct: float = 0.01,
    take_profit_pct: float = 0.02,
):
    """
    Simple long-only backtest.

    Entry:
        Strategy score >= entry_score

    Exit:
        Strategy score < exit_score
        OR stop loss
        OR take profit
    """

    trades = []

    in_position = False
    entry_price = None
    entry_time = None

    for timestamp, row in data.iterrows():

        price = row["Close"]

        # Calculate strategy score directly from indicators
        score = 0

        if price > row["VWAP"]:
            score += 20

        if row["EMA_9"] > row["EMA_20"]:
            score += 15

        if row["EMA_20"] > row["EMA_50"]:
            score += 15

        if row["RSI_14"] > 50:
            score += 10

        if 50 < row["RSI_14"] < 70:
            score += 5

        if row["MACD"] > row["MACD_SIGNAL"]:
            score += 15

        if row["MACD_HISTOGRAM"] > 0:
            score += 10

        if row["RELATIVE_VOLUME"] > 1.5:
            score += 10

        # Skip rows where indicators aren't ready
        if pd.isna(score):
            continue

        # -------------------------
        # ENTRY
        # -------------------------

        if not in_position and score >= entry_score:

            in_position = True
            entry_price = price
            entry_time = timestamp

            continue

        # -------------------------
        # EXIT
        # -------------------------

        if in_position:

            stop_price = entry_price * (1 - stop_loss_pct)
            target_price = entry_price * (1 + take_profit_pct)

            exit_reason = None

            if price <= stop_price:
                exit_reason = "STOP_LOSS"

            elif price >= target_price:
                exit_reason = "TAKE_PROFIT"

            elif score < exit_score:
                exit_reason = "SIGNAL_EXIT"

            if exit_reason:

                pnl_pct = (
                    (price - entry_price)
                    / entry_price
                ) * 100

                trades.append({
                    "entry_time": entry_time,
                    "entry_price": entry_price,
                    "exit_time": timestamp,
                    "exit_price": price,
                    "pnl_pct": pnl_pct,
                    "exit_reason": exit_reason,
                })

                in_position = False
                entry_price = None
                entry_time = None

    return pd.DataFrame(trades)