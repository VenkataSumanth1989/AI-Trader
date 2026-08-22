from app.market_data.gold_analysis import calculate_gold_analysis
from app.strategies.gold_decision import calculate_gold_decision


def main():
    analysis = calculate_gold_analysis()
    decision = calculate_gold_decision(analysis)

    print("\n" + "=" * 72)
    print("XAUUSD GOLD DECISION CENTER")
    print("=" * 72)
    print(f"Bias:             {decision['bias']}")
    print(f"Trend Alignment:  {decision['trend_alignment']}")
    print(f"Entry State:      {decision['entry_state']}")
    print(f"Candidate:        {decision['candidate']}")
    print(f"5m Confirmations: {decision['confirmations']}/5")

    if decision["entry_zone_low"] is not None:
        print(
            f"Entry Zone:       "
            f"{decision['entry_zone_low']:.2f} - "
            f"{decision['entry_zone_high']:.2f}"
        )
        print(f"Invalidation:     {decision['invalidation']:.2f}")
        print(f"Target 1:         {decision['target_1']:.2f}")
        print(f"Target 2:         {decision['target_2']:.2f}")

    print("-" * 72)
    print("Reasons:")
    for item in decision["reasons"]:
        print(f"  + {item}")

    print("Warnings:")
    for item in decision["warnings"]:
        print(f"  ! {item}")

    print("=" * 72)


if __name__ == "__main__":
    main()