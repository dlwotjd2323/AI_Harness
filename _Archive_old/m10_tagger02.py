import os
from datetime import datetime

# =====================================================================
# ⚙️ [하네스 중앙 통제 스위치]
# 오늘 퇴근 후 집에 가서 LM Studio에 팩(모델)을 꽂으면 이걸 True로 바꿉니다!
# =====================================================================
IS_REAL_BRAIN_ON = False  
BRAIN_URL = "YOUR_TOKEN"

def ask_brain(prompt, system_prompt="너는 하네스의 두뇌야."):
    """스위치 상태에 따라 진짜 LLM을 부를지, 가짜(Mock) 응답을 줄지 결정하는 라우터"""
    if not IS_REAL_BRAIN_ON:
        # [모의 훈련 모드] 텍스트에 따라 지정된 가짜 응답을 뱉음
        print("💡 [Mock 모드] 가짜 두뇌가 작동합니다. (네트워크/VRAM 소모 없음)")
        if "키워드" in user_prompt:
            return "K3s, NOC장애, DevOps"
        elif "실수" in user_prompt or "해결책" in user_prompt:
            return "- 작업 전 LM Studio에 AI 모델(팩)이 적재되었는지 먼저 확인한다.\n- 외부 접속 전 절전모드와 서버 포트를 점검한다."
        return "가짜 응답 테스트입니다."

    # [실전 모드] 집에 가서 True로 바꾸면 이 아래 코드가 실행됨
    from openai import OpenAI
    client = OpenAI(base_url=BRAIN_URL, api_key="lm-studio")
    response = client.chat.completions.create(
        model="local-model",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
        temperature=0.1
    )
    return response.choices[0].message.content.strip()

# =====================================================================
# 1. M10: 지식 규합망 (옵시디언 자동 태그)
# =====================================================================
def m10_obsidian_tagger(content, title, base_path):
    global user_prompt # ask_brain에 넘길 프롬프트
    user_prompt = f"다음 텍스트에서 명사 키워드 3개만 쉼표로 추출해. 텍스트: {content}"
    
    keywords_str = ask_brain(user_prompt, "너는 크리스탈 정제 에이전트야.")
    keywords = [kw.strip() for kw in keywords_str.split(',') if kw.strip()]
    
    tags = " ".join([f"#{w.replace(' ', '_')}" for w in keywords])
    bi_links = " ".join([f"[[{w}]]" for w in keywords])
    
    md_content = f"---\ndate: {datetime.now().strftime('%Y-%m-%d')}\ntags: [{', '.join(keywords)}]\n---\n# {title}\n\n{content}\n\n---\n### 🔗 M10 링크\n{tags}\n{bi_links}"
    
    os.makedirs(base_path, exist_ok=True)
    with open(os.path.join(base_path, f"{title.replace(' ', '_')}.md"), 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"✅ [M10] 규합 완료: {bi_links}")

# =====================================================================
# 2. Hookify: 실수 방지망 (룰북 자동 생성)
# =====================================================================
def hookify_create_rule(error_log, mistake_name, rules_path):
    global user_prompt
    user_prompt = f"다음 에러 로그를 보고, 앞으로 같은 실수를 반복하지 않기 위한 행동 지침 2가지를 작성해. 에러: {error_log}"
    
    rule_content = ask_brain(user_prompt, "너는 하네스 시스템의 실수를 교정하는 수석 엔지니어(Hookify)야.")
    
    md_content = f"---\ndate: {datetime.now().strftime('%Y-%m-%d')}\ntags: [#Rule, #실수방지, #{mistake_name}]\n---\n# 🚨 룰북: {mistake_name} 방지\n\n### 발생한 에러\n```text\n{error_log}\n```\n\n### 🛡️ AI 행동 지침 (Hookify)\n{rule_content}"
    
    os.makedirs(rules_path, exist_ok=True)
    with open(os.path.join(rules_path, f"[규칙]_{mistake_name}.md"), 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"✅ [Hookify] 룰북 생성 완료! 다시는 같은 실수를 하지 않습니다. (저장됨: [규칙]_{mistake_name}.md)")

# =====================================================================
# 🚀 실전 테스트 실행
# =====================================================================
if __name__ == "__main__":
    print("--- 하네스 시스템 테스트 가동 ---")
    
    # 옵시디언 경로 설정 (본인 PC에 맞게 수정)
    obsidian_inbox = "./Obsidian_Inbox"
    obsidian_rules = "./Obsidian_Rules"
    
    # 1. M10 테스트
    m10_obsidian_tagger("서버 통신은 성공했는데 No models loaded 에러가 났다.", "LM스튜디오 연동 에러", obsidian_inbox)
    
    # 2. Hookify 테스트 (회원님의 방금 전 실수 상황 입력!)
    hookify_create_rule("Error code: 400 - No models loaded.", "모델적재누락", obsidian_rules)