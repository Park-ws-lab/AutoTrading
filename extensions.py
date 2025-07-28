import requests
from pyupbit import Upbit
import numpy as np

def is_volume_spike(df, n, threshold) -> bool:
    """
    직전 n봉 평균 거래량 대비 현재봉 거래량이 threshold배 이상이면 True
    """
    if df is None or len(df) < n + 1:
        return False

    vol_prev_n = df['volume'].iloc[-n-1:-1]
    vol_now = df['volume'].iloc[-1]

    avg_vol = vol_prev_n.mean()

    if avg_vol == 0:
        return False

    return vol_now / avg_vol >= threshold

def calculate_trend_slope(df, n) -> float:
    """
    n봉 기준 저점과 고점의 선형 회귀 기울기의 평균값 (추세의 기울기)

    Returns:
        float: 상승추세면 +값, 하락추세면 -값
    """
    if df is None or len(df) < n:
        return 0.0

    lows = df['low'].iloc[-n:].values
    highs = df['high'].iloc[-n:].values
    x = np.arange(n)

    # 선형 회귀로 기울기 추정
    low_slope = np.polyfit(x, lows, deg=1)[0]
    high_slope = np.polyfit(x, highs, deg=1)[0]

    return (low_slope + high_slope) / 2

def get_bullish_ratio(df, n=5):
    """
    최근 n개의 봉 중에서 양봉의 비율 계산

    Args:
        df (pd.DataFrame): ohlcv 데이터 (open, high, low, close, volume 포함)
        n (int): 최근 몇 개의 봉을 기준으로 할지

    Returns:
        float: 양봉 비율 (0.0 ~ 1.0)
    """
    if df is None or len(df) < n:
        return 0.0

    recent_df = df.iloc[-n:]
    bullish_count = (recent_df['close'] > recent_df['open']).sum()

    return bullish_count / n

def get_ticker_pnl_rate(ticker: str, balances: list, current_prices: dict) -> float:
    """
    보유 중인 특정 종목의 현재 수익률(PnL Rate)을 계산합니다.

    Args:
        ticker (str): 예: "KRW-BTC"
        balances (list): upbit.get_balances() 결과
        current_prices (dict): {ticker(str): price(float)} 형태의 현재가 정보

    Returns:
        float: 수익률 (예: 0.054 = 5.4%)
    """
    coin = ticker.split("-")[1]
    avg_buy_price = 0.0
    volume = 0.0

    for b in balances:
        if b['currency'] == coin:
            avg_buy_price = float(b.get("avg_buy_price", 0.0))
            volume = float(b.get("balance", 0.0))
            break

    if avg_buy_price == 0 or volume == 0:
        return 0.0  # 보유 중이 아니거나 데이터 없음

    current_price = current_prices.get(ticker)
    if not current_price or current_price == 0:
        return 0.0  # 가격 정보 없음

    pnl_rate = (current_price - avg_buy_price) / avg_buy_price
    return pnl_rate
    

def get_recent_trade_strength(ticker: str, count: int = 30) -> float:
    """
    체결강도 계산 (최근 count건 기준)

    Args:
        ticker: KRW-BTC 같은 마켓명
        count: 몇 건의 체결 데이터로 계산할지 (최대 100)

    Returns:
        float: 체결강도 (1.0 이상이면 매수세 우위)
    """
    url = "https://api.upbit.com/v1/trades/ticks"
    params = {"market": ticker, "count": count}
    try:
        res = requests.get(url, params=params)
        res.raise_for_status()
        data = res.json()

        buy = sum(t["trade_volume"] for t in data if t["ask_bid"] == "BID")
        sell = sum(t["trade_volume"] for t in data if t["ask_bid"] == "ASK")

        if sell == 0:
            return float("inf") if buy > 0 else 1.0

        return buy / sell

    except Exception as e:
        print(f"[{ticker}][체결강도 ERROR] {e}")
        return 1.0  # fallback value