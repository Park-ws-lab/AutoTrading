import requests
import numpy as np
import math
import pandas as pd
from sklearn.linear_model import LinearRegression


def get_volume_spike_percentage(df, amount_target: int, amount_before: int) -> float:
    """
    최근 거래량 급등배수를 반환하는 함수

    Args:
        df (pd.DataFrame): OHLCV 데이터 (시간순 정렬되어 있어야 함)
        amount_target (int): 현재 구간의 길이 (예: a=3 최근 3봉간의 거래량 평균) -1 ~ -3 [-a:]
        amount_before (int): 비교 대상 구간의 길이 (예: b=5 이전 5봉간의 거래량 평균) -4 ~ -8 [-a-b:-a-1]

    Returns:
        float: 거래량 급등 비율
    """
    # 데이터 충분한지 확인
    if len(df) < amount_target + amount_before:
        return False

    # 이전 평균 거래량 (-a-b ~ -a-1)
    vol_past = df['volume'].iloc[-amount_target-amount_before : -amount_target-1].mean()

    # 현재 평균 거래량 (-a ~ -1)
    vol_now = df['volume'].iloc[-amount_target:].mean()

    if vol_past == 0:
        return 0  # 0으로 나누기 방지

    return (vol_now / vol_past)

def is_volume_spike(df, amount_target: int, amount_before: int, threshold: float) -> bool:
    """
    최근 거래량 급등 여부를 판단하는 함수

    Args:
        df (pd.DataFrame): OHLCV 데이터 (시간순 정렬되어 있어야 함)
        amount_target (int): 현재 구간의 길이 (예: a=3 최근 3봉간의 거래량 평균) -1 ~ -3 [-a:]
        amount_before (int): 비교 대상 구간의 길이 (예: b=5 이전 5봉간의 거래량 평균) -4 ~ -8 [-a-b:-a-1]
        threshold (float): 거래량 급등 판단 기준 배수

    Returns:
        bool: 거래량 급등 여부
    """
    # 데이터 충분한지 확인
    if len(df) < amount_target + amount_before:
        return False

    # 이전 평균 거래량 (-a-b ~ -a-1)
    vol_past = df['volume'].iloc[-amount_target-amount_before : -amount_target-1].mean()

    # 현재 평균 거래량 (-a ~ -1)
    vol_now = df['volume'].iloc[-amount_target:].mean()

    if vol_past == 0:
        return False  # 0으로 나누기 방지

    return (vol_now / vol_past) >= threshold



def calculate_trend_slope(df: pd.DataFrame, n: int) -> float:
    """
    스캘핑 전용: n초 간의 저점/고점 추세선을 선형회귀로 추정 후, 각도 계산
    """
    if df is None or len(df) < n:
        return 0.0

    df = df.sort_index()
    sub_df = df.iloc[-n:]
    x = np.arange(n).reshape(-1, 1)  # 시간 간격은 상대적으로 1초씩

    lows = sub_df['low'].values
    highs = sub_df['high'].values

    # 변화폭이 너무 작으면 보합 간주
    low_range = abs(lows[-1] - lows[0]) / (lows[0] + 1e-8)
    high_range = abs(highs[-1] - highs[0]) / (highs[0] + 1e-8)

    if low_range < 0.001 and high_range < 0.001:
        return 0.0

    model_low = LinearRegression().fit(x, lows)
    model_high = LinearRegression().fit(x, highs)

    avg_slope = (model_low.coef_[0] + model_high.coef_[0]) / 2
    angle = math.degrees(math.atan(avg_slope))

    return angle

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