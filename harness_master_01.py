import os
import requests
import yfinance as yf
import pandas as pd
from ta.trend import MACD, SMAIndicator
from ta.momentum import RSIIndicator
from datetime import datetime
import json

# =====================================================================
# ⚙️ 하네스 중앙 통제 스위치 (퇴근 후 IS_REAL_BRAIN_ON = True 필수!)
# =====================================================================
IS_REAL_BRAIN_ON = False  
BRAIN_URL = "YOUR_TOKEN"
DISCORD_WEBHOOK_URL = "YOUR_TOKEN"

# 시각적 직관성을 위한 아바타 URL 예시 (주인님이 가진 이미지 주소로 교체하세요!)
# [A chart icon with a green line and a small buy arrow on a black circle]
TRADING_ICON_URL = "YOUR_TOKEN"
# [A red emergency alarm light icon on a black shield shape]
NOC_ICON_URL = "YOUR_TOKEN"

# =====================================================================
# 1. 기억 인출 부서 (M10-1 RAG) 
# =====================================================================
def search_obsidian_memory(keyword, vault_path):
    print(f"🔍 [M10-1] '{keyword}'에 대한 과거 매매 일지를 회상합니다...")
    if not os.path.exists(vault_path): return "⚠️ 폴더가 없습니다."
    
    found_memories = []
    # 최신 파일 순으로 정렬하여 텍스트 내용 확인
    for filename in sorted(os.listdir(vault_path), reverse=True):
        if filename.endswith(".md"):
            with open(os.path.join(vault_path, filename), 'r', encoding='utf-8') as f:
                content = f.read()
                if keyword.lower() in filename.lower() or keyword.lower() in content.lower():
                    found_memories.append({ "title": filename, "content": content[:300] })
    
    if not found_memories: return f"💡 '{keyword}'에 대한 과거 기억이 없습니다. (신규 진입)"
    
    memory_report = f"📚 [과거 기억 인출 완료: {len(found_memories)}건 발견]\n"
    memory_report += f"[1. {found_memories[0]['title']}]\n{found_memories[0]['content']}..."
    return memory_report

