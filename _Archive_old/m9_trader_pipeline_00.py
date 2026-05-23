import os
import yfinance as yf
import pandas as pd
from ta.trend import MACD, SMAIndicator
from ta.momentum import RSIIndicator
from datetime import datetime

# =====================================================================
# ⚙️ 하네스 중앙 통제 스위치 
# =====================================================================
IS_REAL_BRAIN_ON = False  
BRAIN_URL = "YOUR_TOKEN"

def ask_brain(prompt, system_prompt="너는 월스트리트 헤지펀드의 수석 퀀트 트레이더야."):
    if not IS_REAL_BRAIN_ON:
        print("💡 [Mock 모드] AI 펀드매니저가 퀀트 지표를 분석 중입니다...")
        return "RSI가 45로 과열되지 않았으며, 주가가 20일 이동평균선 위에 안착했습니다. MACD 시그널이 골든크로스를 발생시켰으므로 상승 여력이 충분합니다. **'적극 매수(STRONG BUY)'**를 추천합니다. (목표수익률 15%)"

    from openai import OpenAI
    client = OpenAI(base_url=BRAIN_URL, api_key="lm-studio")
    response = client.chat.completions.create(
        model="local-model",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
        temperature=0.2
    )
    return response.choices[0].message.content.strip()

# =====================================================================
# 1. 정보 수집 부서 (M9-1: 퀀트 보조지표 TA 연동)
# =====================================================================
def fetch_stock_data_with_ta(ticker_symbol):
    # 보조 지표를 정확히 계산하기 위해 과거 60일치 데이터를 넉넉히 가져옵니다.
    stock = yf.Ticker(ticker_symbol)
    df = stock.history(period="60d")
    
    if df.empty:
        return f"⚠️ {ticker_symbol} 데이터를 불러오지 못했습니다."

    # 📈 기술적 지표(TA) 계산
    # 1. MA20 (20일 이동평균선: 단기 추세선)
    df['MA20'] = SMAIndicator(close=df['Close'], window=20).sma_indicator()
    # 2. RSI (14일 기준: 30 이하면 과매도, 70 이상이면 과매수)
    df['RSI'] = RSIIndicator(close=df['Close'], window=14).rsi()
    # 3. MACD (추세 전환 지표)
    macd = MACD(close=df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()

    # 가장 최근(오늘)의 데이터 추출
    latest = df.iloc[-1]
    current_price = latest['Close']
    ma20 = latest['MA20']
    rsi = latest['RSI']
    macd_val = latest['MACD']
    macd_sig = latest['MACD_Signal']
    
    # AI에게 던져줄 정제된 퀀트 보고서 작성
    report = f"📊 [종목명: {ticker_symbol} 퀀트 분석 데이터]\n"
    report += f"▶ 현재가: ${current_price:.2f}\n"
    report += f"▶ 20일 이동평균선(MA20): ${ma20:.2f} (현재가가 이보다 높으면 단기 상승세)\n"
    report += f"▶ RSI(14): {rsi:.2f} (30이하 매수권, 70이상 매도권)\n"
    report += f"▶ MACD: {macd_val:.3f} / Signal: {macd_sig:.3f} (MACD가 Signal을 상향 돌파하면 매수 신호)\n"
    report += "-" * 30 + "\n[최근 5일 주가 흐름]\n"
    
    for date, row in df.tail(5).iterrows():
        report += f"- {date.strftime('%Y-%m-%d')}: 종가 ${row['Close']:.2f}\n"
    return report

# =====================================================================
# 2. 지식 규합 부서 (M10 매매일지 자동 작성)
# =====================================================================
def save_trading_journal(ticker, market_data, ai_opinion, base_path):
    today = datetime.now().strftime('%Y-%m-%d')
    title = f"{today}_{ticker}_매매전략_TA"
    
    tags = f"#M9_트레이더 #퀀트분석 #매매일지 #{ticker}"
    bi_links = f"[[{ticker}]] [[퀀트매매일지]]"
    code_block = "```"
    
    md_content = f"""---
date: {today}
tags: [M9_트레이더, 퀀트분석, 매매일지, {ticker}]
---
# 📈 {ticker} M9-1 퀀트 매매 전략 보고서

### 📡 1. 퀀트 보조지표 데이터 수집
{code_block}text
{market_data}
{code_block}

### 🧠 2. AI 수석 퀀트 분석 의견
> {ai_opinion}

---
### 🔗 지식 규합 링크
**분류 태그:** {tags}
**연결 문서:** {bi_links}
"""
    
    os.makedirs(base_path, exist_ok=True)
    with open(os.path.join(base_path, f"{title}.md"), 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"✅ [M10] 퀀트 매매 일지 규합 완료! (저장됨: {title}.md)")

# =====================================================================
# 🚀 파이프라인 통합 실행
# =====================================================================
if __name__ == "__main__":
    print("--- 📈 하네스 M9-1 퀀트 트레이딩 파이프라인 가동 ---")
    target_ticker = "AAPL"
    obsidian_path = "./Obsidian_Trading" 
    
    # 1. 퀀트 데이터 수집
    market_data = fetch_stock_data_with_ta(target_ticker)
    
    # 2. AI 분석 지시 (프롬프트 고도화)
    analysis_prompt = f"다음은 {target_ticker}의 퀀트 분석 데이터야. MA20, RSI, MACD 지표를 종합적으로 해석해서 이익 실현(매수/매도/관망) 전략을 세워줘. 근거를 명확히 제시해.\n{market_data}"
    ai_opinion = ask_brain(analysis_prompt)
    
    # 3. 매매일지 옵시디언 저장
    save_trading_journal(target_ticker, market_data, ai_opinion, obsidian_path)