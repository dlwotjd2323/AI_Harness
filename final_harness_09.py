import os
import discord
import asyncio
import requests
from datetime import datetime # 🌟 [추가됨] 파일 이름에 시간을 넣기 위한 모듈
from dotenv import load_dotenv
from discord.ext import commands

# ==========================================
# 1. 환경 설정 및 봇 기본 세팅
# ==========================================
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
LLM_URL = os.getenv("LLM_API_URL")

# 🌟 옵시디언 경로 가져오기 (.env에 없으면 현재 폴더 아래에 'Obsidian_Trading' 자동 생성)
OBSIDIAN_PATH = os.getenv("OBSIDIAN_VAULT_PATH", "./Obsidian_Trading")

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
# 2. AI 두뇌 이식 구역 (+ 한자 금지 프롬프트)
# ==========================================
def call_local_llm_sync(agent_name, market_context):
    url = f"{LLM_URL}/chat/completions"
    headers = {"Content-Type": "application/json"}
    
    # 🌟 [보안 패치]: 100% 한국어 사용 강제 및 20자 이내 강력 통제
    system_prompt = (
        f"당신은 투자 위원회의 '{agent_name}'입니다.\n"
        f"아래 시장 데이터를 바탕으로 '매수', '매도', '관망' 중 하나를 선택하세요.\n"
        f"반드시 이유를 포함하여 20자 이내의 단답형 1문장으로만 보고하세요.\n"
        f"조건: 100% 한국어로만 작성할 것. (한자 및 영어 사용 절대 금지)\n\n"
        f"{market_context}"
    )
    
    payload = {
        "messages": [{"role": "system", "content": system_prompt}],
        "temperature": 0.7,
        "max_tokens": 60
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status() 
        return f"{agent_name}: {response.json()['choices'][0]['message']['content'].strip()}"
    except Exception as e:
        return f"❌ {agent_name}: 통신 오류"

def call_chief_judge_sync(report_text):
    url = f"{LLM_URL}/chat/completions"
    headers = {"Content-Type": "application/json"}
    
    system_prompt = (
        "당신은 투자 위원회의 '수석 결재자'입니다. "
        "제공된 시장 데이터와 10명 위원들의 의견을 종합하여, "
        "최종적으로 '[매수]', '[매도]', '[관망]' 중 단 하나만 결정하세요. "
        "조건 1: 반드시 30자 이내로 결정 사유를 1문장으로 요약하세요.\n"
        "조건 2: 100% 한국어로만 작성하세요. (한자 및 영어 사용 절대 금지)"
    )
    
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": report_text}
        ],
        "temperature": 0.3,
        "max_tokens": 80
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status() 
        return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        return "❌ 통신 오류로 결재 보류"

async def llm_agent_task(agent_name, market_context):
    async with semaphore:
        return await asyncio.to_thread(call_local_llm_sync, agent_name, market_context)

# ==========================================
# 2.5. M10 옵시디언 자동 기록기
# ==========================================
def save_to_obsidian(content):
    """최종 보고서를 .md 파일로 옵시디언 폴더에 저장합니다."""
    # 폴더가 없으면 생성
    if not os.path.exists(OBSIDIAN_PATH):
        os.makedirs(OBSIDIAN_PATH, exist_ok=True)
    
    # 파일명: 2026-05-19_14시30분_위원회보고서.md
    now_str = datetime.now().strftime("%Y-%m-%d_%H시%M분")
    filename = f"{now_str}_위원회보고서.md"
    filepath = os.path.join(OBSIDIAN_PATH, filename)
    
    # 파일 쓰기 (UTF-8 인코딩)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    return filepath

# ==========================================
# 3. 디스코드 명령어 처리 구역
# ==========================================
@bot.event
async def on_ready():
    print(f"✅ [시스템 가동] {bot.user} 관제탑 로그인 완료!")

@bot.command(name="투표")
async def vote(ctx):
    await ctx.send("🚨 **[투자 위원회 소집]** 실시간 데이터를 분석 중입니다. 잠시만 기다려 주십시오...")
    
    market_context = get_upbit_btc_data()
    
    agents = [
        "추세 추종자", "안전주의 퀀트", "역발상가", "뉴스 분석가", "기관 수급 추적자", 
        "패턴 인식기", "거시경제 전문가", "리스크 관리자", "단기 스캘퍼", "장기 가치투자자"
    ]
    tasks = [llm_agent_task(name, market_context) for name in agents]
    results = await asyncio.gather(*tasks)
    
    mid_report = f"{market_context}\n=====================================\n"
    for res in results:
        mid_report += f"{res}\n"
    
    print("👨‍⚖️ 수석 결재자가 최종 결정을 내리는 중입니다...")
    chief_decision = await asyncio.to_thread(call_chief_judge_sync, mid_report)
    
    final_report = f"{mid_report}=====================================\n👨‍⚖️ 수석 결재: {chief_decision}"
    
    # 🌟 M10: 결과물을 옵시디언으로 자동 저장
    saved_path = await asyncio.to_thread(save_to_obsidian, final_report)
    
    # 디스코드로 최종 출력 (저장 완료 알림 포함)
    await ctx.send(f"```text\n{final_report}\n```\n💾 **[옵시디언 자동 기록 완료]** `{saved_path}`에 저장되었습니다.")

bot.run(DISCORD_TOKEN)