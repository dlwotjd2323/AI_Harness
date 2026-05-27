import os
import jwt
import uuid
import hashlib
import requests
import pyupbit
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()
UPBIT_ACCESS_KEY = os.getenv("UPBIT_ACCESS_KEY", "")
UPBIT_SECRET_KEY = os.getenv("UPBIT_SECRET_KEY", "")
SERVER_URL = "https://api.upbit.com"

def get_my_account():
    """내 업비트 계좌의 원화 잔고와 보유 코인 내역(평단가, 매수금액)을 조회합니다."""
    if not UPBIT_ACCESS_KEY or not UPBIT_SECRET_KEY:
        return "⚠️ [API 키 누락] 계좌 조회 불가", 0

    payload = {
        'access_key': UPBIT_ACCESS_KEY,
        'nonce': str(uuid.uuid4()),
    }
    
    jwt_token = jwt.encode(payload, UPBIT_SECRET_KEY)
    authorization_token = 'Bearer {}'.format(jwt_token)
    headers = {"Authorization": authorization_token}

    try:
        res = requests.get(SERVER_URL + "/v1/accounts", headers=headers)
        res.raise_for_status()
        accounts = res.json()
        
        report = "🏦 **[현재 계좌 자산 현황]**\n"
        krw_balance = 0
        
        for acc in accounts:
            if acc['currency'] == 'KRW':
                krw_balance = float(acc['balance'])
                report += f"- 💵 가용 시드머니: {krw_balance:,.0f} KRW\n"
            else:
                avg_price = float(acc['avg_buy_price'])
                balance = float(acc['balance'])
                if avg_price > 0 and balance > 0:
                    total_invested = avg_price * balance
                    report += f"- 🪙 {acc['currency']} 보유량: {balance:.6f} 개 (평단가: {avg_price:,.0f}원, 총 매수금액: {total_invested:,.0f}원)\n"
                    
        return report, krw_balance
        
    except Exception as e:
        return f"❌ [계좌 조회 실패]: {e}", 0

def execute_trade(ticker, decision):
    """AI 판결에 따라 계좌 잔고를 확인하고 100% 풀매수/풀매도를 실행하는 복리 스노우볼 엔진입니다."""
    if not UPBIT_ACCESS_KEY or not UPBIT_SECRET_KEY:
        return "⚠️ [API 키 누락] 주문 시뮬레이션 모드 작동"
        
    if "[관망]" in decision:
        return "⏸️ [주문 보류] 관망 결정으로 매매를 진행하지 않습니다."

    coin_name = ticker.split('-')[1]
    
    # 1. 현재 계좌 잔고 조회
    try:
        payload = {'access_key': UPBIT_ACCESS_KEY, 'nonce': str(uuid.uuid4())}
        jwt_token = jwt.encode(payload, UPBIT_SECRET_KEY)
        headers = {"Authorization": f"Bearer {jwt_token}"}
        res = requests.get(SERVER_URL + "/v1/accounts", headers=headers)
        res.raise_for_status()
        accounts = res.json()
    except Exception as e:
        return f"❌ [계좌 조회 실패] 주문 중단: {e}"

    krw_balance = 0
    coin_balance = 0
    for acc in accounts:
        if acc['currency'] == 'KRW':
            krw_balance = float(acc['balance'])
        elif acc['currency'] == coin_name:
            coin_balance = float(acc['balance'])

    # 2. 스노우볼 주문 로직 구성
    query = {}
    if "[매수]" in decision:
        # 시장가 매수 (가용 시드의 99.9% 사용 - 수수료 0.05% 및 슬리피지 대비)
        buy_amount = krw_balance * 0.999
        if buy_amount < 5000:
            return f"⚠️ [주문 보류] 가용 원화({krw_balance:,.0f}원)가 최소 주문 금액(5,000원)보다 부족합니다."
        
        query = {
            'market': ticker,
            'side': 'bid',
            'price': str(int(buy_amount)), # 소수점 버림
            'ord_type': 'price',
        }
        action_text = f"💸 **[전액 매수 체결]** {int(buy_amount):,}원 복리 시장가 진입 성공!"
        
    elif "[매도]" in decision:
        # 시장가 매도 (보유 코인 100% 전량 익절/손절)
        if coin_balance == 0:
            return f"⚠️ [주문 보류] 보유 중인 {coin_name} 코인이 없어 매도할 수 없습니다."
            
        query = {
            'market': ticker,
            'side': 'ask',
            'volume': str(coin_balance),
            'ord_type': 'market',
        }
        action_text = f"💰 **[전량 매도 체결]** {coin_balance:.6f} {coin_name} 복리 수익 실현(시장가 던지기) 성공!"
        
    else:
        return "⏸️ [주문 보류] 판결 사유에 명확한 지시가 없습니다."

    # 3. 실전 API 주문 전송
    try:
        query_string = urlencode(query).encode()
        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()

        # 🌟 [핵심 패치됨]: 이전 payload를 재사용하지 않고 주문 전용(Nonce 신규 발급) 토큰을 생성합니다.
        order_payload = {
            'access_key': UPBIT_ACCESS_KEY,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512'
        }
        
        jwt_token = jwt.encode(order_payload, UPBIT_SECRET_KEY)
        headers["Authorization"] = f"Bearer {jwt_token}"

        # 🌟 [패치됨]: params 대신 json 규격을 사용하여 401 에러 원천 차단.
        order_res = requests.post(SERVER_URL + "/v1/orders", json=query, headers=headers)
        order_res.raise_for_status()
        return action_text
        
    except Exception as e:
        return f"❌ [주문 실패] API 오류 발생: {e}"

# ==========================================
# 🎯 [신규 이식] 잔치국수 스나이퍼용 수익률 레이더
# ==========================================
def get_current_yield(ticker="KRW-BTC"):
    """
    특정 코인의 현재 수익률(%)과 보유 수량을 실시간으로 계산하여 반환합니다.
    """
    try:
        upbit = pyupbit.Upbit(UPBIT_ACCESS_KEY, UPBIT_SECRET_KEY)
        
        # 1. 내 지갑의 보유 수량 및 매수 평균가 조회
        balance = upbit.get_balance(ticker)
        avg_buy_price = upbit.get_avg_buy_price(ticker)
        
        # ⚠️ 코인을 보유하고 있지 않다면 감시할 필요가 없으므로 0을 반환
        if balance == 0 or balance is None or avg_buy_price == 0:
            return 0.0, 0.0
            
        # 2. 시장 현재가 조회
        current_price = pyupbit.get_current_price(ticker)
        
        # 3. 순수익률 계산 공식: ((현재가 - 매수평균가) / 매수평균가) * 100
        profit_rate = ((current_price - avg_buy_price) / avg_buy_price) * 100
        
        # 소수점 2자리까지만 깔끔하게 잘라서 반환합니다. (예: 1.52)
        return round(profit_rate, 2), balance

    except Exception as e:
        print(f"⚠️ [수익률 계산 오류] API 통신 지연: {e}")
        return 0.0, 0.0