def algorithm(candles, ticker: str) -> str:
    """
    간단한 이동평균 크로스 전략 (5 > 20 상향 돌파 → BUY, 하향 돌파 → SELL)
    ticker 인자를 받지만, 여기선 쓰지 않고 있습니다.
    """
    ma5_now = candles["close"].rolling(5).mean().iloc[-1]
    ma20_now = candles["close"].rolling(20).mean().iloc[-1]
    ma5_prev = candles["close"].rolling(5).mean().iloc[-2]
    ma20_prev = candles["close"].rolling(20).mean().iloc[-2]

    if ma5_prev <= ma20_prev and ma5_now > ma20_now:
        return "BUY"
    if ma5_prev >= ma20_prev and ma5_now < ma20_now:
        return "SELL"
    return "HOLD"