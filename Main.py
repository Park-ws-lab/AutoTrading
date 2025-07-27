#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
업비트 자동매매 템플릿 (멀티 티커 대응, 최대한 단순하게)
- main()        : 설정, 전체 루프
- algorithm()   : 티커별로 동일한 단순 이동평균 크로스 전략
- buy()/sell()  : 티커별 시장가 매수/매도
"""

import os
import time
import pyupbit  # pip install pyupbit

########################################################
# 0) 전역 설정
########################################################
ACCESS_KEY = os.getenv("UPBIT_ACCESS_KEY", "")
SECRET_KEY = os.getenv("UPBIT_SECRET_KEY", "")

# 여러 종목을 여기에 넣으세요.
TICKERS = [
    "KRW-BTC",
    "KRW-ETH",
    # "KRW-XRP",
    # ...
]

INTERVAL = "minute1"       # 'minute1', 'minute5', 'day' 등
CANDLE_COUNT = 200
ORDER_BUDGET = 10000       # 1회 매수 시 티커당 사용할 최대 KRW
SLEEP_SECONDS = 1.0        # 루프(전체 TICKERS 한 바퀴) 끝나고 쉬는 시간
DRY_RUN = True
MIN_ORDER_KRW = 5000       # 업비트 최소 주문금액(대략)

########################################################
# 1) 전략
########################################################
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

########################################################
# 2) 주문함수 (티커별)
########################################################
def buy(upbit, ticker: str):
    """
    - 현재 보유 KRW에서 ORDER_BUDGET 만큼 해당 티커를 시장가 매수
    - DRY_RUN=True면 실제로 주문하지 않습니다.
    """
    krw = float(upbit.get_balance("KRW"))
    amount = min(krw, ORDER_BUDGET)

    if amount < MIN_ORDER_KRW:
        print(f"[{ticker}][BUY] KRW 부족 (보유: {krw:.0f} KRW)")
        return

    if DRY_RUN:
        print(f"[{ticker}][BUY][DRY_RUN] {amount:.0f} KRW 시장가 매수 (실제 주문 X)")
    else:
        resp = upbit.buy_market_order(ticker, amount)
        print(f"[{ticker}][BUY][DONE] {resp}")

def sell(upbit, ticker: str):
    """
    - 해당 티커의 코인 전체 수량 시장가 매도
    - DRY_RUN=True면 실제로 주문하지 않습니다.
    """
    coin = ticker.split("-")[1]
    volume = float(upbit.get_balance(coin))
    if volume <= 0:
        print(f"[{ticker}][SELL] 보유 {coin} 수량 없음")
        return

    if DRY_RUN:
        print(f"[{ticker}][SELL][DRY_RUN] {volume} {coin} 시장가 매도 (실제 주문 X)")
    else:
        resp = upbit.sell_market_order(ticker, volume)
        print(f"[{ticker}][SELL][DONE] {resp}")

########################################################
# 3) 메인 루프
########################################################
def main():
    if not ACCESS_KEY or not SECRET_KEY:
        print("[WARN] API 키가 없습니다. (DRY_RUN=True 권장)")
    upbit = pyupbit.Upbit(ACCESS_KEY, SECRET_KEY)

    print("=== 시작 ===")
    print(f"TICKERS={TICKERS}, INTERVAL={INTERVAL}, DRY_RUN={DRY_RUN}")

    while True:
        try:
            # 모든 티커를 한 바퀴 돕니다.
            for ticker in TICKERS:
                try:
                    # 1) 티커별 캔들 가져오기
                    candles = pyupbit.get_ohlcv(ticker, interval=INTERVAL, count=CANDLE_COUNT)

                    # 2) 전략 실행
                    signal = algorithm(candles, ticker)
                    print(f"[{ticker}][SIGNAL] {signal}")

                    # 3) 신호에 따른 주문
                    if signal == "BUY":
                        buy(upbit, ticker)
                    elif signal == "SELL":
                        sell(upbit, ticker)
                    else:
                        # HOLD
                        pass

                    # (선택) 너무 빠른 연속 호출 방지용 소량 sleep
                    time.sleep(0.2)

                except Exception as e_ticker:
                    print(f"[{ticker}][ERROR] {e_ticker}")

        except Exception as e:
            print(f"[ERROR] {e}")

        # 한 바퀴 다 돌았으면 쉬기
        time.sleep(SLEEP_SECONDS)

if __name__ == "__main__":
    main()
