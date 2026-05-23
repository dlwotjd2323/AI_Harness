import os
import requests
import pandas as pd
import matplotlib
matplotlib.use('Agg') # 🌟 [긴급 패치] GUI 창을 띄우지 않고 파일로만 렌더링하도록 강제 설정 (스레드 에러 방지)
import mplfinance as mpf
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
OBSIDIAN_PATH = os.getenv("OBSIDIAN_VAULT_PATH", "./Obsidian_Trading")

def get_upbit_data(ticker="KRW-BTC"):
    coin_name = ticker.split('-')[1]
    
    ticker_url = f"https://api.upbit.com/v1/ticker?markets={ticker}"
    candle_url = f"https://api.upbit.com/v1/candles/days?market={ticker}&count=100"
    
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
        
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        
        std = df['Close'].rolling(window=20).std()
        df['Upper'] = df['MA20'] + (std * 2)
        df['Lower'] = df['MA20'] - (std * 2)
        
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        plot_df = df.iloc[-30:]
        
        if not os.path.exists(OBSIDIAN_PATH):
            os.makedirs(OBSIDIAN_PATH, exist_ok=True)
            
        now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        chart_filename = f"{coin_name}_Chart_{now_str}.png"
        chart_filepath = os.path.join(OBSIDIAN_PATH, chart_filename)
        
        apds = [
            mpf.make_addplot(plot_df['Upper'], color='gray', linestyle='dashed', alpha=0.5, panel=0),
            mpf.make_addplot(plot_df['Lower'], color='gray', linestyle='dashed', alpha=0.5, panel=0),
            mpf.make_addplot(plot_df['MA20'], color='orange', width=1.5, panel=0),
            mpf.make_addplot(plot_df['MA60'], color='purple', width=1.5, panel=0),
            mpf.make_addplot(plot_df['RSI'], color='magenta', panel=2, ylabel='RSI (14)')
        ]
        
        mc = mpf.make_marketcolors(up='r', down='b', edge='inherit', wick='inherit', volume='inherit')
        s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':')
        
        mpf.plot(plot_df, type='candle', volume=True, style=s, savefig=chart_filepath, 
                 title=f"{coin_name}/KRW 30 Days (w/ MA, BB, RSI)", 
                 addplot=apds, panel_ratios=(5, 1, 2), figratio=(10, 8))
        
        current_rsi = plot_df['RSI'].iloc[-1]
        market_context = (
            f"📈 [현재 {coin_name} 시장 데이터 브리핑]\n"
            f"- 현재가: {t_data['trade_price']:,} KRW\n"
            f"- 24h 최고가: {t_data['high_price']:,} KRW\n"
            f"- 24h 최저가: {t_data['low_price']:,} KRW\n"
            f"- 24h 거래량: {t_data['acc_trade_volume_24h']:,.2f} {coin_name}\n"
            f"- 현재 RSI (14): {current_rsi:.1f} (30이하 과매도, 70이상 과매수)\n\n"
            f"📊 **[시황 차트 이미지]**\n"
            f"![[{chart_filename}]]"
        )
        # 메모리 누수 방지를 위해 차트 객체 초기화 (선택적 안정화 조치)
        matplotlib.pyplot.close('all') 
        
        return market_context, chart_filepath
        
    except Exception as e:
        return f"⚠️ {ticker} 시세 데이터 수집 실패: {e}", None