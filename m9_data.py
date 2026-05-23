import os
import requests
import pandas as pd
import mplfinance as mpf
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
OBSIDIAN_PATH = os.getenv("OBSIDIAN_VAULT_PATH", "./Obsidian_Trading")

def get_upbit_btc_data():
    """업비트 API로 텍스트 시세와 30일치 캔들 차트 이미지를 생성합니다."""
    ticker_url = "https://api.upbit.com/v1/ticker?markets=KRW-BTC"
    candle_url = "https://api.upbit.com/v1/candles/days?market=KRW-BTC&count=30"
    
    try:
        # 1. 텍스트 시세 수집
        ticker_res = requests.get(ticker_url)
        ticker_res.raise_for_status()
        t_data = ticker_res.json()[0]
        
        # 2. 차트용 캔들 데이터 수집 및 가공 (Pandas)
        candle_res = requests.get(candle_url)
        candle_res.raise_for_status()
        c_data = candle_res.json()
        
        df = pd.DataFrame(c_data)
        df['candle_date_time_kst'] = pd.to_datetime(df['candle_date_time_kst'])
        df = df.set_index('candle_date_time_kst')
        df = df.sort_index()
        df = df.rename(columns={'opening_price': 'Open', 'high_price': 'High', 'low_price': 'Low', 'trade_price': 'Close', 'candle_acc_trade_volume': 'Volume'})
        
        # 3. 차트 이미지 생성 및 물리적 저장
        if not os.path.exists(OBSIDIAN_PATH):
            os.makedirs(OBSIDIAN_PATH, exist_ok=True)
            
        now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        chart_filename = f"BTC_Chart_{now_str}.png"
        chart_filepath = os.path.join(OBSIDIAN_PATH, chart_filename)
        
        mc = mpf.make_marketcolors(up='r', down='b', edge='inherit', wick='inherit', volume='inherit')
        s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':')
        mpf.plot(df, type='candle', volume=True, style=s, savefig=chart_filepath, title="BTC/KRW 30 Days")
        
        # 4. 옵시디언 임베딩 텍스트 및 파일 경로 반환
        market_context = (
            f"📈 [현재 시장 데이터 브리핑]\n"
            f"- 현재가: {t_data['trade_price']:,} KRW\n"
            f"- 24h 최고가: {t_data['high_price']:,} KRW\n"
            f"- 24h 최저가: {t_data['low_price']:,} KRW\n"
            f"- 24h 거래량: {t_data['acc_trade_volume_24h']:,.2f} BTC\n\n"
            f"📊 **[시황 차트 이미지]**\n"
            f"![[{chart_filename}]]"
        )
        return market_context, chart_filepath
        
    except Exception as e:
        return f"⚠️ 시세 데이터 수집 실패: {e}", None