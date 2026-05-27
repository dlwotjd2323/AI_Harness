import discord
from discord.ext import commands
from config.settings import DISCORD_TOKEN

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"✅ [시스템 가동] {bot.user} 초경량 관제탑(V2) 로그인 완료!")
    
    # 🌟 분리해 둔 톱니바퀴(Cogs) 부품들을 조립하여 전원을 넣습니다.
    await bot.load_extension("cogs.task_cron")
    await bot.load_extension("cogs.cmd_manual")
    await bot.load_extension("cogs.task_sniper")
    
    print("🔧 [모듈 장착 완료] 자동 스케줄러 및 수동 통제소 인프라 연동 완료.")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)