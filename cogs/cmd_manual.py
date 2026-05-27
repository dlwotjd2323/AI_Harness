import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
import psutil
import time
from core.pipeline import run_analysis_pipeline

# 🌟 하드코딩 제거: settings.py에서 환경 변수를 안전하게 수입해옵니다.
from config.settings import TARGET_CHANNEL_ID, DASHBOARD_CHANNEL_ID

class CommitteeView(View):
    def __init__(self):
        super().__init__(timeout=None) # 봇 재시작 시에도 버튼이 죽지 않도록 영구 설정

    @discord.ui.button(label="BTC 분석 (모의)", style=discord.ButtonStyle.primary, emoji="🧡", custom_id="btn_btc_dry")
    async def btc_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🧪 비트코인 모의 분석 가동... (결과는 보고서 채널로 발송됩니다)", ephemeral=True)
        report_channel = interaction.client.get_channel(TARGET_CHANNEL_ID)
        if report_channel:
            await run_analysis_pipeline(report_channel, ["KRW-BTC"], live_trade=False)

    @discord.ui.button(label="ETH 분석 (모의)", style=discord.ButtonStyle.success, emoji="💙", custom_id="btn_eth_dry")
    async def eth_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🧪 이더리움 모의 분석 가동... (결과는 보고서 채널로 발송됩니다)", ephemeral=True)
        report_channel = interaction.client.get_channel(TARGET_CHANNEL_ID)
        if report_channel:
            await run_analysis_pipeline(report_channel, ["KRW-ETH"], live_trade=False)

    @discord.ui.button(label="SOL 분석 (모의)", style=discord.ButtonStyle.secondary, emoji="💜", custom_id="btn_sol_dry")
    async def sol_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🧪 솔라나 모의 분석 가동... (결과는 보고서 채널로 발송됩니다)", ephemeral=True)
        report_channel = interaction.client.get_channel(TARGET_CHANNEL_ID)
        if report_channel:
            await run_analysis_pipeline(report_channel, ["KRW-SOL"], live_trade=False)

class CmdManual(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dashboard_msg = None
        self.start_time = time.time()
        self.dashboard_loop.start() # 봇이 켜지면 전광판 갱신 모터 즉시 가동

    def cog_unload(self):
        self.dashboard_loop.cancel()

    # ⏱️ 60초마다 서버 상태를 스캔하여 전광판의 숫자를 바꿉니다.
    @tasks.loop(seconds=60)
    async def dashboard_loop(self):
        # ⚠️ 만약 .env에 ID를 안 넣었다면 에러를 방지하고 조용히 멈춥니다.
        if DASHBOARD_CHANNEL_ID == 0:
            return
            
        channel = self.bot.get_channel(DASHBOARD_CHANNEL_ID)
        if not channel:
            return

        # 시스템 리소스 측정
        cpu_usage = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        ram_usage = ram.percent
        ping = round(self.bot.latency * 1000)
        
        # 봇 가동 시간 계산
        uptime_seconds = int(time.time() - self.start_time)
        uptime_str = f"{uptime_seconds // 3600}시간 {(uptime_seconds % 3600) // 60}분"

        # 전광판 UI 조립 (CPU가 80% 이상이면 경고색(빨강)으로 변경)
        embed_color = discord.Color.red() if cpu_usage > 80 else discord.Color.green()
        embed = discord.Embed(
            title="🖥️ 실시간 AI 투자 관제 센터 (NOC)",
            description="자동 매매(스케줄러/스나이퍼)는 백그라운드에서 정상 가동 중입니다.\n아래 버튼으로 안전하게 모의 분석을 트리거할 수 있습니다.",
            color=embed_color
        )
        embed.add_field(name="📡 봇 네트워크 핑", value=f"`{ping} ms`", inline=True)
        embed.add_field(name="🧠 CPU 점유율", value=f"`{cpu_usage}%`", inline=True)
        embed.add_field(name="💾 RAM 점유율", value=f"`{ram_usage}%`", inline=True)
        embed.add_field(name="⏱️ 연속 무중단 가동", value=f"`{uptime_str}`", inline=True)
        embed.add_field(name="🎯 보고서 타겟 채널", value=f"<#{TARGET_CHANNEL_ID}>", inline=False)

        # 1. 봇이 처음 켜졌거나 메시지가 지워졌을 때 새로 만듦
        if not self.dashboard_msg:
            try:
                await channel.purge(limit=10) # 예전 찌꺼기 메시지 삭제
                self.dashboard_msg = await channel.send(embed=embed, view=CommitteeView())
            except Exception as e:
                print(f"⚠️ 대시보드 갱신 실패 (권한 확인 필요): {e}")
        # 2. 이미 전광판이 있으면 메시지를 수정하여 덮어씀 (알림 스팸 방지)
        else:
            try:
                await self.dashboard_msg.edit(embed=embed, view=CommitteeView())
            except discord.NotFound:
                self.dashboard_msg = None # 누군가 지웠다면 다음 루프에서 재생성

    @dashboard_loop.before_loop
    async def before_dashboard(self):
        await self.bot.wait_until_ready()
        print("🖥️ [전광판 가동] 실시간 서버 상태 인디케이터 장착 완료!")

async def setup(bot):
    bot.add_view(CommitteeView()) # 버튼 영속성 부여
    await bot.add_cog(CmdManual(bot))