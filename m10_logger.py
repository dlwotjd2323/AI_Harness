import os
from datetime import datetime
from dotenv import load_dotenv
import chromadb 

load_dotenv()
OBSIDIAN_PATH = os.getenv("OBSIDIAN_VAULT_PATH", "./Obsidian_Trading")
CHROMA_PATH = os.getenv("CHROMA_DB_PATH", "./Chroma_DB")

chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
memory_collection = chroma_client.get_or_create_collection(name="investment_memory")

def save_to_obsidian(content, ticker="KRW-BTC"):
    coin_name = ticker.split('-')[1] 
    
    if not os.path.exists(OBSIDIAN_PATH):
        os.makedirs(OBSIDIAN_PATH, exist_ok=True)
    
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d_%H시%M분")
    filepath = os.path.join(OBSIDIAN_PATH, f"{now_str}_{coin_name}_위원회보고서.md")
    
    # ==========================================
    # 🌟 [추가됨] 정밀 회계 기록(Ledger) 마크다운 표 생성
    # ==========================================
    decision = "관망"
    if "[매수]" in content: decision = "매수"
    elif "[매도]" in content: decision = "매도"
    
    execute_log = "주문 보류"
    if "⚙️" in content:
        execute_log = content.split("⚙️")[1].strip()
        
    ledger_section = "\n\n## 💰 [거래 회계 원장 (Transaction Ledger)]\n"
    ledger_section += "| 일시 | 종목 | 판결 | 실행 결과 |\n"
    ledger_section += "|:---:|:---:|:---:|---|\n"
    ledger_section += f"| {now.strftime('%Y-%m-%d %H:%M')} | **{coin_name}** | **{decision}** | {execute_log} |\n"
    
    final_content = content + ledger_section
    # ==========================================
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(final_content)
        
    doc_id = f"report_{coin_name}_{now.strftime('%Y%m%d%H%M%S')}" 
    
    memory_collection.add(
        documents=[content],
        metadatas=[{"date": now_str, "type": "committee_report", "ticker": ticker}],
        ids=[doc_id]
    )
    print(f"🧠 [기억 각인 및 회계 기록 완료] 문서 ID: {doc_id}")
    
    return filepath