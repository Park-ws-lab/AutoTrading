import pyupbit
import time
import utils
from pyupbit import Upbit
from utils import (
    get_ohlcv, get_current_price,
    get_balance, get_avg_buy_price,
    buy_market, sell_market_percentage
)
from extensions import is_volume_spike, calculate_trend_slope, get_bullish_ratio, get_ticker_pnl_rate, get_trade_strength



def find_tickers(threshold=3.0):
    """
    거래량 급등 종목 탐색 (1분봉 기준 전봉 대비 volume n배 이상)

    Args:
        threshold (float): 거래량 급등으로 판단할 배수 기준 (ex. 3.0이면 전봉 대비 3배 이상이면 선택)

    Returns:
        List[str]: 거래량이 급등한 KRW 마켓 티커 리스트
    """
    tickers = pyupbit.get_tickers(fiat="KRW")
    result = []

    for ticker in tickers:
        try:
            # 최근 3개의 1분봉 데이터 가져오기
            df = get_ohlcv(ticker, interval="minute1", count=3)
            if df is None or len(df) < 2:
                continue

            # 직전봉 대비 현재봉 거래량 비교
            vol_now = df.iloc[-1]["volume"]
            vol_prev = df.iloc[-2]["volume"]


            if vol_prev == 0:
                continue  # 0으로 나누는 경우 제외

            # 거래량이 설정 기준 이상이면 종목 리스트에 추가
            if (vol_now / vol_prev) >= threshold:
                print(f"ticker: {ticker}, 직전 분봉 대비 거래량 상승률: {(vol_now / vol_prev):.2%} => 추가!")
                result.append(ticker)
                time.sleep(0.2)

        except Exception as e:
            print(f"[FIND ERROR][{ticker}] {e}")

    return result



buy_time_map = {}

def algorithm(upbit: Upbit, balances: list, current_prices: list, ticker: str):
    try:

        # 캔들 리스트
        df = get_ohlcv(ticker, interval="seconds", count=100)
        if df is None or len(df) < 100:
            return

        # 데이터 리스트
        current = df.iloc[-1] # 현재 봉
        open_now = current['open'] # 현재 봉 시가
        close_now = current['close'] # 현재 봉 종가
        high_3min = df.iloc[-4:]['high'].max() # 최근 4개의 캔들 중 고가
        change_rate = (close_now - open_now) / open_now # 현재 초봉 수익률
        percentage_buy = 0.1
        percentage_sell = 0.5
        buy_delay = 5

        # 거래량이 직전 n봉 평균 대비 m배 급등 했는가
        volume_spiked = is_volume_spike(df, 20, 50)

        # 100초간의 추세
        trend_slope_100 = calculate_trend_slope(df, 100)

        # 30초간의 추세
        trend_slope_30 = calculate_trend_slope(df, 30)

        # 10초간의 추세
        trend_slope_10 = calculate_trend_slope(df, 10)

        # 5초간의 추세
        trend_slope_5 = calculate_trend_slope(df, 5)

        # 3초간의 추세
        trend_slope_3 = calculate_trend_slope(df, 3)

        # 최근 n봉 중에서 양봉의 비율
        bullish_ratio = get_bullish_ratio(df, 10)

        # 현재 해당 종목의 평균 수익률
        total_pnl_rate = get_ticker_pnl_rate(ticker, balances, current_prices)

        # 현재 종목의 체결강도 (1.0 > 매수 우위, 1.0 > 매도 우위)
        trade_strength = get_trade_strength(ticker, 200)

        # 직전 거래 후 충분한 시간이 지났는가
        is_delay_passed = True
        if ticker in buy_time_map:
            is_delay_passed = (time.time() - buy_time_map[ticker]) >= buy_delay


        ##### 매매 조건 #####
        if total_pnl_rate <= -0.03:
            utils.sell_market_percentage(upbit, ticker, 1)
            # TODO: 해당 종목 트레이딩 대상에서 제외할 것

        elif bullish_ratio >= 0.6 and trend_slope_5 > 0 and trend_slope_100 > 0.2 and trade_strength > 1.0 and is_delay_passed:
            # 매수
            utils.buy_market_percentage(upbit, ticker, percentage_buy)
        
        elif trend_slope_3 <= -0.7 or trend_slope_10 <= -0.5 or trend_slope_30 <= -0.3:
            # 익절
            utils.sell_market_percentage(upbit, ticker, percentage_sell)

    except Exception as e:
        print(f"[ALGO ERROR][{ticker}] {e}")
