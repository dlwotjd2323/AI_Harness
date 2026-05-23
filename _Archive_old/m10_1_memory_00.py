import os

def search_obsidian_memory(keyword, vault_path, max_results=2):
    """
    옵시디언 폴더를 스캔하여 키워드가 포함된 과거의 기억(마크다운 파일)을 찾아냅니다.
    """
    print(f"🔍 [M10-1 기억 스캔] '{keyword}' 관련 과거 기록을 탐색합니다...")
    
    if not os.path.exists(vault_path):
        return "⚠️ [시스템 알림] 지정된 옵시디언 경로가 존재하지 않거나 비어있습니다."

    found_memories = []
    
    # 폴더 내의 모든 마크다운 파일 탐색
    for filename in os.listdir(vault_path):
        if filename.endswith(".md"):
            filepath = os.path.join(vault_path, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # 파일명이나 본문에 키워드가 있으면 '유의미한 기억'으로 추출
                    if keyword.lower() in filename.lower() or keyword.lower() in content.lower():
                        found_memories.append({
                            "title": filename,
                            "content": content[:300] # LLM 토큰 절약을 위해 상단 300자(핵심 요약부)만 추출
                        })
            except Exception as e:
                print(f"⚠️ 파일 읽기 에러 ({filename}): {e}")

    # 검색 결과 조립 (AI 프롬프트 주입용 텍스트로 가공)
    if not found_memories:
        return f"💡 '{keyword}'에 대한 과거 기억이 없습니다. (새로운 상황입니다)"

    memory_report = f"📚 [과거 기억 인출 완료: {len(found_memories)}건 발견]\n\n"
    for i, mem in enumerate(found_memories[:max_results]):
        memory_report += f"[{i+1}. {mem['title']}]\n{mem['content']}...\n\n"
        
    return memory_report.strip()

# =====================================================================
# 🚀 기억 인출 실전 테스트
# =====================================================================
if __name__ == "__main__":
    # 방금 전 우리가 생성했던 트레이딩 매매일지 폴더를 타겟으로 설정합니다.
    obsidian_trading_path = "./Obsidian_Trading"
    
    # 'AAPL' 이라는 키워드로 과거에 작성해둔 매매 전략을 찾아옵니다.
    past_memory = search_obsidian_memory("AAPL", obsidian_trading_path)
    
    print("\n" + "="*50)
    print("🧠 하네스가 옵시디언에서 회상해낸 과거의 기억")
    print("="*50)
    print(past_memory)