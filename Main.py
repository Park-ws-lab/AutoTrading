#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import pyupbit  # pip install pyupbit
from dotenv import load_dotenv
from strategy_scalping import algorithm, find_tickers
from utils import cancel_all_orders, sell_all_holdings

load_dotenv()

ACCESS_KEY = os.getenv("ACCESS_KEY", "")
SECRET_KEY = os.getenv("SECRET_KEY", "")
INTERVAL_TRADING = float(os.getenv("INTERVAL_TRADING", 3))
INTERVAL_FINDING = float(os.getenv("INTERVAL_FINDING", 60))
CANDLE_COUNT = int(os.getenv("CANDLE_COUNT", 3))
ORDER_BUDGET = float(os.getenv("ORDER_BUDGET", 50000))
SLEEP_SECONDS = float(os.getenv("SLEEP_SECONDS", 1))
DRY_RUN = os.getenv("DRY_RUN", "True").lower() == "true"
MIN_ORDER_KRW = float(os.getenv("MIN_ORDER_KRW", 5000))


tickers_current = []


def refresh_tickers():
    finded = find_tickers()
    if not finded:
        return
    for ticker in finded:
        if ticker not in tickers_current:
            tickers_current.append(ticker)


def main():
    if not ACCESS_KEY or not SECRET_KEY:
        print("[WARN] API 키가 없습니다. (DRY_RUN=True 권장)")

    upbit = pyupbit.Upbit(ACCESS_KEY, SECRET_KEY)

    print("=== 시작 ===")
    print(f"종목찾기 주기={INTERVAL_FINDING}, 트레이딩 주기={INTERVAL_TRADING}, 테스트 모드={DRY_RUN}")

    before_find_time = 0

    try:
        while True:
            now = time.time()
            need_to_find = (now - before_find_time) > INTERVAL_FINDING

            if need_to_find:
                print("종목 탐색중...")
                refresh_tickers()
                before_find_time = now
                time.sleep(0.5)

            current_balances = upbit.get_balances()
            time.sleep(0.1)
            current_prices = pyupbit.get_current_price(tickers_current)
            time.sleep(0.1)

            for ticker in tickers_current:
                algorithm(upbit, current_balances, current_prices, ticker)
                time.sleep(0.2)

            time.sleep(INTERVAL_TRADING)

    except KeyboardInterrupt:
        print("\n[EXIT] 수동 종료 감지됨")
        # cancel_all_orders(upbit)
        sell_all_holdings(upbit)

    except Exception as e:
        print(f"[FATAL ERROR] {e}")
        # cancel_all_orders(upbit)
        sell_all_holdings(upbit)

    finally:
        print("[CLEANUP] 자동매매 종료 완료")


if __name__ == "__main__":
    main()