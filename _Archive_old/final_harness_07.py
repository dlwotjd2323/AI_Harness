import os
import discord
import asyncio
import requests
from dotenv import load_dotenv
from discord.ext import commands

# ==========================================
# 1. 환경 설정 및 봇 기본 세팅
# ==========================================
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
LLM_URL = os.getenv("LLM_API_URL")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
semaphore = asyncio.Semaphore(3)

# ==========================================
# 1.5. 실시간 시장 데이터 수집기 (M9-4)
# ==========================================
def get_upbit_btc_data():
    """업비트 퍼블릭 API를 통해 비트코인(KRW-BTC) 시세 데이터를 가져옵니다."""
    url = "https://api.upbit.com/v1/ticker?markets=KRW-BTC"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()[0]
        
        current_price = data['trade_price']
        high_price = data['high_price']
        low_price = data['low_price']
        volume = data['acc_trade_volume_24h']
        
        market_context = (
            f"📈 [현재 시장 데이터 브리핑]\n"
            f"- 현재가: {current_price:,} KRW\n"
            f"- 24h 최고가: {high_price:,} KRW\n"
            f"- 24h 최저가: {low_price:,} KRW\n"
            f"- 24h 거래량: {volume:,.2f} BTC"
        )
        return market_context
    except Exception as e:
        return f"⚠️ 시세 데이터 수집 실패: {e}"

# ==========================================
# 2. AI 두뇌 이식 구역 (데이터 주입형 프롬프트)
# ==========================================
def call_local_llm_sync(agent_name, market_context):
    """LM Studio에 데이터와 함께 분석을 요청합니다."""
    url = f"{LLM_URL}/chat/completions"
    headers = {"Content-Type": "application/json"}
    
    # 🌟 [핵심 변경]: 에이전트에게 업비트 실시간 가격 데이터를 팩트로 던져줍니다!
    system_prompt = (
        f"당신은 가상화폐 투자 위원회의 '{agent_name}'입니다.\n"
        f"아래 제공된 [현재 시장 데이터 브리핑]을 바탕으로 현재 시장을 분석하고, '매수', '매도', '관망' 중 하나를 선택하세요.\n"
        f"반드시 데이터에 기반한 이유를 포함하여 20자 이내의 단답형 1문장으로만 보고하세요.\n\n"
        f"{market_context}"
    )
    
    payload = {
        "messages": [{"role": "system", "content": system_prompt}],
        "temperature": 0.7,
        "max_tokens": 50
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status() 
        return f"{agent_name}: {response.json()['choices'][0]['message']['content'].strip()}"
    except Exception as e:
        return f"❌ {agent_name}: 통신 오류"

async def llm_agent_task(agent_name, market_context):
    """비동기 병목 방지용 래퍼 (데이터 전달 추가)"""
    async with semaphore:
        print(f"⏳ [{agent_name}] 분석 시작 (LM Studio 연산 중...)")
        result = await asyncio.to_thread(call_local_llm_sync, agent_name, market_context)
        return result

# ==========================================
# 3. 디스코드 명령어 처리 구역
# ==========================================
@bot.event
async def on_ready():
    print(f"✅ [시스템 가동] {bot.user} 관제탑 로그인 완료! 명령을 대기합니다.")

@bot.command(name="투표")
async def vote(ctx):
    await ctx.send("🚨 **[투자 위원회 소집]** 실시간 업비트 데이터를 수집하여 분석을 시작합니다...")
    
    # 1. 실시간 데이터 긁어오기
    market_context = get_upbit_btc_data()
    
    agents = [
        "추세 추종자", "안전주의 퀀트", "역발상가", "뉴스 분석가", "기관 수급 추적자", 
        "패턴 인식기", "거시경제 전문가", "리스크 관리자", "단기 스캘퍼", "장기 가치투자자"
    ]
    
    # 2. 에이전트들에게 데이터 쥐여주고 파견하기
    tasks = [llm_agent_task(name, market_context) for name in agents]
    results = await asyncio.gather(*tasks)
    
    # 3. 최종 보고서 작성 (상단에 실시간 브리핑 포함)
    report = f"{market_context}\n"
    report += "=====================================\n📊 [위원 상세 의견 최종 집계]\n"
    for res in results:
        report += f"{res}\n"
    report += "=====================================\n👨‍⚖️ 수석 결재: 대기 중"
    
    await ctx.send(f"```text\n{report}\n```")

# 봇 실행
bot.run(DISCORD_TOKEN)