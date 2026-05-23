import requests

def get_upbit_btc_data():
    """업비트 퍼블릭 API를 통해 비트코인(KRW-BTC) 시세 데이터를 가져옵니다."""
    url = "https://api.upbit.com/v1/ticker?markets=KRW-BTC"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()[0]
        
        return (
            f"📈 [현재 시장 데이터 브리핑]\n"
            f"- 현재가: {data['trade_price']:,} KRW\n"
            f"- 24h 최고가: {data['high_price']:,} KRW\n"
            f"- 24h 최저가: {data['low_price']:,} KRW\n"
            f"- 24h 거래량: {data['acc_trade_volume_24h']:,.2f} BTC"
        )
    except Exception as e:
        return f"⚠️ 시세 데이터 수집 실패: {e}"