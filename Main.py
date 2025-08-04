#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import pyupbit  # pip install pyupbit
import utils
from dotenv import load_dotenv
from strategy_scalping import algorithm, find_ticker, check_ticker_state

load_dotenv()

ACCESS_KEY = os.getenv("ACCESS_KEY", "")
SECRET_KEY = os.getenv("SECRET_KEY", "")
INTERVAL_LOOP = float(os.getenv("INTERVAL_LOOP", 3))
INTERVAL_FINDING = float(os.getenv("INTERVAL_FINDING", 60))
DRY_RUN = os.getenv("DRY_RUN", "True").lower() == "true"
MIN_ORDER_KRW = float(os.getenv("MIN_ORDER_KRW", 5000))
MAX_TARGET_TICKERS = int(os.getenv("MAX_TARGET_TICKERS", 3))


def main():
    if not ACCESS_KEY or not SECRET_KEY:
        print("[WARN] API 키가 없습니다. (DRY_RUN=True 권장)")

    upbit = pyupbit.Upbit(ACCESS_KEY, SECRET_KEY)

    print("=== 시작 ===")
    print(f"종목찾기 주기={INTERVAL_FINDING}, 전체 루프 주기={INTERVAL_LOOP}, 테스트 모드={DRY_RUN}")

    tickers_current = []
    before_find_time = 0

    try:
        while True:
            
            # 현재 잔고 캐싱
            current_balances = upbit.get_balances()
            # 현재 전체 시장 가격 캐싱
            current_prices = pyupbit.get_current_price(tickers_current)

            time.sleep(0.2)

            ### CHECK_TICKERS
            if not tickers_current:
                for ticker in tickers_current:
                    state = check_ticker_state(ticker)

                    if state == "REMOVE":
                        tickers_current.remove(ticker)
                        # utils.cancel_orders_by_ticker(ticker)
                        utils.sell_market_percentage(upbit, ticker, 1)
                        print(f"[MAIN][DONE] 매매 대상 제거 완료: {ticker}, 현재 매매 대상 개수: {len(tickers_current)}")
                time.sleep(0.5)

            ### FINDING
            # 현재 매매 대상 개수가 초과했는가
            is_exceed_target_count = len(tickers_current) > MAX_TARGET_TICKERS
            # 탐색 주기가 되었는가
            passed_find_delay = (time.time() - before_find_time) > INTERVAL_FINDING

            if not is_exceed_target_count and passed_find_delay:
                print("[MAIN] 종목 탐색중...")

                # tickers = pyupbit.get_tickers(fiat="KRW")

                # 이미 대상인 종목은 제외
                # for item in tickers_current:
                #     tickers.remove(item)

                finded = find_ticker(tickers_current)

                if finded == "NONE":
                    continue
                
                tickers_current.append(finded)
                print(f"[MAIN][DONE] 매매 대상 추가 완료: {finded}, 현재 매매 대상 개수: {len(tickers_current)}/{MAX_TARGET_TICKERS}")
                before_find_time = time.time()
                time.sleep(0.5)

            ### TRADING
            if len(tickers_current) > 0:
                for ticker in tickers_current:
                    signal = algorithm(upbit, current_balances, current_prices, ticker)

                    if signal == "REMOVE":
                        tickers_current.remove(ticker)
                        # utils.cancel_orders_by_ticker(upbit, ticker)
                        utils.sell_market_percentage(upbit, ticker, 1)
                        print(f"[TRADE][DONE] 매매 대상 제거 완료: {ticker}, 현재 매매 대상 개수: {len(tickers_current)}")

                    time.sleep(0.2)

            time.sleep(INTERVAL_LOOP)

    except KeyboardInterrupt:
        print("\n[EXIT] 수동 종료 감지됨")
        if upbit is not None:
            utils.cancel_all_orders(upbit)
            utils.sell_all_holdings(upbit)

    except Exception as e:
        print(f"[FATAL ERROR] {e}")
        if upbit is not None:
            utils.cancel_all_orders(upbit)
            utils.sell_all_holdings(upbit)

    finally:
        print("[CLEANUP] 자동매매 종료 완료")


if __name__ == "__main__":
    main()