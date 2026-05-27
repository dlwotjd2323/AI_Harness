import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone
from config.settings import TARGET_CHANNEL_ID 

# 🌟 [수정 포인트 1] 방금 core 폴더에 만든 '파이프라인 엔진'을 불러옵니다.
from core.pipeline import run_analysis_pipeline 

class TaskCron(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone=timezone('Asia/Seoul'))
        self.setup_schedule()

    def setup_schedule(self):
        self.scheduler.add_job(
            self.run_scheduled_task,
            CronTrigger(hour="9,18,21", minute=0, second=0), 
            misfire_gracetime=60,
            coalesce=True
        )
        self.scheduler.start()
        print("⏰ [스케줄러 톱니바퀴] 무인 자동 관제 크론 작업 장착 완료!")
        self.scheduler.print_jobs()

    async def run_scheduled_task(self):
        print("✅ [스케줄러 작동] 정각입니다! 스노우볼 파이프라인을 가동합니다.")
        channel = self.bot.get_channel(TARGET_CHANNEL_ID)
        if channel:
            # 🌟 [수정 포인트 2] 이전의 단순 텍스트 출력(TODO) 대신, 실제 파이프라인 엔진에 시동을 겁니다.
            # (과부하 방지를 위해 안전하게 BTC 단일 종목만 분석하도록 고정했습니다)
            await run_analysis_pipeline(channel, ["KRW-BTC"], live_trade=True)

async def setup(bot):
    await bot.add_cog(TaskCron(bot))