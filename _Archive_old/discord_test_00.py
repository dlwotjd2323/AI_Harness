import requests
from datetime import datetime

# 복사하신 디스코드 웹후크 URL을 유지하세요
DISCORD_WEBHOOK_URL = "YOUR_TOKEN"

def send_discord_alert(ticker, message, bot_name="M9 퀀트 트레이더"):
    """
    지정된 봇 이름(bot_name)으로 디스코드에 알림을 전송합니다.
    """
    print(f"📡 [{bot_name}] 디스코드 알림 전송을 시도합니다...")
    
    data = {
        "username": bot_name, # ⚠️ 핵심 추가 사항: 웹훅 발신자 이름 강제 덮어쓰기
        "content": f"🚨 **[{bot_name} 시스템]** 새로운 보고서가 도착했습니다.",
        "embeds": [
            {
                "title": f"📈 {ticker} 상태 요약",
                "description": message,
                "color": 5814783, # 보라색 테마
                "footer": {
                    "text": f"하네스 중앙 관제탑 • {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                }
            }
        ]
    }
    
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data)
        
        if response.status_code == 204:
            print(f"✅ [디스코드] '{bot_name}' 명의로 알림 전송 성공!")
        else:
            print(f"⚠️ [디스코드] 전송 실패 (상태 코드: {response.status_code})")
    except Exception as e:
        print(f"⚠️ 전송 중 에러 발생: {e}")

# =====================================================================
# 🚀 다중 봇 이름 전송 테스트
# =====================================================================
if __name__ == "__main__":
    sample_ticker = "AAPL"
    
    # 1. 주식 트레이딩 봇 이름으로 발송
    sample_opinion_1 = "RSI가 72.38로 명백한 과매수 구간에 진입했습니다. '부분 매도'를 권장합니다."
    send_discord_alert(sample_ticker, sample_opinion_1, bot_name="M9 퀀트 트레이더")
    
    # 2. 인프라 시스템 관제 봇 이름으로 발송 (하나의 웹훅으로 다른 이름 사용)
    sample_opinion_2 = "Ansible 배포 중 K3s Pod OOMKilled 에러가 감지되었습니다. Hookify 규칙을 점검합니다."
    send_discord_alert("K3s-Cluster", sample_opinion_2, bot_name="NOC 인프라 관제탑")