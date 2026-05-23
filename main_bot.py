import os
import discord
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from discord.ext import commands
from discord.ui import Button, View
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import m9_data
import m9_ai
import m10_logger
import m3_order # 🌟 [추가됨] 실전 자동 매매 모듈

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

class CommitteeView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="BTC 분석", style=discord.ButtonStyle.primary, emoji="🧡")
    async def btc_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🚀 비트코인 정밀 분석 및 매매 파이프라인 가동...", ephemeral=True)
        await run_manual_committee(interaction.channel, ["KRW-BTC"])

    @discord.ui.button(label="ETH 분석", style=discord.ButtonStyle.success, emoji="💙")
    async def eth_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🚀 이더리움 정밀 분석 및 매매 파이프라인 가동...", ephemeral=True)
        await run_manual_committee(interaction.channel, ["KRW-ETH"])

    @discord.ui.button(label="SOL 분석", style=discord.ButtonStyle.secondary, emoji="💜")
    async def sol_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🚀 솔라나 정밀 분석 및 매매 파이프라인 가동...", ephemeral=True)
        await run_manual_committee(interaction.channel, ["KRW-SOL"])

    @discord.ui.button(label="전체 종목 스캔", style=discord.ButtonStyle.danger, emoji="🔥")
    async def all_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🚨 전 종목 풀스캔 및 자동 매매 파이프라인 가동!", ephemeral=True)
        await run_manual_committee(interaction.channel, ["KRW-BTC", "KRW-ETH", "KRW-SOL"])

async def run_manual_committee(channel, tickers):
    for ticker in tickers:
        coin_name = ticker.split('-')[1]
        await channel.send(f"🔄 **[{coin_name}]** 분석 파이프라인 가동 중...")
        
        market_context, chart_filepath = await asyncio.to_thread(m9_data.get_upbit_data, ticker)
        
        agents = ["추세 추종자", "안전주의 퀀트", "역발상가", "뉴스 분석가", "기관 수급 추적자", "패턴 인식기", "밸류체인 분석가", "리스크 관리자", "단기 스캘퍼", "장기 가치투자자"]
        tasks = [m9_ai.llm_agent_task(name, market_context) for name in agents]
        results = await asyncio.gather(*tasks)

        mid_report = f"{market_context}\n=====================================\n"
        for res in results:
            mid_report += f"{res}\n"

        chief_decision = await asyncio.to_thread(m9_ai.call_chief_judge_sync, mid_report)
        
        # 🌟 [추가됨] 수석 결재자 결정에 따른 매수 로직 실행
        trade_result = await asyncio.to_thread(m3_order.execute_trade, ticker, chief_decision)
        
        # 🌟 [수정됨] 최종 보고서에 체결 내역 기록
        final_report = f"{mid_report}=====================================\n👨‍⚖️ [{coin_name}] 수석 결재: {chief_decision}\n⚙️ {trade_result}"

        saved_path = await asyncio.to_thread(m10_logger.save_to_obsidian, final_report, ticker)
        
        if chart_filepath and os.path.exists(chart_filepath):
            discord_file = discord.File(chart_filepath)
            await channel.send(f"```text\n{final_report}\n```\n💾 **[옵시디언/기억망 자동 기록 완료]** `{saved_path}`", file=discord_file)
        else:
            await channel.send(f"```text\n{final_report}\n```\n💾 **[옵시디언/기억망 자동 기록 완료]** `{saved_path}`")
            
        await asyncio.sleep(3)

async def run_automatic_committee():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await run_manual_committee(channel, ["KRW-BTC", "KRW-ETH", "KRW-SOL"])

@bot.event
async def on_ready():
    print(f"✅ [시스템 가동] {bot.user} 관제탑 로그인 완료!")
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_automatic_committee, CronTrigger(hour="9,21", minute=0))
    scheduler.start()
    print("⏰ [스케줄러 가동] 무인 자동 관제 크론 작업 등록 완료 (매일 09시, 21시)")

@bot.command(name="메뉴")
async def show_menu(ctx):
    embed = discord.Embed(
        title="🤖 AI 하네스 투자 관제 대시보드",
        description="분석을 원하는 종목의 버튼을 터치해 주세요.\n분석 결과는 옵시디언과 크리스탈(기억망)에 저장되며, 매수 판결 시 1만 원 자동 매수가 진행됩니다.",
        color=discord.Color.blue()
    )
    embed.add_field(name="상태", value="🟢 가동 중 (24/7 무인 관제)", inline=True)
    embed.add_field(name="종목", value="BTC, ETH, SOL", inline=True)
    await ctx.send(embed=embed, view=CommitteeView())

@bot.command(name="투표")
async def vote(ctx):
    await ctx.send("🚨 **[수동 호출]** 전체 자산 분석을 시작합니다...")
    await run_automatic_committee()

bot.run(DISCORD_TOKEN)