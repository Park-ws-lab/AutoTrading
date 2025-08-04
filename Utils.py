import os
from pyupbit import Upbit
import pyupbit
from dotenv import load_dotenv
import pandas as pd
import requests
import hashlib
import jwt
import uuid
import time
from urllib.parse import urlencode

load_dotenv()


ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
MIN_ORDER_KRW = os.getenv("MIN_ORDER_KRW")
DRY_RUN = os.getenv("DRY_RUN")


##### 시장가 매수 (Amount) #####
def buy_market(upbit: Upbit, ticker: str, amount_krw):
    """
    - 해당 종목 시장가 매수
    - amount_krw: 주문할 양
    """

    krw = float(upbit.get_balance("KRW"))
    amount = min(krw, amount_krw)

    if amount < MIN_ORDER_KRW:
        print(f"[{ticker}][BUY] KRW 부족 (보유: {krw:.0f} KRW)")
        return

    if DRY_RUN:
        print(f"[{ticker}][BUY][DRY_RUN] {amount:.0f} KRW 시장가 매수 (실제 주문 X)")
    else:
        resp = upbit.buy_market_order(ticker, amount)
        print(f"[{ticker}][BUY][DONE] {resp}")
        

##### 시장가 매수 (Percentage) #####
def buy_market_percentage(upbit: Upbit, ticker: str, percentage: float):
    """
    - 해당 종목 시장가 매수
    - percentage: 주문할 양 비율 (0.0 ~ 1.0)
    """

    percentage = max(0.0, min(percentage, 1.0))
    amount_krw = float(upbit.get_balance("KRW")) * percentage

    buy_market(upbit, ticker, amount_krw)


def sell_market(upbit: Upbit, ticker: str, amount_krw):
    """
    - 해당 종목 시장가 매도
    - amount_krw: 주문할 금액 (KRW)
    """

    coin = ticker.split("-")[1]
    balance_krw = float(upbit.get_amount(coin))

    if balance_krw <= 0:
        print(f"[{ticker}][SELL] 보유 {coin} 수량 없음")
        return

    if amount_krw > balance_krw:
        amount_krw = balance_krw  # 최대치 보정

    price_now = pyupbit.get_current_price(ticker)
    if not price_now or price_now == 0:
        print(f"[{ticker}][SELL][ERROR]가격 정보 없음")
        return
    
    amount_coin = amount_krw / price_now


    if DRY_RUN:
        print(f"[{ticker}][SELL][DRY_RUN] {amount_krw:.0f} KRW → {amount_coin:.8f} {coin} 매도 (실제 주문 X)")
    else:
        resp = upbit.sell_market_order(ticker, amount_coin)
        print(f"[{ticker}][SELL][DONE] {resp}")


##### 시장가 매도 (Percentage) #####
def sell_market_percentage(upbit: Upbit, ticker: str, percentage: float):
    """
    - 해당 종목 시장가 매도
    - percentage: 주문할 양 비율 (0.0 ~ 1.0)
    """

    percentage = max(0.0, min(percentage, 1.0))

    coin = ticker.split("-")[1]
    amount_krw = float(upbit.get_amount(coin)) * percentage
    
    sell_market(upbit, ticker, amount_krw)


##### 지정가 매수 (Amount) #####
def buy_limit(upbit: Upbit, ticker: str, target_price, amount_krw):
    """
    - 해당 종목 지정가 매수 주문
    - target_price: 주문 가격
    - amount_krw: 주문할 양
    """

    krw = float(upbit.get_balance("KRW"))
    amount_krw = min(krw, amount_krw)

    if amount_krw < MIN_ORDER_KRW:
        print(f"[{ticker}][BUY] KRW 부족 (보유: {krw:.0f} KRW)")
        return

    if DRY_RUN:
        print(f"[{ticker}][BUY][DRY_RUN] {amount_krw:.0f} 지정가 매수 주문 (실제 주문 X)")
    else:
        resp = upbit.buy_limit_order(ticker, target_price, amount_krw)
        print(f"[{ticker}][BUY][DONE] {resp}")


##### 지정가 매수 (Percentage) #####
def buy_limit_percentage(upbit: Upbit, ticker: str, target_price, percentage):
    """
    - 해당 종목 지정가 매수 주문
    - target_price: 주문 가격
    - percentage: 주문할 양 비율 (0.0 ~ 1.0)
    """

    percentage = max(0.0, min(1.0, percentage))
    amount_krw = float(upbit.get_balance("KRW")) * percentage

    buy_limit(upbit, ticker, target_price, amount_krw)


