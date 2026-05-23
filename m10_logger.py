import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
OBSIDIAN_PATH = os.getenv("OBSIDIAN_VAULT_PATH", "./Obsidian_Trading")

def save_to_obsidian(content):
    if not os.path.exists(OBSIDIAN_PATH):
        os.makedirs(OBSIDIAN_PATH, exist_ok=True)
    
    now_str = datetime.now().strftime("%Y-%m-%d_%H시%M분")
    filepath = os.path.join(OBSIDIAN_PATH, f"{now_str}_위원회보고서.md")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    return filepath