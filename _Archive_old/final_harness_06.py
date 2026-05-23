import os
import discord
import asyncio
import requests # 🌟 [추가됨] AI 서버와 통신하기 위한 도구
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

# 트래픽 제어: 한 번에 3명씩만 AI 연산 (컴퓨터 과부하 방지)
semaphore = asyncio.Semaphore(3)


# ==========================================
# 1.5. 실시간 시장 데이터 수집기 (M9-4)
# ==========================================
def get_upbit_btc_data():
    """업비트 퍼블릭 API를 통해 비트코인(KRW-BTC) 24시간 시세 데이터를 가져옵니다."""
    url = "https://api.upbit.com/v1/ticker?markets=KRW-BTC"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()[0]
        
        # 보기 좋게 숫자 포맷팅 (콤마 추가)
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
# 2. AI 두뇌 이식 구역 (LM Studio API 연동)
# ==========================================
def call_local_llm_sync(agent_name):
    """LM Studio에 실제 분석을 요청하는 코어 로직"""
    url = f"{LLM_URL}/chat/completions"
    headers = {"Content-Type": "application/json"}
    
    # 🌟 페르소나(다중 인격) 부여 프롬프트
    system_prompt = (
        f"당신은 가상화폐 투자 위원회의 '{agent_name}'입니다. "
        f"자신의 성향에 맞춰 현재 시장을 분석하고, '매수', '매도', '관망' 중 하나를 선택하세요. "
        f"반드시 이유를 포함하여 20자 이내의 단답형 1문장으로만 보고하세요. "
        f"예시 형식: [매수] MA20 돌파 모멘텀이 확인되었습니다."
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
        return f"❌ {agent_name}: 통신 오류 (LM Studio 서버 켜져 있는지 확인)"

async def llm_agent_task(agent_name):
    """비동기 병목 방지용 래퍼"""
    async with semaphore:
        print(f"⏳ [{agent_name}] 분석 시작 (LM Studio 연산 중...)")
        # 동기 통신을 비동기 스레드로 안전하게 우회 처리
        result = await asyncio.to_thread(call_local_llm_sync, agent_name)
        return result

# ==========================================
# 3. 디스코드 명령어 처리 구역
# ==========================================
@bot.event
async def on_ready():
    print(f"✅ [시스템 가동] {bot.user} 관제탑 로그인 완료! 명령을 대기합니다.")

@bot.command(name="투표")
async def vote(ctx):
    await ctx.send("🚨 **[투자 위원회 소집]** 10명의 위원이 분석을 시작합니다. (최대 3명 동시 연산)")
    
    agents = [
        "추세 추종자", "안전주의 퀀트", "역발상가", "뉴스 분석가", "기관 수급 추적자", 
        "패턴 인식기", "거시경제 전문가", "리스크 관리자", "단기 스캘퍼", "장기 가치투자자"
    ]
    
    # 🌟 [수정됨] 가짜 함수 대신, 진짜 AI 호출 함수(llm_agent_task)를 사용합니다.
    tasks = [llm_agent_task(name) for name in agents]
    results = await asyncio.gather(*tasks)
    
    # 🌟 [수정됨] 디스코드에서 보기 좋게 출력되도록 텍스트 포맷을 개선했습니다.
    report = "📊 [위원 상세 의견 최종 집계]\n=====================================\n"
    for res in results:
        report += f"{res}\n"
    report += "=====================================\n👨‍⚖️ 수석 결재: 대기 중"
    
    # 디스코드 코드 블록(```text)으로 감싸서 깔끔한 표 형태로 전송
    await ctx.send(f"```text\n{report}\n```")

# 봇 실행
bot.run(DISCORD_TOKEN)