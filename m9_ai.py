import os
import asyncio
import requests
import chromadb
from dotenv import load_dotenv

load_dotenv()
LLM_URL = os.getenv("LLM_API_URL")
CHROMA_PATH = os.getenv("CHROMA_DB_PATH", "./Chroma_DB")

chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
memory_collection = chroma_client.get_or_create_collection(name="investment_memory")

semaphore = asyncio.Semaphore(3)

# 🌟 [추가됨] 10명 위원들의 고유 페르소나 및 판단 기준 (프롬프트 세분화)
AGENT_PROMPTS = {
    "추세 추종자": "추세의 방향성을 맹신합니다. 시장 데이터의 '현재가'가 24시간 최고가에 가까우면 상승장으로 보고 매수, 최저가에 가까우면 하락장으로 보아 매도/관망을 지시하세요.",
    "안전주의 퀀트": "통계적 변동성을 극도로 경계합니다. 변동폭(최고가-최저가 차이)이 크거나 방향을 알 수 없을 때는 무조건 '관망'을 선택하여 자본을 지키세요.",
    "역발상가": "대중의 광기를 역이용합니다. 제공된 데이터의 'RSI'가 70 이상이면 과매수로 판단해 '매도', 30 이하이면 과매도로 보아 '매수'를 지시하세요.",
    "뉴스 분석가": "현재 시장의 거래량(Volume) 변동을 뉴스의 결과물로 해석합니다. 거래량이 평소보다 폭증했다면 매수/매도 방향을 강하게 잡고, 거래량이 저조하면 관망하세요.",
    "기관 수급 추적자": "고래(기관)들의 자금 흐름을 추적합니다. 가격이 떨어지는데도 거래량이 터졌다면 기관의 매집으로 간주하고 '매수'를 외치세요.",
    "패턴 인식기": "기술적 지표의 조합을 봅니다. RSI 수치와 24시간 가격 변동률을 조합하여 기계적인 단기 패턴을 찾아내 단답형으로 보고하세요.",
    "밸류체인 분석가": "가상자산 생태계의 인프라 점유율을 분석합니다. 비트코인, 이더리움, 솔라나 등 각 메인넷이 가진 본질적 가치와 펀더멘탈을 기반으로 가장 보수적으로 평가하세요.",
    "리스크 관리자": "수익보다 손실 방어가 최우선입니다. 시장이 조금이라도 과열(RSI 60 이상)되었거나 최저가 대비 많이 올랐다면 무조건 매도를 외치세요.",
    "단기 스캘퍼": "오직 현재가와 24h 변동성만 보고 치고 빠지는 초단기 타점을 잡습니다. RSI가 40~60 사이의 횡보장이면 적극적으로 틈새 매수를 노리세요.",
    "장기 가치투자자": "단기적 가격 등락이나 RSI 수치를 철저히 무시합니다. 오직 해당 코인의 장기적 우상향 가치만 믿고 무조건 '매수' 또는 '관망'만 지시하세요 (매도 금지)."
}

def call_local_llm_sync(agent_name, market_context):
    url = f"{LLM_URL}/chat/completions"
    
    # 🌟 [추가됨] 에이전트 이름에 맞는 전용 지시사항 추출
    specific_instruction = AGENT_PROMPTS.get(agent_name, "당신은 가상화폐 투자 위원회의 전문 위원입니다.")
    
    system_prompt = (
        f"당신은 투자 위원회의 '{agent_name}'입니다.\n"
        f"당신의 행동 강령: {specific_instruction}\n\n"
        f"아래 시장 데이터를 바탕으로 오직 '매수', '매도', '관망' 중 하나를 선택하세요.\n"
        f"반드시 당신의 행동 강령에 의거한 이유를 포함하여 20자 이내의 단답형 1문장으로만 보고하세요.\n"
        f"조건: 100% 한국어로만 작성할 것. (한자 및 영어 사용 금지)\n\n"
        f"{market_context}"
    )
    payload = {"messages": [{"role": "system", "content": system_prompt}], "temperature": 0.7, "max_tokens": 70}
    
    try:
        response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload)
        return f"{agent_name}: {response.json()['choices'][0]['message']['content'].strip()}"
    except:
        return f"❌ {agent_name}: 통신 오류"

def call_chief_judge_sync(report_text):
    past_memory = "아직 참조할 만한 과거 기억이 충분하지 않습니다."
    try:
        results = memory_collection.query(query_texts=[report_text], n_results=1)
        if results['documents'] and results['documents'][0]:
            extracted_memory = results['documents'][0][0]
            past_memory = extracted_memory[-300:] 
            print(f"\n=====================================")
            print(f"📖 [기억 인출 확인] 수석 결재자가 다음 과거 기록을 참조 중입니다:")
            print(f"{past_memory}")
            print(f"=====================================\n")
    except Exception as e:
        pass

    url = f"{LLM_URL}/chat/completions"
    system_prompt = (
        "당신은 투자 위원회의 '수석 결재자'입니다.\n"
        "제공된 실시간 데이터와 각기 다른 성향을 가진 10명 위원들의 의견, 그리고 아래의 [과거 기억]을 모두 종합하여 "
        "최종적으로 '[매수]', '[매도]', '[관망]' 중 단 하나만 결정하세요.\n"
        "조건 1: 반드시 30자 이내로 결정 사유를 1문장으로 요약하세요.\n"
        "조건 2: 100% 한국어로만 작성하세요.\n\n"
        f"🧠 [과거 유사 상황에서의 위원회 기억]:\n...{past_memory}\n\n"
        "위 과거의 판단과 결과를 반면교사 삼아 오늘의 가장 현명한 최종 판결을 내리십시오."
    )
    
    payload = {"messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": report_text}], "temperature": 0.3, "max_tokens": 100}
    
    try:
        response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload)
        return response.json()['choices'][0]['message']['content'].strip()
    except:
        return "❌ 통신 오류로 결재 보류"

async def llm_agent_task(agent_name, market_context):
    async with semaphore:
        return await asyncio.to_thread(call_local_llm_sync, agent_name, market_context)