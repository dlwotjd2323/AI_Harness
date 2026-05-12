import discord
from discord.ext import commands

# 봇 기본 설정 (명령어 시작 기호는 '!'로 설정)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# 🚨 여기에 아까 복사한 디스코드 봇 토큰을 넣으세요!
DISCORD_TOKEN = "YOUR_TOKEN"

@bot.event
async def on_ready():
    print(f'✅ [시스템 가동] 디스코드 관제탑 봇({bot.user})이 로그인했습니다!')
    print("스마트폰 디스코드 앱에서 '!명령어 [주제]' 형식으로 지시를 내려보세요.")

# 테스트용 명령어: '!핑' 이라고 치면 '퐁!' 이라고 대답합니다.
@bot.command()
async def 핑(ctx):
    await ctx.send("🏓 퐁! 관제탑과 정상 통신 중입니다. (H8005 허브 경유)")

# 본격적인 작업 지시 명령어 (나중에 여기에 CrewAI 코드를 결합할 것입니다)
@bot.command()
async def 작업(ctx, *, 주제):
    await ctx.send(f"🤖 알겠습니다! '{주제}'에 대한 작업을 CrewAI 에이전트 팀에 하달합니다. (잠시만 기다려주세요...)")
    
    # [차후 추가] 여기에 기존의 CrewAI 실행 코드가 들어갑니다.
    # result = company.kickoff(inputs={'topic': 주제})
    
    # 작업이 끝나면 가상의 완료 메시지 전송
    await ctx.send(f"✅ '{주제}' 작업이 완료되어 옵시디언에 저장되었습니다!")

# 봇 실행 (스크립트를 켜두어야 봇이 살아있습니다)
bot.run(DISCORD_TOKEN)