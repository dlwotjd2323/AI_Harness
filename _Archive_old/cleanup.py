import os
import shutil

# 1. 작업 공간에 남겨둘 '최종 검토 완료' 파일 리스트
final_files = [
    "harness_master_01.py",
    "final_harness_05.py",
    "m10_tagger02.py",
    "m10_1_memory_00.py",
    "m9_trader_pipeline_00.py",
    "m9_trader_fetch_00.py",
    "main_harness_00.py",
    "discord_bot.py",
    "discord_test_00.py"
]

# 2. 구버전 보관용 아카이브 폴더 생성
archive_dir = "./_Archive_Tests"
os.makedirs(archive_dir, exist_ok=True)

# 3. 디렉토리 스캔 및 정리 실행
for filename in os.listdir('.'):
    # 파이썬 파일이면서, 정리 스크립트 자체는 건드리지 않음
    if filename.endswith('.py') and filename != os.path.basename(__file__):
        if filename not in final_files:
            # 구버전 파일 격리
            shutil.move(filename, os.path.join(archive_dir, filename))
            print(f"📦 보관소로 이동됨: {filename}")

print("\n✅ [디렉토리 정리 완료] 작업 공간이 최적화되었습니다!")