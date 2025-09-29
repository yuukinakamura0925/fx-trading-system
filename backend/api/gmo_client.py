"""
GMOコインFX API クライアント
Public APIとPrivate APIの両方に対応
"""

import requests
import json
import hmac
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from decimal import Decimal


class GMOPublicClient:
    """
    GMOコイン Public API クライアント
    認証不要で市場データを取得
    """

    def __init__(self):
        """Public APIクライアントを初期化"""
        self.base_url = 'https://forex-api.coin.z.com/public'
        self.session = requests.Session()

    def get_status(self) -> Dict[str, Any]:
        """
        外国為替FXステータスを取得

        Returns:
            dict: {
                "status": 0,
                "data": {"status": "OPEN"/"CLOSE"/"MAINTENANCE"},
                "responsetime": "2019-03-19T02:15:06.001Z"
            }
        """
        path = '/v1/status'
        response = self.session.get(self.base_url + path)
        response.raise_for_status()  # HTTPエラーをチェック
        return response.json()

    def get_ticker(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        全銘柄分の最新レートを取得

        Args:
            symbol: 特定の銘柄のみ取得する場合は指定（例: "USD_JPY"）

        Returns:
            dict: {
                "status": 0,
                "data": [
                    {
                        "symbol": "USD_JPY",
                        "ask": "137.644",  # 買値
                        "bid": "137.632",  # 売値
                        "timestamp": "2018-03-30T12:34:56.789671Z",
                        "status": "OPEN"
                    },
                    ...
                ],
                "responsetime": "2019-03-19T02:15:06.014Z"
            }
        """
        path = '/v1/ticker'
        response = self.session.get(self.base_url + path)
        response.raise_for_status()
        data = response.json()

        # 特定の銘柄のみフィルタリング
        if symbol and data.get('status') == 0:
            filtered_data = [
                item for item in data['data']
                if item['symbol'] == symbol
            ]
            data['data'] = filtered_data

        return data

    def get_klines(
        self,
        symbol: str,
        price_type: str,
        interval: str,
        date: str
    ) -> Dict[str, Any]:
        """
        指定した銘柄の四本値（ローソク足データ）を取得

        Args:
            symbol: 取扱銘柄（例: "USD_JPY"）
            price_type: "BID" または "ASK"
            interval: 時間間隔
                - 日付指定(YYYYMMDD): 1min, 5min, 10min, 15min, 30min, 1hour
                - 年指定(YYYY): 4hour, 8hour, 12hour, 1day, 1week, 1month
            date: 日付フォーマット（YYYYMMDD または YYYY）

        Returns:
            dict: {
                "status": 0,
                "data": [
                    {
                        "openTime": "1618588800000",  # Unix timestamp (ms)
                        "open": "141.365",   # 始値
                        "high": "141.368",   # 高値
                        "low": "141.360",    # 安値
                        "close": "141.362"   # 終値
                    },
                    ...
                ],
                "responsetime": "2023-07-08T22:28:07.980Z"
            }
        """
        path = f'/v1/klines'
        params = {
            'symbol': symbol,
            'priceType': price_type,
            'interval': interval,
            'date': date
        }

        response = self.session.get(self.base_url + path, params=params)
        response.raise_for_status()
        return response.json()

    def get_symbols(self) -> Dict[str, Any]:
        """
        取引ルールを取得

        Returns:
            dict: {
                "status": 0,
                "data": [
                    {
                        "symbol": "USD_JPY",
                        "minOpenOrderSize": "10000",     # 新規最小注文数量/回
                        "maxOrderSize": "500000",         # 最大注文数量/回
                        "sizeStep": "1",                  # 最小注文単位/回
                        "tickSize": "0.001"               # 注文価格の呼値
                    },
                    ...
                ],
                "responsetime": "2022-12-15T19:22:23.792Z"
            }
        """
        path = '/v1/symbols'
        response = self.session.get(self.base_url + path)
        response.raise_for_status()
        return response.json()

    def format_ticker_data(self, ticker_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        ティッカーデータを整形して表示用に変換

        Args:
            ticker_data: get_ticker()の戻り値

        Returns:
            list: 整形されたレートデータのリスト
        """
        if ticker_data.get('status') != 0:
            return []

        formatted_data = []
        for item in ticker_data.get('data', []):
            # スプレッド計算（買値 - 売値）
            ask = Decimal(item['ask'])
            bid = Decimal(item['bid'])
            spread = ask - bid

            formatted_item = {
                'symbol': item['symbol'],
                'ask': float(ask),
                'bid': float(bid),
                'spread': float(spread),
                'spread_pips': float(spread * 100),  # pips単位（0.01円 = 1pips）
                'status': item['status'],
                'timestamp': item['timestamp']
            }
            formatted_data.append(formatted_item)

        return formatted_data


class GMOPrivateClient:
    """
    GMOコイン Private API クライアント
    認証が必要な取引・アカウント操作
    """

    def __init__(self, api_key: str, secret_key: str):
        """
        Private APIクライアントを初期化

        Args:
            api_key: APIキー
            secret_key: APIシークレット
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = 'https://forex-api.coin.z.com/private'
        self.session = requests.Session()

    def _create_signature(
        self,
        method: str,
        path: str,
        body: Dict[str, Any] = None
    ) -> Dict[str, str]:
        """
        API認証用の署名を生成

        Args:
            method: HTTPメソッド（GET/POST/PUT/DELETE）
            path: APIパス（/v1/...）
            body: リクエストボディ（POSTの場合）

        Returns:
            dict: 認証ヘッダー
        """
        timestamp = '{0}000'.format(int(time.mktime(datetime.now().timetuple())))

        # GETリクエストの場合、ボディは空文字列
        body_str = json.dumps(body) if body else ''

        # 署名対象文字列を作成
        text = timestamp + method + path + body_str

        # HMAC-SHA256で署名
        sign = hmac.new(
            bytes(self.secret_key.encode('ascii')),
            bytes(text.encode('ascii')),
            hashlib.sha256
        ).hexdigest()

        return {
            "API-KEY": self.api_key,
            "API-TIMESTAMP": timestamp,
            "API-SIGN": sign
        }

    def get_assets(self) -> Dict[str, Any]:
        """
        資産残高を取得

        Returns:
            dict: 資産情報
        """
        path = '/v1/account/assets'
        headers = self._create_signature('GET', path)

        response = self.session.get(
            self.base_url + path,
            headers=headers
        )
        response.raise_for_status()
        return response.json()

    def create_order(
        self,
        symbol: str,
        side: str,
        size: str,
        execution_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        新規注文を作成

        Args:
            symbol: 取扱銘柄（例: "USD_JPY"）
            side: "BUY" または "SELL"
            size: 注文数量
            execution_type: "MARKET", "LIMIT", "STOP", "OCO"
            **kwargs: その他のオプション（limitPrice, stopPrice等）

        Returns:
            dict: 注文結果
        """
        path = '/v1/order'
        body = {
            "symbol": symbol,
            "side": side,
            "size": size,
            "executionType": execution_type
        }
        body.update(kwargs)

        headers = self._create_signature('POST', path, body)

        response = self.session.post(
            self.base_url + path,
            headers=headers,
            data=json.dumps(body)
        )
        response.raise_for_status()
        return response.json()


# 使用例とテスト用コード
if __name__ == "__main__":
    # Public APIのテスト
    public_client = GMOPublicClient()

    # FXステータス確認
    print("=== FXステータス ===")
    status = public_client.get_status()
    print(f"ステータス: {status['data']['status']}")

    # 最新レート取得
    print("\n=== 最新レート ===")
    ticker = public_client.get_ticker()
    if ticker['status'] == 0:
        formatted_rates = public_client.format_ticker_data(ticker)
        for rate in formatted_rates[:5]:  # 最初の5件のみ表示
            print(f"{rate['symbol']}: "
                  f"買値={rate['ask']:.3f}, "
                  f"売値={rate['bid']:.3f}, "
                  f"スプレッド={rate['spread_pips']:.1f}pips")

    # 取引ルール確認
    print("\n=== 取引ルール ===")
    symbols = public_client.get_symbols()
    if symbols['status'] == 0:
        for rule in symbols['data'][:3]:  # 最初の3件のみ表示
            print(f"{rule['symbol']}: "
                  f"最小={rule['minOpenOrderSize']}, "
                  f"最大={rule['maxOrderSize']}, "
                  f"呼値={rule['tickSize']}")