# =====================================================================
# 2. 정보 수집 부서 (M9-1 퀀트)
# =====================================================================
def fetch_stock_data_with_ta(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    df = stock.history(period="60d")
    
    df['MA20'] = SMAIndicator(close=df['Close'], window=20).sma_indicator()
    df['RSI'] = RSIIndicator(close=df['Close'], window=14).rsi()
    macd = MACD(close=df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()

    latest = df.iloc[-1]
    
    report = f"📊 [{ticker_symbol} 현재 퀀트 지표]\n"
    report += f"▶ 현재가: ${latest['Close']:.2f}\n"
    report += f"▶ MA20: ${latest['MA20']:.2f} | RSI: {latest['RSI']:.2f}\n"
    report += f"▶ MACD: {latest['MACD']:.3f} | Signal: {latest['MACD_Signal']:.3f}\n"
    return report

# =====================================================================
# 3. AI 분석 부서 (Mock + RAG)
# =====================================================================
def ask_brain_with_rag(current_data, past_memory, ticker):
    system_prompt = "너는 하네스의 수석 퀀트 트레이더야. 과거 기억과 현재 지표를 반드시 비교해서 연속적인 사고를 보여줘."
    user_prompt = f"[하네스의 과거 기억]\n{past_memory}\n\n[현재 시장 데이터]\n{current_data}\n\n과거의 판단을 회고하고, 현재 지표를 바탕으로 {ticker}의 최종 매매 전략(매수/매도/관망)을 도출해."
    
    if not IS_REAL_BRAIN_ON:
        print("💡 [Mock 모드] 과거 기억과 현재 데이터를 융합 분석 중...")
        # 이미지(Image 2)에서 보여준 것과 동일한 Mock 대답을 반환합니다.
        return "RSI가 72.38로 명백한 과매수 구간에 진입했습니다. 과거의 포지션을 청산하고 **'부분 매도(TAKE PROFIT)'**하여 이익을 실현할 것을 강력히 권장합니다."

    from openai import OpenAI
    client = OpenAI(base_url=BRAIN_URL, api_key="lm-studio")
    response = client.chat.completions.create(
        model="local-model",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        temperature=0.2
    )
    return response.choices[0].message.content.strip()

# =====================================================================
# 4. 지식 규합 부서 (M10 저장) : 새로운 일지 작성
# =====================================================================
def save_trading_journal(ticker, market_data, past_memory, ai_opinion, base_path):
    today = datetime.now().strftime('%Y-%m-%d_%H%M%S') 
    title = f"{today}_{ticker}_매매전략_융합본"
    
    tags = f"#M9_트레이더 #RAG융합 #매매일지 #{ticker}"
    bi_links = f"[[{ticker}]] [[퀀트매매일지]] [[RAG회상기록]]"
    code_block = "```"
    
    md_content = f"""---
date: {today[:10]}
tags: [M9_트레이더, RAG융합, 매매일지, {ticker}]
---
# 📈 {ticker} M9+M10 RAG 융합 매매 보고서

### 🧠 1. 하네스의 과거 회상
{code_block}text
{past_memory}
{code_block}

### 📡 2. 현재 퀀트 데이터 스캔
{code_block}text
{market_data}
{code_block}

### ⚖️ 3. AI 최종 융합 분석 의견
> {ai_opinion}

---
### 🔗 지식 규합 링크
**분류 태그:** {tags}
**연결 문서:** {bi_links}
"""
    
    os.makedirs(base_path, exist_ok=True)
    with open(os.path.join(base_path, f"{title}.md"), 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"✅ [M10] 융합 매매 일지 규합 완료! (저장됨: {title}.md)")
    return ai_opinion

# =====================================================================
# 5. 디스코드 NOC 관제탑 (알림) : 동적 이름 & 프로필
# =====================================================================
def send_discord_alert(ticker, ai_opinion, bot_name="M9 퀀트 트레이더", avatar_url="URL_FOR_TRADING_ICON"):
    print(f"📡 [{bot_name}] 디스코드 알림 전송을 시도합니다...")
    
    data = {
        "username": bot_name, # 동적 이름
        "avatar_url": avatar_url, # ⚠️ 최종 추가 사항: 동적 프로필 사진
        "content": f"🚨 **[{bot_name} 시스템]** 새로운 보고서가 도착했습니다.",
        "embeds": [
            {
                "title": f"📈 {ticker} 분석 결과 요약",
                "description": ai_opinion,
                "color": 5814783, # 보라색 테마
                "footer": {
                    "text": f"하네스 중앙 관제탑 • {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                }
            }
        ]
    }
    
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, data=json.dumps(data), headers={"Content-Type": "application/json"})
        if response.status_code == 204:
            print(f"✅ [디스코드] '{bot_name}'的名義로 알림 전송 성공!")
        else:
            print(f"⚠️ [디스코드] 전송 실패 (상태 코드: {response.status_code})")
    except Exception as e:
        print(f"⚠️ 전송 중 에러 발생: {e}")

# =====================================================================
# 🚀 그랜드 마스터 파이프라인 통합 가동 (엔드투엔드 시각화 완결본)
# =====================================================================
if __name__ == "__main__":
    print("--- 🚀 하네스 그랜드 마스터 관제탑 시각화 완결 파이프라인 가동 ---")
    target_ticker = "AAPL"
    obsidian_trading_path = "./Obsidian_Trading" 
    
    # 1. 장기 기억 인출
    past_memory = search_obsidian_memory(target_ticker, obsidian_trading_path)
    
    # 2. 실시간 퀀트 데이터 수집
    market_data = fetch_stock_data_with_ta(target_ticker)
    
    # 3. AI 융합 추론 (Mock)
    mock_ai_opinion = ask_brain_with_rag(market_data, past_memory, target_ticker)
    
    # 4. 옵시디언 영구 저장 (Image 0 & 1의 로직을 그대로 사용)
    stored_opinion = save_trading_journal(target_ticker, market_data, past_memory, mock_ai_opinion, obsidian_trading_path)
    
    # 5. 디스코드 관제탑 즉각 보고 (⚠️ 최종 융합 및 시각적 완결)
    # 이제 이 함수 한 줄로 회원님은 디스코드 관제탑에서 시각적으로 완벽한 보고를 받게 됩니다.
    # [주인님이 가진 이미지 주소로 TRADING_ICON_URL과 NOC_ICON_URL을 교체하세요!]
    send_discord_alert(target_ticker, stored_opinion, bot_name="M9 퀀트 트레이더", avatar_url=TRADING_ICON_URL)
    
    # (선택 사항) 만약 인프라 장애라면, NOC용 아이콘으로 다음과 같이 호출하게 됩니다.
    # send_discord_alert("K3s-Cluster", "OOMKilled 에러 발생!", bot_name="NOC 엔지니어", avatar_url=NOC_ICON_URL)