from app.market_data.gold_data import test_xauusd_intervals

def main():
    results = test_xauusd_intervals()
    print("\nXAU/USD Twelve Data connectivity test")
    print("=" * 60)
    all_ok = True
    for interval, result in results.items():
        if result["ok"]:
            print(
                f"{interval:>5}: OK | rows={result['rows']} | "
                f"latest={result['latest_time']} | close={result['latest_close']}"
            )
        else:
            all_ok = False
            print(f"{interval:>5}: FAILED | {result['error']}")
    print("=" * 60)
    if all_ok:
        print("SUCCESS: XAU/USD is available for all required intervals.")
    else:
        print("Some intervals are unavailable. Do not pay/upgrade yet.")

if __name__ == "__main__":
    main()