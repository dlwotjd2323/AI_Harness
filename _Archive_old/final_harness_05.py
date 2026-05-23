import os
import datetime
import discord
from dotenv import load_dotenv
from discord.ext import commands
from crewai import Agent, Task, Crew, LLM

# 🌟 [수정됨] LangChain 포장지 대신, CrewAI 순정 포장지를 가져옵니다!
from crewai.tools import tool 
from langchain_community.tools import DuckDuckGoSearchRun 

# 🚨 중요: 백그라운드에서 .env 파일을 몰래 읽어오는 스위치 켜기
load_dotenv()

# ==========================================
# 1. 환경 설정 (회원님 환경에 맞게 필수 수정!)
# ==========================================
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
LLM_URL = os.getenv("LLM_API_URL")
OBSIDIAN_VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH")

# ==========================================
# 2. 디스코드 & 도구 설정
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# 🌟 [수정됨] CrewAI 순정 방식: 파이썬 함수를 무기로 만들어버립니다.
ddg_search = DuckDuckGoSearchRun()

@tool("Internet_Search")
def internet_search_tool(query: str) -> str:
    """최신 뉴스, 트렌드, 현재 상황 등 실시간 정보가 필요할 때 반드시 이 도구를 사용하여 인터넷을 검색하세요."""
    return ddg_search.run(query)

# ==========================================
# 3. CrewAI 에이전트 실행 함수
# ==========================================
def run_crewai_task(topic_text):
    my_llm = LLM(
        model="openai/local-model",
        base_url=LLM_URL,
        api_key="lm-studio"
    )

    planner = Agent(
        role='유튜브 콘텐츠 기획자',
        goal='인터넷을 검색하여 최신 정보를 수집하고, 주어진 주제에 맞는 흥미로운 유튜브 쇼츠 대본 초안을 작성합니다.',
        backstory='당신은 트렌드를 잘 아는 유튜브 쇼츠 기획자입니다. 모르는 내용이나 최신 이슈는 반드시 검색 도구를 사용해 사실을 확인합니다.',
        verbose=True,
        allow_delegation=False,
        llm=my_llm,
        tools=[internet_search_tool] # 🌟 순정 무기 장착 완료
    )

    task1 = Task(
        description=f"다음 주제에 대한 30초짜리 유튜브 쇼츠 대본을 작성하세요: {topic_text}\n필요하다면 반드시 최신 인터넷 검색 결과를 반영하세요.",
        expected_output="나레이션과 화면 지시문이 포함된 30초 분량의 대본",
        agent=planner
    )

    company = Crew(agents=[planner], tasks=[task1], verbose=True)
    return company.kickoff()

# ==========================================
# 4. 디스코드 명령어 설정
# ==========================================
@bot.event
async def on_ready():
    print(f'✅ [시스템 가동] 디스코드 관제탑 봇({bot.user})이 로그인했습니다! (CrewAI 순정 검색 모듈 탑재)')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ 명령어 형식이 잘못되었습니다. 예시: `!작업 오늘 한국 날씨 유튜브 쇼츠 대본`")

@bot.command()
async def 핑(ctx):
    await ctx.send("🏓 퐁! 관제탑과 정상 통신 중입니다. (검색 기능 온라인)")

@bot.command()
async def 작업(ctx, *, 주제):
    await ctx.send(f"🤖 알겠습니다! '{주제}'에 대한 작업을 시작합니다.\n(인터넷 검색이 포함되어 평소보다 시간이 조금 더 걸릴 수 있습니다...)")
    
    try:
        result = run_crewai_task(주제)
        
        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"유튜브_대본_{now_str}.md"
        file_path = os.path.join(OBSIDIAN_VAULT_PATH, file_name)
        
        markdown_content = (
            f"# 유튜브 쇼츠 대본 기획\n"
            f"**주제:** {주제}\n"
            f"**작업 일시:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"## 🎯 결과물\n"
            f"{result}"
        )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
            
        short_result = str(result)[:1000] + "...\n\n(나머지 내용은 옵시디언에서 확인하세요!)"
        
        discord_msg = (
            f"✅ 작업 완료! 옵시디언에 `{file_name}` 로 저장되었습니다.\n\n"
            f"**[내용 요약]**\n"
            f"```\n{short_result}\n```"
        )
        await ctx.send(discord_msg)
        
    except Exception as e:
        await ctx.send(f"❌ 작업 중 에러가 발생했습니다: {e}")

bot.run(DISCORD_TOKEN)