##### 지정가 매도 (Amount) #####
def sell_limit(upbit: Upbit, ticker: str, target_price, amount_krw):
    """
    - 해당 종목 지정가 매도 주문
    - target_price: 주문 가격
    - amount_krw: 주문할 양
    """

    coin = ticker.split("-")[1]
    volume_krw = float(upbit.get_amount(coin))

    if volume_krw <= amount_krw:
        print(f"[{ticker}][SELL] 보유 {coin} 수량 없음")
        return

    if DRY_RUN:
        print(f"[{ticker}][SELL][DRY_RUN] {volume_krw} {coin} 지정가 매도 주문 (실제 주문 X)")
    else:
        resp = upbit.sell_limit_order(ticker, target_price, amount_krw)
        print(f"[{ticker}][SELL][DONE] 지정가 매도 주문: {resp}")


##### 지정가 매도 (Percentage) #####
def sell_limit_percentage(upbit: Upbit, ticker: str, target_price, percentage: float):
    """
    - 해당 종목 지정가 매도 주문
    - target_price: 주문 가격
    - percentage: 주문할 양 비율 (0.0 ~ 1.0)
    """

    percentage = max(0.0, min(1.0, percentage))

    coin = ticker.split("-")[1]
    amount = float(upbit.get_amount(coin)) * percentage

    sell_limit(upbit, ticker, target_price, amount)

#### 모든 미체결 주문 받아오기 ####
def get_all_orders():
    """
    - 모든 미체결 주문 받아오기
    """

    access_key = ACCESS_KEY
    secret_key = SECRET_KEY

    payload = {
        'access_key': access_key,
        'nonce': str(uuid.uuid4()),
    }

    jwt_token = jwt.encode(payload, secret_key)
    authorize_token = 'Bearer {}'.format(jwt_token)
    headers = {"Authorization": authorize_token}

    res = requests.get("https://api.upbit.com/v1/orders?state=wait", headers=headers)
    return res.json()

##### 모든 주문 취소 (전체 종목) #####
def cancel_all_orders(upbit: Upbit):
    """
    - 미체결된 모든 주문 취소
    """
    orders = get_all_orders()

    if not orders:
        print("[CANCEL_ALL][DONE] 현재 미체결 주문 없음.")
        return

    for order in orders:
        cancel_order(upbit, order.get("uuid"))

##### 특정 종목의 모든 주문 취소 #####
def cancel_orders_by_ticker(upbit: Upbit, ticker: str):
    """
    - 해당 종목의 미체결 주문만 모두 취소
    """
    orders = upbit.get_order(ticker)

    if not orders:
        print(f"[CANCEL][{ticker}] 현재 미체결 주문 없음.")
        return

    for order in orders:
        if order.get("market") == ticker:
            cancel_order(upbit, order.get("uuid"))
            

##### 단일 주문 UUID 취소 #####
def cancel_order(upbit: Upbit, uuid: str):
    """
    - 개별 주문 취소
    """
    try:
        resp = upbit.cancel_order(uuid)
        print(f"[CANCEL][UUID:{uuid}] 취소 완료: {resp}")
    except Exception as e:
        print(f"[CANCEL][UUID:{uuid}] 취소 실패: {e}")
    
    time.sleep(0.2)

##### 현재 보유 중인 모든 코인 전량 매도 #####
def sell_all_holdings(upbit: Upbit):
    """
    - 현재 보유 중인 모든 종목 시장가 전량 매도
    """
    balances = upbit.get_balances()

    for b in balances:
        currency = b.get("currency")
        balance = float(b.get("balance"))

        if currency == "KRW":
            continue  # 현금은 패스
        if balance <= 0:
            continue

        ticker = f"KRW-{currency}"
        amount_krw = float(upbit.get_amount(currency))

        if DRY_RUN:
            print(f"[{ticker}][SELL][DRY_RUN] 보유 전량 시장가 매도({amount_krw:.0f} KRW)")
        else:
            resp = upbit.sell_market_order(ticker, amount_krw)
            print(f"[{ticker}][SELL][DONE] 전량 매도 완료: {resp}")

def get_ohlcv(ticker, interval="minute1", count=2):
    return pyupbit.get_ohlcv(ticker, interval=interval, count=count)

def get_current_price(ticker):
    return pyupbit.get_current_price(ticker)

def get_balance(upbit: Upbit, coin: str) -> float:
    return float(upbit.get_balance(coin))

