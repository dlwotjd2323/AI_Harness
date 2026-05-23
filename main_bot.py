import os
import discord
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

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

    # 🌟 [추가됨] 감시할 코인 종목 리스트 
    tickers = ["KRW-BTC", "KRW-ETH", "KRW-SOL"]
    
    print(f"⏰ [정기 관제] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 자동 투자 위원회 가동 ({len(tickers)}개 종목)")
    await channel.send(f"🚀 **[다중 자산 관제 시작]** 설정된 {len(tickers)}개 종목의 순차 분석을 가동합니다.")

    # 🌟 [수정됨] 종목 리스트를 순회하는 For Loop 적용
    for ticker in tickers:
        coin_name = ticker.split('-')[1]
        await channel.send(f"🔄 **[{coin_name}]** 분석 파이프라인 가동 중...")
        
        # 1. 특정 종목 데이터/차트 수집
        market_context, chart_filepath = await asyncio.to_thread(m9_data.get_upbit_data, ticker)
        
        # 2. 위원회 및 수석 결재
        agents = ["추세 추종자", "안전주의 퀀트", "역발상가", "뉴스 분석가", "기관 수급 추적자", "패턴 인식기", "밸류체인 분석가", "리스크 관리자", "단기 스캘퍼", "장기 가치투자자"]
        tasks = [m9_ai.llm_agent_task(name, market_context) for name in agents]
        results = await asyncio.gather(*tasks)

        mid_report = f"{market_context}\n=====================================\n"
        for res in results:
            mid_report += f"{res}\n"

        chief_decision = await asyncio.to_thread(m9_ai.call_chief_judge_sync, mid_report)
        final_report = f"{mid_report}=====================================\n👨‍⚖️ [{coin_name}] 수석 결재: {chief_decision}"

        # 3. 옵시디언 및 기억망 기록 (종목명 전달)
        saved_path = await asyncio.to_thread(m10_logger.save_to_obsidian, final_report, ticker)
        
        # 4. 디스코드 전송
        if chart_filepath and os.path.exists(chart_filepath):
            discord_file = discord.File(chart_filepath)
            await channel.send(f"```text\n{final_report}\n```\n💾 **[옵시디언/기억망 자동 기록 완료]** `{saved_path}`", file=discord_file)
        else:
            await channel.send(f"```text\n{final_report}\n```\n💾 **[옵시디언/기억망 자동 기록 완료]** `{saved_path}`")
            
        # API Rate Limit 및 LLM 과부하 방지를 위한 5초 대기
        await asyncio.sleep(5)

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
    await ctx.send("🚨 **[수동 호출]** 전체 자산 실시간 데이터 분석 및 차트 생성을 시작합니다...")
    await run_automatic_committee()

bot.run(DISCORD_TOKEN)