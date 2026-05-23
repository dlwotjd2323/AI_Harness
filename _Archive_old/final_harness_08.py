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
    url = "https://api.upbit.com/v1/ticker?markets=KRW-BTC"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()[0]
        
        market_context = (
            f"📈 [현재 시장 데이터 브리핑]\n"
            f"- 현재가: {data['trade_price']:,} KRW\n"
            f"- 24h 최고가: {data['high_price']:,} KRW\n"
            f"- 24h 최저가: {data['low_price']:,} KRW\n"
            f"- 24h 거래량: {data['acc_trade_volume_24h']:,.2f} BTC"
        )
        return market_context
    except Exception as e:
        return f"⚠️ 시세 데이터 수집 실패: {e}"

# ==========================================
# 2. AI 두뇌 이식 구역 (10인 위원 + 수석 결재자)
# ==========================================
def call_local_llm_sync(agent_name, market_context):
    """10인의 일반 위원 호출"""
    url = f"{LLM_URL}/chat/completions"
    headers = {"Content-Type": "application/json"}
    system_prompt = (
        f"당신은 가상화폐 투자 위원회의 '{agent_name}'입니다.\n"
        f"아래 시장 데이터를 바탕으로 분석하고, '매수', '매도', '관망' 중 하나를 선택하세요.\n"
        f"반드시 이유를 포함하여 20자 이내의 단답형 1문장으로 보고하세요.\n\n"
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

def call_chief_judge_sync(report_text):
    """🌟 11번째 AI: 수석 결재자 호출 로직 추가"""
    url = f"{LLM_URL}/chat/completions"
    headers = {"Content-Type": "application/json"}
    
    # 10명의 의견과 시장 상황을 모두 읽고 판단하는 결재자 프롬프트
    system_prompt = (
        "당신은 투자 위원회의 '수석 결재자(Chief Judge)'입니다. "
        "제공된 시장 데이터와 10명 위원들의 의견을 종합하여, "
        "최종적으로 '[매수]', '[매도]', '[관망]' 중 단 하나만 결정하세요. "
        "반드시 30자 이내로 결정 사유를 1문장으로 요약하여 보고하세요."
        "반드시 100% 한국어로만 작성할 것. (한자 및 영어 사용 절대 금지)"
    )
    
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": report_text} # 앞서 취합된 텍스트 전체를 던져줍니다.
        ],
        "temperature": 0.3, # 결재자는 냉철해야 하므로 창의성(온도)을 낮춤
        "max_tokens": 60
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status() 
        return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        return "❌ 통신 오류로 결재 보류"

async def llm_agent_task(agent_name, market_context):
    async with semaphore:
        print(f"⏳ [{agent_name}] 분석 시작...")
        return await asyncio.to_thread(call_local_llm_sync, agent_name, market_context)

# ==========================================
# 3. 디스코드 명령어 처리 구역
# ==========================================
@bot.event
async def on_ready():
    print(f"✅ [시스템 가동] {bot.user} 관제탑 로그인 완료!")

@bot.command(name="투표")
async def vote(ctx):
    await ctx.send("🚨 **[투자 위원회 소집]** 실시간 데이터를 분석 중입니다. 잠시만 기다려 주십시오...")
    
    # 1. 실시간 데이터 수집
    market_context = get_upbit_btc_data()
    
    # 2. 10인 위원 파견
    agents = [
        "추세 추종자", "안전주의 퀀트", "역발상가", "뉴스 분석가", "기관 수급 추적자", 
        "패턴 인식기", "거시경제 전문가", "리스크 관리자", "단기 스캘퍼", "장기 가치투자자"
    ]
    tasks = [llm_agent_task(name, market_context) for name in agents]
    results = await asyncio.gather(*tasks)
    
    # 3. 수석 결재자에게 보낼 중간 보고서 텍스트 조립
    mid_report = f"{market_context}\n=====================================\n"
    for res in results:
        mid_report += f"{res}\n"
    
    # 4. 🌟 수석 결재자 최종 판결 요청 (10인 분석이 끝난 후 비동기 호출)
    print("👨‍⚖️ 수석 결재자가 의견을 종합하여 최종 결정을 내리는 중입니다...")
    chief_decision = await asyncio.to_thread(call_chief_judge_sync, mid_report)
    
    # 5. 최종 완성본 디스코드 발송
    final_report = f"{mid_report}=====================================\n👨‍⚖️ 수석 결재: {chief_decision}"
    await ctx.send(f"```text\n{final_report}\n```")

bot.run(DISCORD_TOKEN)