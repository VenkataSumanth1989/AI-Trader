from app.config import DEFAULT_TICKER
from app.market_data.stock_data import get_historical_data
from app.indicators.technical import add_technical_indicators
from app.backtest.engine import run_backtest


data = get_historical_data(
    DEFAULT_TICKER,
    period="5d",
    interval="5m"
)

data = add_technical_indicators(data)

trades = run_backtest(data)

print("\n" + "=" * 70)
print(f"AI-TRADER BACKTEST: {DEFAULT_TICKER}")
print("=" * 70)

print(f"Total trades: {len(trades)}")

if not trades.empty:

    print("\nTrades:")
    print(trades.to_string(index=False))

    winning_trades = trades[trades["pnl_pct"] > 0]
    losing_trades = trades[trades["pnl_pct"] <= 0]

    win_rate = (
        len(winning_trades)
        / len(trades)
        * 100
    )

    total_pnl = trades["pnl_pct"].sum()

    print("\n" + "-" * 70)
    print(f"Winning trades: {len(winning_trades)}")
    print(f"Losing trades:  {len(losing_trades)}")
    print(f"Win rate:       {win_rate:.2f}%")
    print(f"Total P&L:      {total_pnl:.2f}%")

else:

    print("No trades generated.")

print("=" * 70)