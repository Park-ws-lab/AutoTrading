import pyupbit
import time
import utils
import extensions
from pyupbit import Upbit


records_finded = {}

def find_ticker(blacklist) -> str:
    """
    종목 탐색 알고리즘. 조건에 만족하는 종목의 코드를 반환한다.
    """

    top_ticker_snapshots = utils.get_top_gainers()

    # blacklist 제거
    top_ticker_snapshots = top_ticker_snapshots[~top_ticker_snapshots["ticker"].isin(blacklist)]

    # ticker 문자열 리스트 추출
    search_targets = top_ticker_snapshots["ticker"].tolist()[:30]

    temp_targets = {}

    for ticker in search_targets:
        try:
            df = utils.get_1sec_ohlcv(ticker, count=60)
            if df is None or len(df) < 60:
                continue

            # 거래량이 튀었는가
            spike_percentage = extensions.get_volume_spike_percentage(df, 10, 50)

            # 30추세선의 기울기가 20도 이상인가
            slope_20 = extensions.calculate_trend_slope(df, 20)

            # 5양봉 비율이 0.5 이상인가
            bullish_ratio = extensions.get_bullish_ratio(df, 5)

            # 5봉 거래량 평균
            avg_volume = df['volume'].iloc[-5:].mean()

            # 5봉 평균 거래대금
            avg_value = df['value'].iloc[-5:].mean()

            # 보합 봉 비율
            neutral_candle_percentage = utils.get_neutral_candle_ratio(df, 10, 0)

            if spike_percentage >= 3 and slope_20 >= 5 and neutral_candle_percentage < 0.7:
                temp_targets[ticker] = {
                    "spike_percentage": spike_percentage,
                    "avg_volume": avg_volume }

            if spike_percentage >= 3:
                print(f"[FIND][{ticker}] 거래량 배율: {spike_percentage:.1f}, 20추세: {slope_20:.0f}, 5평균 거래대금: {int(avg_value)}, 보합비율: {neutral_candle_percentage:.1f}")
            else:
                print(f"[FIND][{ticker}] 거래량 안터짐")

            time.sleep(0.1)

        except Exception as e:
            print(f"[FIND ERROR][{ticker}] {e}")

    if not temp_targets:
        return "NONE"

    selected_ticker = max(temp_targets, key=temp_targets.get)
    records_finded[selected_ticker] = {
        "time": time.time(),
        "avg_volume": temp_targets[selected_ticker]['avg_volume']}
    
    time.sleep(0.5)

    return selected_ticker


def check_ticker_state(ticker) -> str:
    """
    해당 종목의 상태를 체크하고 유지할지, 제거할지의 시그널을 반환한다.
    """
    # 기준 시간이 지났는가
    keep_time_passed = time.time() - records_finded[ticker]['time'] >= 200
    
    if not keep_time_passed:
        return "HOLD"

    df = utils.get_1sec_ohlcv(ticker, count=50)
    if df is None or len(df) < 50:
        return "REMOVE"

    # 과거 기록 스파이크 거래량 평균
    recorded_avg_volume = records_finded[ticker]['avg_volume']

    # 현재 거래량 평균
    current_avg_volume = df['volume'][-30:].mean()

    if keep_time_passed and current_avg_volume / recorded_avg_volume < 0.1:
        return "REMOVE"
    
    time.sleep(0.2)
    
    return "HOLD"


buy_time_records = {}

def algorithm(upbit: Upbit, balances: list, current_prices: list, ticker: str) -> str:
    try:
        # 캔들 리스트
        df = utils.get_1sec_ohlcv(ticker, count=100)
        if df is None or len(df) < 100:
            return "REMOVE"

        # 데이터 리스트
        current = df.iloc[-1] # 현재 봉
        open_now = current['open'] # 현재 봉 시가
        close_now = current['close'] # 현재 봉 종가
        high_3min = df.iloc[-4:]['high'].max() # 최근 4개의 캔들 중 고가
        change_rate = (close_now - open_now) / open_now # 현재 초봉 수익률
        percentage_buy = 0.1
        percentage_sell = 1
        buy_delay = 5

        # 직전 a봉 거래량 평균이 직전 b봉 거래량 평균 대비 m배 급등 했는가
        volume_spiked_percentage = extensions.get_volume_spike_percentage(df, 3, 20)
        volume_spiked = volume_spiked_percentage > 3

        # 100초간의 추세
        trend_slope_100 = extensions.calculate_trend_slope(df, 100)

        # 30초간의 추세
        trend_slope_30 = extensions.calculate_trend_slope(df, 30)

        # 10초간의 추세
        trend_slope_10 = extensions.calculate_trend_slope(df, 10)

        # 5초간의 추세
        trend_slope_5 = extensions.calculate_trend_slope(df, 5)

        # 3초간의 추세
        trend_slope_3 = extensions.calculate_trend_slope(df, 3)

        # 최근 n봉 중에서 양봉의 비율
        bullish_ratio = extensions.get_bullish_ratio(df, 10)

        # 현재 해당 종목의 평균 수익률
        total_pnl_rate = extensions.get_ticker_pnl_rate(ticker, balances, current_prices)

        # 현재 종목의 체결강도 (1.0 > 매수 우위, 1.0 > 매도 우위)
        trade_strength = extensions.get_recent_trade_strength(ticker, 200)

        # 직전 거래 후 충분한 시간이 지났는가
        is_delay_passed = True
        if ticker in buy_time_records:
            is_delay_passed = (time.time() - buy_time_records[ticker]) >= buy_delay


        ##### 매매 조건 #####
        now_balance = 0

        for item in balances:
            if item['currency'] == ticker:
                now_balance = item['balance']

        if now_balance > 0 and total_pnl_rate <= -0.03:
            utils.sell_market_percentage(upbit, ticker, 1)
            return "REMOVE"

        ### 매수
        if volume_spiked and bullish_ratio >= 0.5 and trend_slope_5 > 0 and trend_slope_100 > 20 and trade_strength > 0.8 and is_delay_passed:
            utils.buy_market_percentage(upbit, ticker, percentage_buy)
            buy_time_records[ticker] = time.time()
            return "BUY"
        
        ### 익절
        if now_balance > 0 and (trend_slope_3 <= -70 or trend_slope_10 <= -50 or trend_slope_30 <= -30) and trade_strength < 0.7:
            utils.sell_market_percentage(upbit, ticker, percentage_sell)
            return "SELL"
        
        print(f"[TRADE][HOLD][INFO] 거래량 배수:{volume_spiked_percentage:.1f}  양봉비율:{bullish_ratio:.2f}  5추세 각도:{trend_slope_5:.0f}  100추세 각도:{trend_slope_100:.0f}  체결강도:{trade_strength:.1f}  딜레이 충족:{is_delay_passed}")
        return "HOLD"

    except Exception as e:
        print(f"[ALGO ERROR][{ticker}] {e}")
