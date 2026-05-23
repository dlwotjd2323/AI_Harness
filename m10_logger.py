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
    coin_name = ticker.split('-')[1] # 종목 이름 추출
    
    if not os.path.exists(OBSIDIAN_PATH):
        os.makedirs(OBSIDIAN_PATH, exist_ok=True)
    
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d_%H시%M분")
    # 파일명에 종목 이름 추가
    filepath = os.path.join(OBSIDIAN_PATH, f"{now_str}_{coin_name}_위원회보고서.md")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
        
    # 벡터 DB 동시 저장 (기억 각인 시 종목 ID 추가)
    doc_id = f"report_{coin_name}_{now.strftime('%Y%m%d%H%M%S')}" 
    
    memory_collection.add(
        documents=[content],
        metadatas=[{"date": now_str, "type": "committee_report", "ticker": ticker}],
        ids=[doc_id]
    )
    print(f"🧠 [장기 기억 각인 완료] 문서 ID: {doc_id}")
    
    return filepath