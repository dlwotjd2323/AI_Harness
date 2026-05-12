import yfinance as yf
from datetime import datetime

def fetch_stock_data(ticker_symbol, days=5):
    """
    야후 파이낸스(yfinance)를 통해 특정 종목의 최근 시장 데이터를 수집하고
    AI가 읽기 쉬운 텍스트 형태로 가공합니다.
    """
    print(f"📡 [{ticker_symbol}] 시장 데이터 수집을 시작합니다...")
    
    try:
        # 1. 티커(종목코드) 객체 생성
        stock = yf.Ticker(ticker_symbol)
        
        # 2. 최근 5일치 과거 데이터(History) 가져오기
        hist = stock.history(period=f"{days}d")
        
        if hist.empty:
            return f"⚠️ {ticker_symbol} 데이터를 찾을 수 없습니다. 종목 코드를 확인하세요."

        # 3. 데이터 가공 (AI 프롬프트용 텍스트로 변환)
        company_name = stock.info.get('shortName', ticker_symbol)
        current_price = hist['Close'].iloc[-1]
        
        report = f"📊 [종목명: {company_name} ({ticker_symbol})]\n"
        report += f"현재가: ${current_price:.2f}\n"
        report += "-" * 30 + "\n"
        report += "[최근 5일 주가 흐름]\n"
        
        for date, row in hist.iterrows():
            date_str = date.strftime("%Y-%m-%d")
            close_price = row['Close']
            volume = row['Volume']
            report += f"- {date_str}: 종가 ${close_price:.2f} (거래량: {volume:,})\n"
            
        return report

    except Exception as e:
        return f"⚠️ 데이터 수집 중 에러 발생: {e}"

# =====================================================================
# 🚀 실전 데이터 수집 테스트
# =====================================================================
if __name__ == "__main__":
    # 나스닥 대장주 '애플(AAPL)'과 '엔비디아(NVDA)' 데이터 수집 테스트
    target_ticker = "AAPL" # 엔비디아를 원하시면 "NVDA", 테슬라는 "TSLA"로 변경하세요
    
    market_report = fetch_stock_data(target_ticker)
    
    print("\n" + "="*40)
    print("📥 하네스 정보 수집 부서 보고서")
    print("="*40)
    print(market_report)
    