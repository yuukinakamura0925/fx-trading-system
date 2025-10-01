"""
GMO Coin FX API クライアント
Public APIを使用した市場データ取得
"""

import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class GMOFXClient:
    """GMO Coin FX API クライアント"""

    BASE_URL = "https://forex-api.coin.z.com/public/v1"

    # GMO APIの時間軸マッピング
    INTERVAL_MAP = {
        "5m": "5min",
        "1h": "1hour",
        "4h": "4hour",
        "1d": "1day",
        "1min": "1min",
        "10min": "10min",
        "15min": "15min",
        "30min": "30min",
        "8hour": "8hour",
        "12hour": "12hour",
        "1week": "1week",
        "1month": "1month",
    }

    def __init__(self, timeout: int = 10):
        """
        初期化

        Args:
            timeout: リクエストタイムアウト（秒）
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def get_klines(
        self,
        symbol: str,
        interval: str,
        date: str,
        price_type: str = "ASK"
    ) -> List[Dict[str, Any]]:
        """
        KLine（ローソク足）データを取得

        Args:
            symbol: 通貨ペア（例: USD_JPY）
            interval: 時間軸（例: 5m, 1h, 4h, 1d）
            date: 日付（YYYYMMDD形式）
            price_type: 価格タイプ（BID or ASK）

        Returns:
            KLineデータのリスト

        Raises:
            Exception: API呼び出し失敗時
        """
        # interval変換（5m -> 5min）
        gmo_interval = self.INTERVAL_MAP.get(interval, interval)

        url = f"{self.BASE_URL}/klines"
        params = {
            "symbol": symbol,
            "priceType": price_type,
            "interval": gmo_interval,
            "date": date
        }

        logger.info(f"GMO API リクエスト: {url} {params}")

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            if data.get("status") != 0:
                raise Exception(f"GMO API エラー: {data}")

            klines = data.get("data", [])
            logger.info(f"GMO API 取得成功: {len(klines)} 件")

            return klines

        except requests.exceptions.RequestException as e:
            logger.error(f"GMO API リクエストエラー: {e}")
            raise

    def get_klines_by_year(
        self,
        symbol: str,
        interval: str,
        year: str,
        price_type: str = "ASK"
    ) -> List[Dict[str, Any]]:
        """
        年単位でKLineデータを取得（GMO APIのYYYY形式を使用）

        Args:
            symbol: 通貨ペア（例: USD_JPY）
            interval: 時間軸（例: 1d, 1week, 1month）
            year: 年（YYYY形式、例: 2025）
            price_type: 価格タイプ（BID or ASK）

        Returns:
            KLineデータのリスト
        """
        return self.get_klines(symbol, interval, year, price_type)

    def get_klines_multi_days(
        self,
        symbol: str,
        interval: str,
        days: int,
        price_type: str = "ASK"
    ) -> pd.DataFrame:
        """
        複数日のKLineデータを取得してDataFrameに変換

        長期足（1day, 1week, 1month）は年単位で取得、
        短期足（5min, 1hour等）は日単位で取得

        Args:
            symbol: 通貨ペア（例: USD_JPY）
            interval: 時間軸（例: 5m, 1h, 4h, 1d）
            days: 過去何日分取得するか
            price_type: 価格タイプ（BID or ASK）

        Returns:
            pandas DataFrame（OHLC + タイムスタンプ）
        """
        all_klines = []
        today = datetime.now()

        # 長期足は年単位で取得（GMO APIのYYYY形式を使用）
        if interval in ["1d", "1day", "4h", "4hour", "8hour", "12hour", "1week", "1month"]:
            logger.info(f"長期足データを年単位で取得: {interval}")
            # 今年と去年のデータを取得
            for year_offset in range(2):  # 今年と去年
                year = str(today.year - year_offset)
                try:
                    klines = self.get_klines_by_year(symbol, interval, year, price_type)
                    if klines:
                        all_klines.extend(klines)
                        logger.info(f"年データ取得成功: {year} - {len(klines)}件")
                except Exception as e:
                    logger.warning(f"年データ取得失敗: {year} - {e}")
                    continue
        else:
            # 短期足は日単位で取得（平日のみ）
            logger.info(f"短期足データを日単位で取得: {interval}")
            attempted_days = 0
            successful_days = 0
            consecutive_failures = 0  # 連続失敗カウント
            max_consecutive_failures = 30  # 連続30回失敗したら打ち切り

            for i in range(days * 2):
                if successful_days >= days:
                    break

                # 連続失敗が多すぎる場合は打ち切り（古いデータがない）
                if consecutive_failures >= max_consecutive_failures:
                    logger.info(f"連続{consecutive_failures}回失敗のため取得終了（これ以上古いデータなし）")
                    break

                target_date = today - timedelta(days=i)

                # 週末はスキップ
                if target_date.weekday() >= 5:
                    continue

                date_str = target_date.strftime("%Y%m%d")
                attempted_days += 1

                try:
                    klines = self.get_klines(symbol, interval, date_str, price_type)
                    if klines:
                        all_klines.extend(klines)
                        successful_days += 1
                        consecutive_failures = 0  # 成功したらリセット
                    else:
                        consecutive_failures += 1
                except Exception as e:
                    # 404エラーの場合は連続失敗カウント増加
                    if "404" in str(e) or "Not Found" in str(e):
                        consecutive_failures += 1
                        logger.warning(f"データなし: {date_str} (連続失敗: {consecutive_failures}回)")
                    else:
                        logger.warning(f"データ取得失敗: {date_str} - {e}")
                    continue

        if not all_klines:
            logger.warning(f"データが取得できませんでした: {symbol} {interval}")
            return pd.DataFrame()

        # DataFrameに変換
        df = pd.DataFrame(all_klines)

        # タイムスタンプをDatetime型に変換（ミリ秒 -> 秒）
        df['openTime'] = pd.to_datetime(df['openTime'].astype(int), unit='ms')

        # 数値型に変換
        for col in ['open', 'high', 'low', 'close']:
            df[col] = pd.to_numeric(df[col])

        # カラム名をyfinance形式に変換（既存コードとの互換性）
        df = df.rename(columns={
            'openTime': 'Date',
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close'
        })

        # インデックスをDateに設定
        df = df.set_index('Date')
        df = df.sort_index()

        # 重複削除
        df = df[~df.index.duplicated(keep='last')]

        logger.info(f"DataFrame作成完了: {len(df)} rows")

        return df

    def get_symbols(self) -> List[Dict[str, Any]]:
        """
        取引可能な通貨ペア一覧を取得

        Returns:
            通貨ペア情報のリスト
        """
        url = f"{self.BASE_URL}/symbols"

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            if data.get("status") != 0:
                raise Exception(f"GMO API エラー: {data}")

            return data.get("data", [])

        except requests.exceptions.RequestException as e:
            logger.error(f"GMO API リクエストエラー: {e}")
            raise

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        現在価格を取得

        Args:
            symbol: 通貨ペア（例: USD_JPY）

        Returns:
            ティッカー情報
        """
        url = f"{self.BASE_URL}/ticker"
        params = {"symbol": symbol}

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            if data.get("status") != 0:
                raise Exception(f"GMO API エラー: {data}")

            ticker_list = data.get("data", [])
            if ticker_list:
                return ticker_list[0]

            return {}

        except requests.exceptions.RequestException as e:
            logger.error(f"GMO API リクエストエラー: {e}")
            raise
