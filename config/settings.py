import os
from dotenv import load_dotenv

# 시스템 부팅 시 .env 파일을 가장 먼저 읽어옵니다.
load_dotenv()

# [보안 통제] API 키를 변수에 매핑하여 다른 모듈에 공급합니다.
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
UPBIT_ACCESS = os.getenv("UPBIT_ACCESS")
UPBIT_SECRET = os.getenv("UPBIT_SECRET")

# [채널 통제] 에러가 나거나 로그를 보낼 고정 디스코드 채널 ID (아까 복사한 값)
TARGET_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
DASHBOARD_CHANNEL_ID = int(os.getenv("DASHBOARD_CHANNEL_ID", 0))