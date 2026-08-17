import pandas as pd


def detect_order_block(
    data: pd.DataFrame,
    msb_result: dict,
    search_back: int = 20,
) -> dict:
    """
    Detect a candidate order block associated with a confirmed MSB and
    classify its current validity.

    Status:
        ACTIVE:
            Price has not revisited the zone after the MSB and the zone
            has not been invalidated.

        RETESTED:
            Price has revisited/overlapped the zone after the MSB, but the
            zone has not been invalidated.

        INVALIDATED:
            Bullish OB: a later candle closes below the OB low.
            Bearish OB: a later candle closes above the OB high.
    """

    result = {
        "order_block": "NONE",
        "direction": "NEUTRAL",
        "zone_low": None,
        "zone_high": None,
        "ob_time": None,
        "current_price": None,
        "price_position": "UNKNOWN",
        "revisited": False,
        "status": "NONE",
        "invalidation_time": None,
        "confidence": 0,
        "reasons": [],
        "warnings": [],
    }

    required = {
        "Open",
        "High",
        "Low",
        "Close",
    }

    if not required.issubset(data.columns):
        result["reasons"].append(
            "Required OHLC data is missing"
        )
        return result

    if (
        msb_result.get("msb") in (None, "NONE")
        or msb_result.get("break_time") is None
    ):
        result["reasons"].append(
            "No confirmed MSB available for order block detection"
        )
        return result

    df = data[
        ["Open", "High", "Low", "Close"]
    ].dropna().copy()

    if df.empty:
        result["reasons"].append(
            "No valid price data available"
        )
        return result

    break_time = msb_result["break_time"]

    if break_time not in df.index:
        result["reasons"].append(
            "MSB break candle is not available in the supplied data"
        )
        return result

    break_index = df.index.get_loc(break_time)

    start_index = max(
        0,
        break_index - search_back,
    )

    candidate_index = None

    # --------------------------------------------------
    # BULLISH ORDER BLOCK
    # --------------------------------------------------

    if msb_result["direction"] == "BULLISH":

        for i in range(
            break_index - 1,
            start_index - 1,
            -1,
        ):

            open_price = float(df["Open"].iloc[i])
            close_price = float(df["Close"].iloc[i])

            if close_price < open_price:
                candidate_index = i
                break

        if candidate_index is None:
            result["reasons"].append(
                "No bearish candle found before bullish MSB"
            )
            return result

        order_block = "BULLISH_OB"
        direction = "BULLISH"

    # --------------------------------------------------
    # BEARISH ORDER BLOCK
    # --------------------------------------------------

    elif msb_result["direction"] == "BEARISH":

        for i in range(
            break_index - 1,
            start_index - 1,
            -1,
        ):

            open_price = float(df["Open"].iloc[i])
            close_price = float(df["Close"].iloc[i])

            if close_price > open_price:
                candidate_index = i
                break

        if candidate_index is None:
            result["reasons"].append(
                "No bullish candle found before bearish MSB"
            )
            return result

        order_block = "BEARISH_OB"
        direction = "BEARISH"

    else:
        result["reasons"].append(
            "Unsupported MSB direction"
        )
        return result

    # --------------------------------------------------
    # ORDER BLOCK ZONE
    # --------------------------------------------------

    zone_low = float(df["Low"].iloc[candidate_index])
    zone_high = float(df["High"].iloc[candidate_index])
    ob_time = df.index[candidate_index]
    current_price = float(df["Close"].iloc[-1])

    # --------------------------------------------------
    # CURRENT PRICE POSITION
    # --------------------------------------------------

    if current_price > zone_high:
        price_position = "ABOVE_OB"
    elif current_price < zone_low:
        price_position = "BELOW_OB"
    else:
        price_position = "INSIDE_OB"

    # --------------------------------------------------
    # REVISIT + INVALIDATION
    # --------------------------------------------------

    revisited = False
    invalidated = False
    invalidation_time = None

    candles_after_break = df.iloc[
        break_index + 1:
    ]

    for candle_time, candle in candles_after_break.iterrows():

        candle_high = float(candle["High"])
        candle_low = float(candle["Low"])
        candle_close = float(candle["Close"])

        # Any overlap means the zone has been revisited.
        if (
            candle_low <= zone_high
            and candle_high >= zone_low
        ):
            revisited = True

        # Invalidation uses candle CLOSE rather than wick penetration.
        if direction == "BULLISH":
            if candle_close < zone_low:
                invalidated = True
                invalidation_time = candle_time
                break

        elif direction == "BEARISH":
            if candle_close > zone_high:
                invalidated = True
                invalidation_time = candle_time
                break

    if invalidated:
        status = "INVALIDATED"
    elif revisited:
        status = "RETESTED"
    else:
        status = "ACTIVE"

    # --------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------

    confidence = 60

    if msb_result.get("confidence", 0) >= 70:
        confidence += 10

    if status == "RETESTED":
        confidence += 5

    if price_position == "INSIDE_OB" and status != "INVALIDATED":
        confidence += 5

    if status == "INVALIDATED":
        confidence = min(confidence, 35)

    confidence = min(confidence, 100)

    reasons = [
        (
            "Last bearish candle before bullish MSB used as candidate bullish order block"
            if direction == "BULLISH"
            else
            "Last bullish candle before bearish MSB used as candidate bearish order block"
        ),
        f"Current price is {price_position}",
        f"Order block status is {status}",
    ]

    warnings = []

    if status == "ACTIVE":
        reasons.append(
            "Price has not yet revisited the order block zone after the MSB"
        )

    elif status == "RETESTED":
        reasons.append(
            "Price revisited the order block zone and the zone remains valid"
        )

    elif status == "INVALIDATED":
        warnings.append(
            (
                "Bullish order block invalidated by a candle close below the zone low"
                if direction == "BULLISH"
                else
                "Bearish order block invalidated by a candle close above the zone high"
            )
        )

    return {
        "order_block": order_block,
        "direction": direction,
        "zone_low": zone_low,
        "zone_high": zone_high,
        "ob_time": ob_time,
        "current_price": current_price,
        "price_position": price_position,
        "revisited": revisited,
        "status": status,
        "invalidation_time": invalidation_time,
        "confidence": confidence,
        "reasons": reasons,
        "warnings": warnings,
    }