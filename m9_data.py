import os
import requests
import pandas as pd
import mplfinance as mpf
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
OBSIDIAN_PATH = os.getenv("OBSIDIAN_VAULT_PATH", "./Obsidian_Trading")

def get_upbit_btc_data():
    """100일치 데이터를 바탕으로 기술적 지표를 계산하고 최근 30일 차트를 그립니다."""
    ticker_url = "https://api.upbit.com/v1/ticker?markets=KRW-BTC"
    # 🌟 [수정됨] 60일 이동평균선 등을 계산하기 위해 넉넉히 과거 100일치 데이터를 가져옵니다.
    candle_url = "https://api.upbit.com/v1/candles/days?market=KRW-BTC&count=100"
    
    try:
        ticker_res = requests.get(ticker_url)
        ticker_res.raise_for_status()
        t_data = ticker_res.json()[0]
        
        candle_res = requests.get(candle_url)
        candle_res.raise_for_status()
        c_data = candle_res.json()
        
        df = pd.DataFrame(c_data)
        df['candle_date_time_kst'] = pd.to_datetime(df['candle_date_time_kst'])
        df = df.set_index('candle_date_time_kst')
        df = df.sort_index()
        df = df.rename(columns={'opening_price': 'Open', 'high_price': 'High', 'low_price': 'Low', 'trade_price': 'Close', 'candle_acc_trade_volume': 'Volume'})
        
        # ==========================================
        # 🌟 [추가됨] 전문 기술적 지표 계산 (Pandas 연산)
        # ==========================================
        # 1. 이동평균선 (MA20: 주황색, MA60: 보라색)
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        
        # 2. 볼린저 밴드 (표준편차 2배수 기준)
        std = df['Close'].rolling(window=20).std()
        df['Upper'] = df['MA20'] + (std * 2)
        df['Lower'] = df['MA20'] - (std * 2)
        
        # 3. RSI (14일 기준 모멘텀 지표)
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # ==========================================
        
        # 계산은 100일치로 했지만, 차트 이미지는 최근 30일치만 깔끔하게 잘라냅니다.
        plot_df = df.iloc[-30:]
        
        if not os.path.exists(OBSIDIAN_PATH):
            os.makedirs(OBSIDIAN_PATH, exist_ok=True)
            
        now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        chart_filename = f"BTC_Chart_{now_str}.png"
        chart_filepath = os.path.join(OBSIDIAN_PATH, chart_filename)
        
        # 🌟 [추가됨] 기존 캔들 차트 위에 덧그릴 보조 지표(Addplot) 레이어 설정
        apds = [
            mpf.make_addplot(plot_df['Upper'], color='gray', linestyle='dashed', alpha=0.5, panel=0), # 볼린저 상단
            mpf.make_addplot(plot_df['Lower'], color='gray', linestyle='dashed', alpha=0.5, panel=0), # 볼린저 하단
            mpf.make_addplot(plot_df['MA20'], color='orange', width=1.5, panel=0),                    # 20일선
            mpf.make_addplot(plot_df['MA60'], color='purple', width=1.5, panel=0),                    # 60일선
            mpf.make_addplot(plot_df['RSI'], color='magenta', panel=2, ylabel='RSI (14)')             # RSI (독립된 맨 아래 패널)
        ]
        
        mc = mpf.make_marketcolors(up='r', down='b', edge='inherit', wick='inherit', volume='inherit')
        s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':')
        
        # 패널 비율 조정 (0번: 캔들/이평/볼린저, 1번: 거래량, 2번: RSI)
        mpf.plot(plot_df, type='candle', volume=True, style=s, savefig=chart_filepath, 
                 title="BTC/KRW 30 Days (w/ MA, BB, RSI)", 
                 addplot=apds, panel_ratios=(5, 1, 2), figratio=(10, 8))
        
        # 🌟 [수정됨] AI 프롬프트에 제공할 텍스트에도 최신 RSI 값을 추가!
        current_rsi = plot_df['RSI'].iloc[-1]
        market_context = (
            f"📈 [현재 시장 데이터 브리핑]\n"
            f"- 현재가: {t_data['trade_price']:,} KRW\n"
            f"- 24h 최고가: {t_data['high_price']:,} KRW\n"
            f"- 24h 최저가: {t_data['low_price']:,} KRW\n"
            f"- 24h 거래량: {t_data['acc_trade_volume_24h']:,.2f} BTC\n"
            f"- 현재 RSI (14): {current_rsi:.1f} (30이하 과매도, 70이상 과매수)\n\n"
            f"📊 **[시황 차트 이미지]**\n"
            f"![[{chart_filename}]]"
        )
        return market_context, chart_filepath
        
    except Exception as e:
        return f"⚠️ 시세 데이터 수집 실패: {e}", None