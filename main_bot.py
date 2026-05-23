import os
import discord
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# 🌟 분할된 커스텀 모듈 부품 불러오기
import m9_data
import m9_ai
import m10_logger

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

async def run_automatic_committee():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("⚠️ 에러: 채널 ID를 찾을 수 없습니다.")
        return

    print(f"⏰ [정기 관제] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 자동 투자 위원회 가동")
    
    # 1. 데이터 수집 모듈 호출
    market_context = m9_data.get_upbit_btc_data()
    
    # 2. AI 통신 모듈 호출
    agents = ["추세 추종자", "안전주의 퀀트", "역발상가", "뉴스 분석가", "기관 수급 추적자", "패턴 인식기", "거시경제 전문가", "리스크 관리자", "단기 스캘퍼", "장기 가치투자자"]
    tasks = [m9_ai.llm_agent_task(name, market_context) for name in agents]
    results = await asyncio.gather(*tasks)

    mid_report = f"{market_context}\n=====================================\n"
    for res in results:
        mid_report += f"{res}\n"

    chief_decision = await asyncio.to_thread(m9_ai.call_chief_judge_sync, mid_report)
    final_report = f"{mid_report}=====================================\n👨‍⚖️ 수석 결재: {chief_decision}"

    # 3. 로거 모듈 호출
    saved_path = await asyncio.to_thread(m10_logger.save_to_obsidian, final_report)
    
    await channel.send(f"```text\n{final_report}\n```\n💾 **[옵시디언 자동 기록 완료]** `{saved_path}`")

@bot.event
async def on_ready():
    print(f"✅ [시스템 가동] {bot.user} 관제탑 로그인 완료!")
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_automatic_committee, CronTrigger(hour="9,21", minute=0))
    scheduler.start()
    print("⏰ [스케줄러 가동] 무인 자동 관제 크론 작업 등록 완료 (매일 09시, 21시)")

@bot.command(name="투표")
async def vote(ctx):
    global CHANNEL_ID
    CHANNEL_ID = ctx.channel.id
    await ctx.send("🚨 **[수동 호출]** 실시간 데이터를 분석 중입니다...")
    await run_automatic_committee()

bot.run(DISCORD_TOKEN)