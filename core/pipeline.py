import os
import discord
import asyncio
import m9_data
import m9_ai
import m10_logger
import m3_order

# 🌟 live_trade=False가 기본값입니다. 스위치가 켜져야만 실제 매매가 나갑니다.
async def run_analysis_pipeline(channel, tickers, live_trade=False):
    for ticker in tickers:
        coin_name = ticker.split('-')[1]
        
        # 🌟 모드에 따라 안내 메시지가 확연히 다르게 출력됩니다.
        mode_text = "🚨 [실전 매매]" if live_trade else "🧪 [시뮬레이션/분석 전용]"
        await channel.send(f"🔄 **[{coin_name}]** 계좌 연동 및 {mode_text} 파이프라인 가동 중...")
        
        market_context, chart_filepath = await asyncio.to_thread(m9_data.get_upbit_data, ticker)
        account_report, krw_balance = await asyncio.to_thread(m3_order.get_my_account)
        full_market_context = f"{account_report}\n{market_context}"
        
        agents = ["추세 추종자", "안전주의 퀀트", "역발상가", "뉴스 분석가", "기관 수급 추적자", "패턴 인식기", "밸류체인 분석가", "리스크 관리자", "단기 스캘퍼", "장기 가치투자자"]
        tasks = [m9_ai.llm_agent_task(name, full_market_context) for name in agents]
        results = await asyncio.gather(*tasks)

        mid_report = f"{full_market_context}\n=====================================\n"
        for res in results:
            mid_report += f"{res}\n"

        chief_decision = await asyncio.to_thread(m9_ai.call_chief_judge_sync, mid_report)
        
        # 🌟 live_trade 스위치가 True일 때만 진짜 매매(execute_trade)를 격발합니다.
        if live_trade:
            trade_result = await asyncio.to_thread(m3_order.execute_trade, ticker, chief_decision)
        else:
            trade_result = "⚠️ [안전 통제] 시뮬레이션 모드 작동 중. (실제 주문은 생략되었습니다)"
        
        final_report = f"{mid_report}=====================================\n👨‍⚖️ [{coin_name}] 수석 결재: {chief_decision}\n⚙️ {trade_result}"

        saved_path = await asyncio.to_thread(m10_logger.save_to_obsidian, final_report, ticker)
        
        if chart_filepath and os.path.exists(chart_filepath):
            discord_file = discord.File(chart_filepath)
            await channel.send(f"```text\n{final_report}\n```\n💾 **[옵시디언 기록 완료]** `{saved_path}`", file=discord_file)
        else:
            await channel.send(f"```text\n{final_report}\n```\n💾 **[옵시디언 기록 완료]** `{saved_path}`")
            
        await asyncio.sleep(3)