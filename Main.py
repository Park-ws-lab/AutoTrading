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
from dotenv import load_dotenv
from Strategy import algorithm
from Utils import buy_market, sell_market


load_dotenv()

ACCESS_KEY = os.getenv("ACCESS_KEY", "")
SECRET_KEY = os.getenv("SECRET_KEY", "")

TICKERS = os.getenv("TICKERS").replace(" ", "").split(',')
INTERVAL = os.getenv("INTERVAL")
CANDLE_COUNT = os.getenv("CANDLE_COUNT")
ORDER_BUDGET = os.getenv("ORDER_BUDGET")
SLEEP_SECONDS = os.getenv("SLEEP_SECONDS")
DRY_RUN = os.getenv("DRY_RUN")
MIN_ORDER_KRW = os.getenv("MIN_ORDER_KRW")


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
                        buy_market(upbit, ticker)
                    elif signal == "SELL":
                        sell_market(upbit, ticker)
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
