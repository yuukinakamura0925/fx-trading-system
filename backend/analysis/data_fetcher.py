"""
シンプルな過去データ取得モジュール
分析機能は一切含まず、純粋にGMO APIからデータを取得するのみ
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
from enum import Enum
from .gmo_client import GMOFXClient


class TimeFrame(Enum):
    """時間軸の定義"""
    FIVE_MIN = "5m"
    ONE_HOUR = "1h"
    FOUR_HOUR = "4h"
    ONE_DAY = "1d"


class DataFetcher:
    """過去データ取得クラス"""

    def __init__(self):
        self.gmo_client = GMOFXClient()

        # 時間軸ごとの設定
        self.timeframes = {
            TimeFrame.FIVE_MIN: {
                "interval": "5min",
                "days": 7,  # 5分足は7日分
                "description": "5分足（スキャルピング用）"
            },
            TimeFrame.ONE_HOUR: {
                "interval": "1hour",
                "days": 30,  # 1時間足は30日分
                "description": "1時間足（デイトレード用）"
            },
            TimeFrame.FOUR_HOUR: {
                "interval": "4hour",
                "days": 180,  # 4時間足は180日分
                "description": "4時間足（スイング用）"
            },
            TimeFrame.ONE_DAY: {
                "interval": "1day",
                "days": 365,  # 日足は365日分
                "description": "日足（長期トレンド用）"
            }
        }

    def fetch_all_timeframes(self, symbol: str) -> Dict[str, Any]:
        """
        全時間軸の過去データを取得

        Args:
            symbol: 通貨ペアシンボル (例: "USDJPY=X")

        Returns:
            全時間軸のデータ
        """
        # シンボル変換（yfinance形式 → GMO形式）
        gmo_symbol = symbol.replace('=X', '').replace('JPY', '_JPY')

        results = {}

        for timeframe, config in self.timeframes.items():
            data = self._fetch_timeframe(gmo_symbol, timeframe, config)
            results[timeframe.value] = data

        return {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "timeframes": results
        }

    def _fetch_timeframe(self, symbol: str, timeframe: TimeFrame, config: Dict) -> Dict[str, Any]:
        """
        単一時間軸のデータを取得

        Args:
            symbol: GMO形式のシンボル (例: "USD_JPY")
            timeframe: 時間軸
            config: 設定

        Returns:
            データと説明
        """
        try:
            # GMO APIからデータ取得
            data = self.gmo_client.get_klines_multi_days(
                symbol=symbol,
                interval=config["interval"],
                days=config["days"]
            )

            if data.empty:
                return {
                    "error": f"データが取得できませんでした: {timeframe.value}",
                    "data_points": 0
                }

            # DataFrameをJSON形式に変換
            records = []
            for index, row in data.iterrows():
                records.append({
                    "timestamp": index.isoformat(),
                    "open": float(row['Open']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "close": float(row['Close']),
                    "volume": int(row['Volume']) if 'Volume' in row else 0
                })

            return {
                "timeframe": timeframe.value,
                "description": config["description"],
                "interval": config["interval"],
                "days": config["days"],
                "data": records,
                "data_points": len(records)
            }

        except Exception as e:
            return {
                "error": f"データ取得エラー: {str(e)}",
                "timeframe": timeframe.value,
                "data_points": 0
            }
