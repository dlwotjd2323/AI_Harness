import os
import asyncio
import requests
from dotenv import load_dotenv

load_dotenv()
LLM_URL = os.getenv("LLM_API_URL")
semaphore = asyncio.Semaphore(3)

def call_local_llm_sync(agent_name, market_context):
    url = f"{LLM_URL}/chat/completions"
    system_prompt = (
        f"당신은 투자 위원회의 '{agent_name}'입니다.\n"
        f"아래 시장 데이터를 바탕으로 '매수', '매도', '관망' 중 하나를 선택하세요.\n"
        f"반드시 이유를 포함하여 20자 이내의 단답형 1문장으로만 보고하세요.\n"
        f"조건: 100% 한국어로만 작성할 것. (한자 및 영어 사용 절대 금지)\n\n"
        f"{market_context}"
    )
    payload = {"messages": [{"role": "system", "content": system_prompt}], "temperature": 0.7, "max_tokens": 60}
    
    try:
        response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload)
        return f"{agent_name}: {response.json()['choices'][0]['message']['content'].strip()}"
    except:
        return f"❌ {agent_name}: 통신 오류"

def call_chief_judge_sync(report_text):
    url = f"{LLM_URL}/chat/completions"
    system_prompt = (
        "당신은 투자 위원회의 '수석 결재자'입니다. "
        "제공된 시장 데이터와 10명 위원들의 의견을 종합하여, "
        "최종적으로 '[매수]', '[매도]', '[관망]' 중 단 하나만 결정하세요. "
        "조건 1: 반드시 30자 이내로 결정 사유를 1문장으로 요약하세요.\n"
        "조건 2: 100% 한국어로만 작성하세요. (한자 및 영어 사용 절대 금지)"
    )
    payload = {"messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": report_text}], "temperature": 0.3, "max_tokens": 80}
    
    try:
        response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload)
        return response.json()['choices'][0]['message']['content'].strip()
    except:
        return "❌ 통신 오류로 결재 보류"

async def llm_agent_task(agent_name, market_context):
    async with semaphore:
        return await asyncio.to_thread(call_local_llm_sync, agent_name, market_context)