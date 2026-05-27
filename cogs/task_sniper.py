import discord
from discord.ext import commands, tasks
import asyncio

# 이전에 만든 레이더(get_current_yield)와 매매 엔진(execute_trade)을 가져옵니다.
import m3_order
from config.settings import TARGET_CHANNEL_ID

TARGET_YIELD = 1.50  # 🎯 목표 순수익률 (잔치국수 타점)

class TaskSniper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sniper_loop.start() # 봇이 켜지면 스나이퍼 루프도 즉시 가동 시작

    def cog_unload(self):
        self.sniper_loop.cancel()

    # ⏱️ 60초마다 무한 반복하며 잔고를 감시합니다. (서버 부하 거의 0)
    @tasks.loop(seconds=60)
    async def sniper_loop(self):
        try:
            # 1. 레이더 가동: 현재 수익률 확인
            current_yield, balance = await asyncio.to_thread(m3_order.get_current_yield, "KRW-BTC")
            
            # 코인을 보유하고 있지 않다면(0개), 살포시 다음 60초를 기다립니다.
            if balance == 0:
                return

            # 2. 목표 수익률 도달 확인 및 격발
            if current_yield >= TARGET_YIELD:
                # 방아쇠 격발 (AI 판단 없이 무조건 전량 매도)
                trade_result = await asyncio.to_thread(m3_order.execute_trade, "KRW-BTC", "[매도]")
                
                # 3. 디스코드 스텔스 보고 (요란한 차트 없이 깔끔하게 텍스트만)
                channel = self.bot.get_channel(TARGET_CHANNEL_ID)
                if channel:
                    await channel.send(
                        f"🍜 **[잔치국수 스나이퍼 익절]** 조용히 한 그릇 비웠습니다! (순수익: `+{current_yield}%`)\n"
                        f"└ ⚙️ {trade_result}"
                    )
                    
        except Exception as e:
            print(f"⚠️ [스나이퍼 루프 에러] 통신 지연 무시: {e}")

    # 루프가 시작되기 전 봇이 완전히 로그인할 때까지 대기하는 안전장치
    @sniper_loop.before_loop
    async def before_sniper(self):
        await self.bot.wait_until_ready()
        print(f"🔫 [잔치국수 스나이퍼] 상시 감시망(60초 주기, 타겟 +{TARGET_YIELD}%) 장착 완료!")

async def setup(bot):
    await bot.add_cog(TaskSniper(bot))