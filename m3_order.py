import os
import jwt
import uuid
import hashlib
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()
UPBIT_ACCESS_KEY = os.getenv("UPBIT_ACCESS_KEY", "")
UPBIT_SECRET_KEY = os.getenv("UPBIT_SECRET_KEY", "")
SERVER_URL = "https://api.upbit.com"

def execute_trade(ticker, decision, amount=10000):
    """AI 수석 결재자의 판결을 받아 실제 1만 원 시장가 매수 주문을 실행합니다."""
    # 1. API 키 검증 및 매수 결정 여부 확인
    if not UPBIT_ACCESS_KEY or not UPBIT_SECRET_KEY:
        return f"⚠️ [API 키 누락] 주문 시뮬레이션 모드 작동"
        
    if "[매수]" not in decision:
        return f"⏸️ [주문 보류] 판결 사유에 따라 매수를 진행하지 않습니다."

    # 2. 업비트 시장가 매수 (Price 타입) 파라미터 구성
    query = {
        'market': ticker,
        'side': 'bid',       # 매수
        'price': str(amount),# 주문 금액 (기본 10,000 KRW)
        'ord_type': 'price', # 시장가 매수
    }
    
    query_string = urlencode(query).encode()
    m = hashlib.sha512()
    m.update(query_string)
    query_hash = m.hexdigest()

    payload = {
        'access_key': UPBIT_ACCESS_KEY,
        'nonce': str(uuid.uuid4()),
        'query_hash': query_hash,
        'query_hash_alg': 'SHA512',
    }

    jwt_token = jwt.encode(payload, UPBIT_SECRET_KEY)
    authorization_token = 'Bearer {}'.format(jwt_token)
    headers = {"Authorization": authorization_token}

    # 3. 주문 API 전송
    try:
        res = requests.post(SERVER_URL + "/v1/orders", params=query, headers=headers)
        res.raise_for_status()
        return f"💸 **[매수 체결 완료]** {ticker} {amount:,}원 시장가 진입 성공!"
    except Exception as e:
        return f"❌ **[주문 실패]** {ticker} 매수 중 오류 발생: {e}"