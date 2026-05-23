import asyncio
import re

# 1. 페르소나 정의 (10명 세팅 예정)
COMMITTEE_PERSONAS = {
    "추세 추종자": "MA20 돌파 중시. [매수], [매도], [관망] 필수.",
    "안전주의 퀀트": "RSI 70 이상 보수적 접근. [매수], [매도], [관망] 필수.",
    "역발상가": "남들과 반대로 진입. [매수], [매도], [관망] 필수."
}

# 🚦 안전장치 1: Semaphore (동시 접속자 수 제한)
# 최대 3명의 AI만 동시에 GPU 자원을 사용하도록 통제
MAX_CONCURRENT_TASKS = 3
semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

async def ask_agent(name, persona, chart_data):
    # 신호등 대기: 자리가 날 때까지(3명 미만일 때까지) 기다림
    async with semaphore:
        print(f"  ⏳ [{name}] 분석 시작 (GPU 자원 할당됨)")
        try:
            # ⏱️ 안전장치 2: Timeout (무한 로딩 방지)
            # 30초 안에 분석을 못 끝내면 강제로 끊어버림
            async def mock_llm_call():
                await asyncio.sleep(2) # LLM 연산 시간 2초 시뮬레이션
                return f"[{'매수' if name == '추세 추종자' else '관망'}] 지표 분석 완료."

            mock_response = await asyncio.wait_for(mock_llm_call(), timeout=30.0)
            return name, mock_response
            
        except asyncio.TimeoutError:
            print(f"  ⚠️ [{name}] 응답 시간 초과! (기권 처리)")
            return name, "[관망] (Time-out 기권)"
        except Exception as e:
            print(f"  ❌ [{name}] 분석 중 에러 발생: {e}")
            return name, "[관망] (시스템 에러)"

async def run_investment_committee(chart_data):
    print("📢 [투자 위원회 소집] 10명의 위원이 분석을 시작합니다. (최대 3명 동시 연산)\n")
    
    # 작업 지시서(Tasks) 일괄 생성
    tasks = [ask_agent(name, persona, chart_data) for name, persona in COMMITTEE_PERSONAS.items()]
    
    # 10개를 한 번에 던지지만, Semaphore가 알아서 3개씩 끊어서 처리함
    results = await asyncio.gather(*tasks)
    
    votes = {"매수": 0, "매도": 0, "관망": 0}
    
    print("\n📊 [각 위원 분석 결과]")
    for name, response in results:
        match = re.search(r'\[(매수|매도|관망)\]', response)
        decision = match.group(1) if match else "관망"
        votes[decision] += 1
        print(f"- **{name}**: {decision}")
        
    buy_ratio = (votes['매수'] / len(COMMITTEE_PERSONAS)) * 100
    print(f"\n✅ [최종 집계] 매수: {votes['매수']}표, 매도: {votes['매도']}표, 관망: {votes['관망']}표")
    print(f"👨‍⚖️ 수석 결재: {'승인 (매수 진행)' if buy_ratio >= 70 else '반려 (관망 유지)'}")

# 실행부
if __name__ == "__main__":
    test_data = "AAPL 현재가 180, RSI 65"
    asyncio.run(run_investment_committee(test_data))