import os
from pyupbit import Upbit
import pyupbit
from dotenv import load_dotenv


load_dotenv()


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


##### 모든 주문 취소 (전체 종목) #####
def cancel_all_orders(upbit: Upbit):
    """
    - 미체결된 모든 주문 취소
    """
    orders = upbit.get_order()

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
    orders = upbit.get_order()

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

# Upbit API
# float(upbit.get_balance(coin_id)) => 보유 코인 수량
# float(upbit.get_amount(coin_id)) => 보유 코인의 KRW 수량