def get_avg_buy_price(upbit: Upbit, coin: str) -> float:
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == coin:
            return float(b.get('avg_buy_price', 0.0))
    return 0.0

def get_1sec_ohlcv(ticker: str, count: int = 60) -> pd.DataFrame:
    """
    Upbit의 체결 데이터를 기반으로 1초 단위 OHLCV + value 데이터프레임을 생성합니다.

    Args:
        ticker (str): 예: 'KRW-BTC'
        count (int): 최대 몇 초 전까지 조회할지 (최대 60초 권장)

    Returns:
        pd.DataFrame: index = timestamp (초 단위), columns = open, high, low, close, volume, value
    """
    url = "https://api.upbit.com/v1/trades/ticks"
    params = {"market": ticker, "count": 200}
    headers = {"Accept": "application/json"}

    res = requests.get(url, headers=headers, params=params)
    res.raise_for_status()
    trades = res.json()

    rows = []
    for t in trades:
        ts = int(pd.to_datetime(t['timestamp'], unit='ms').timestamp())
        rows.append({
            "timestamp": ts,
            "price": t['trade_price'],
            "volume": t['trade_volume']
        })

    df = pd.DataFrame(rows)
    df = df.groupby("timestamp").agg({
        "price": ['first', 'max', 'min', 'last'],
        "volume": 'sum'
    })
    df.columns = ['open', 'high', 'low', 'close', 'volume']
    df = df.sort_index()

    # 거래대금 = 종가 * 거래량 (초 단위)
    df['value'] = df['close'] * df['volume']

    return df.tail(count)

def get_neutral_candle_ratio(df, n=10, threshold=0.0005) -> float:
    """
    보합(시가와 종가 차이가 거의 없는) 봉의 비율을 계산합니다.

    Args:
        df (pd.DataFrame): OHLCV 데이터프레임 (open, close 컬럼 포함)
        n (int): 최근 n개의 봉을 기준으로 계산
        threshold (float): 보합으로 간주할 시가 대비 종가 차이 비율 (예: 0.001 = 0.1%)

    Returns:
        float: 보합 봉 비율 (ex: 0.3 = 30%)
    """
    if df is None or len(df) < n:
        return 0.0

    df_recent = df.tail(n)
    neutral_count = 0

    for _, row in df_recent.iterrows():
        open_price = row['open']
        close_price = row['close']

        if open_price == 0:
            continue  # 0으로 나누기 방지

        diff_ratio = abs(close_price - open_price) / open_price
        if diff_ratio <= threshold:
            neutral_count += 1

    return neutral_count / n

def get_top_volume_tickers(limit=100) -> list:
    """
    업비트에서 24시간 거래대금 상위 종목 리스트를 반환합니다.

    Args:
        limit (int): 상위 몇 개 종목까지 추출할지 (기본 100)

    Returns:
        List[str]: 거래대금 기준 상위 종목 티커 리스트
    """
    url = "https://api.upbit.com/v1/ticker"
    tickers = requests.get("https://api.upbit.com/v1/market/all?isDetails=false").json()
    krw_tickers = [t["market"] for t in tickers if t["market"].startswith("KRW-")]

    # 요청 (한 번에 최대 100개까지 가능)
    result = []
    for i in range(0, len(krw_tickers), 100):
        chunk = krw_tickers[i:i+100]
        params = {"markets": ",".join(chunk)}
        res = requests.get(url, params=params)
        res.raise_for_status()
        result.extend(res.json())

    # 거래대금 기준 정렬
    sorted_result = sorted(result, key=lambda x: x["acc_trade_price_24h"], reverse=True)

    # 상위 티커만 반환
    return [item["market"] for item in sorted_result[:limit]]

def get_top_gainers(limit=20):
    tickers = requests.get("https://api.upbit.com/v1/market/all?isDetails=false").json()
    krw_tickers = [t["market"] for t in tickers if t["market"].startswith("KRW-")]

    url = "https://api.upbit.com/v1/ticker"
    result = []
    for i in range(0, len(krw_tickers), 100):
        chunk = krw_tickers[i:i+100]
        params = {"markets": ",".join(chunk)}
        res = requests.get(url, params=params)
        res.raise_for_status()
        result.extend(res.json())

    sorted_result = sorted(result, key=lambda x: x["signed_change_rate"], reverse=True)

    df = pd.DataFrame([{
        "ticker": item["market"],
        "change_rate": item["signed_change_rate"],
        "trade_price": item["trade_price"],
        "acc_trade_price_24h": item["acc_trade_price_24h"]
    } for item in sorted_result[:limit]])

    return df