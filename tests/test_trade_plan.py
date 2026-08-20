from app.strategies.trade_plan import build_trade_plan


def main():
    row = {
        "Close": 100.0,
        "ATR_14": 2.0,
    }

    multi_timeframe = {
        "snapshots": {
            "1h": {
                "support": 96.0,
                "resistance": 104.0,
            },
            "4h": {
                "support": 94.0,
                "resistance": 108.0,
            },
        }
    }

    long_plan = build_trade_plan(
        swing_outlook={"bias": "LONG"},
        trade_state={
            "state": "ENTRY_READY",
            "direction": "LONG",
        },
        row=row,
        multi_timeframe=multi_timeframe,
    )

    assert long_plan["status"] == "READY"
    assert long_plan["invalidation"] < 100.0
    assert long_plan["target_1"] > 100.0
    assert long_plan["target_2"] > long_plan["target_1"]

    short_plan = build_trade_plan(
        swing_outlook={"bias": "SHORT"},
        trade_state={
            "state": "WAITING",
            "direction": "SHORT",
        },
        row=row,
        multi_timeframe=multi_timeframe,
    )

    assert short_plan["status"] == "WATCH"
    assert short_plan["invalidation"] > 100.0
    assert short_plan["target_1"] < 100.0
    assert short_plan["target_2"] < short_plan["target_1"]

    print("Trade plan tests passed")
    print("LONG:", long_plan)
    print("SHORT:", short_plan)


if __name__ == "__main__":
    main()