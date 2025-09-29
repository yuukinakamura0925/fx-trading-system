"""
シンプルなFX分析システム（エラー修正版）
pandas Series エラーを回避した簡易版ハイブリッドアナライザー
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import os
from typing import Dict, Any, Optional


class SimpleFXAnalyzer:
    """シンプルなFX分析クラス"""

    def __init__(self, openai_api_key: Optional[str] = None):
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')

    def analyze(self, symbol: str = "USDJPY=X", period: str = "3mo", use_llm: bool = True) -> Dict[str, Any]:
        """
        FX分析を実行

        Args:
            symbol: 通貨ペアシンボル
            period: 分析期間
            use_llm: LLM分析を使用するか

        Returns:
            分析結果
        """
        try:
            # データ取得
            data = yf.download(symbol, period=period, interval="1d", progress=False)

            if data.empty:
                raise ValueError(f"データが取得できません: {symbol}")

            # アルゴリズム分析
            algo_result = self._algorithmic_analysis(data)

            result = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "algorithmic_analysis": algo_result
            }

            # LLM分析（APIキーがある場合）
            if use_llm and self.api_key:
                llm_result = self._llm_analysis(algo_result)
                result["llm_analysis"] = llm_result

                # 統合推奨
                result["hybrid_recommendation"] = self._hybrid_recommendation(algo_result, llm_result)

            return result

        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _algorithmic_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """アルゴリズムベースの分析"""

        # yfinanceのMultiIndexカラム対応
        if isinstance(data.columns, pd.MultiIndex):
            # MultiIndexの場合は最初のレベルを使用
            data.columns = data.columns.get_level_values(0)

        # 基本データ取得（Series エラーを回避）
        close_prices = data['Close']
        high_prices = data['High']
        low_prices = data['Low']

        # 最新価格（安全な取得方法）
        current_price = self._safe_float(close_prices.iloc[-1])

        # 移動平均計算
        sma20 = close_prices.rolling(window=20).mean()
        sma50 = close_prices.rolling(window=50).mean()

        current_sma20 = self._safe_float(sma20.iloc[-1])
        current_sma50 = self._safe_float(sma50.iloc[-1])

        # RSI計算
        rsi = self._calculate_rsi(close_prices)
        current_rsi = self._safe_float(rsi.iloc[-1])

        # トレンド判定
        trend = self._determine_trend(current_price, current_sma20, current_sma50)

        # シグナル生成
        signal = self._generate_signal(current_rsi, trend)

        # キーレベル計算
        recent_high = self._safe_float(high_prices.tail(20).max())
        recent_low = self._safe_float(low_prices.tail(20).min())

        # サポート・レジスタンス（簡易版）
        resistance_1 = current_price + (recent_high - current_price) * 0.5
        support_1 = current_price - (current_price - recent_low) * 0.5

        return {
            "trend": trend,
            "signal": signal["action"],
            "confidence": signal["confidence"],
            "signal_strength": signal["strength"],
            "risk_reward_ratio": 1.5,  # 固定値
            "position_size": 100.0,    # 固定値
            "key_levels": {
                "current_price": current_price,
                "resistance_1": resistance_1,
                "resistance_2": recent_high,
                "support_1": support_1,
                "support_2": recent_low,
                "pivot": (recent_high + recent_low + current_price) / 3,
                "recent_high": recent_high,
                "recent_low": recent_low
            },
            "indicators": {
                "price": current_price,
                "sma20": current_sma20,
                "sma50": current_sma50,
                "ema20": current_sma20,  # 簡略化
                "rsi": current_rsi,
                "macd": 0.0,  # 簡略化
                "macd_signal": 0.0,  # 簡略化
                "bb_upper": current_price * 1.02,  # 簡易計算
                "bb_lower": current_price * 0.98,  # 簡易計算
                "stoch_k": current_rsi,  # 簡略化
                "stoch_d": current_rsi   # 簡略化
            },
            "summary": f"トレンド: {trend}, シグナル: {signal['action']}, RSI: {current_rsi:.1f}"
        }

    def _safe_float(self, value) -> float:
        """安全なfloat変換（pandas Series エラー回避）"""
        try:
            if pd.isna(value):
                return 0.0
            return float(value)
        except:
            return 0.0

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """RSI計算"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _determine_trend(self, price: float, sma20: float, sma50: float) -> str:
        """トレンド判定"""
        if sma20 > sma50 and price > sma20:
            return "強い上昇トレンド"
        elif sma20 > sma50:
            return "上昇トレンド"
        elif sma20 < sma50 and price < sma20:
            return "強い下降トレンド"
        elif sma20 < sma50:
            return "下降トレンド"
        else:
            return "レンジ相場"

    def _generate_signal(self, rsi: float, trend: str) -> Dict[str, Any]:
        """シグナル生成"""
        confidence = 50.0
        strength = "中程度"

        if "上昇" in trend and rsi < 70:
            action = "BUY"
            confidence = 75.0
            strength = "強い"
        elif "下降" in trend and rsi > 30:
            action = "SELL"
            confidence = 75.0
            strength = "強い"
        elif rsi < 30:
            action = "BUY"
            confidence = 60.0
            strength = "中程度"
        elif rsi > 70:
            action = "SELL"
            confidence = 60.0
            strength = "中程度"
        else:
            action = "HOLD"
            confidence = 40.0
            strength = "弱い"

        return {
            "action": action,
            "confidence": confidence,
            "strength": strength
        }

    def _llm_analysis(self, algo_result: Dict[str, Any]) -> Dict[str, Any]:
        """LLM分析のモック（実際はOpenAI API呼び出し）"""
        return {
            "market_psychology": f"現在の市場は{algo_result['trend']}の状況です。",
            "entry_strategy": {
                "timing": "東京時間またはロンドン時間",
                "order_type": "指値注文推奨",
                "entry_price": algo_result['key_levels']['current_price'] * 0.999
            },
            "risk_management": {
                "stop_loss": algo_result['key_levels']['support_1'],
                "take_profit": algo_result['key_levels']['resistance_1'],
                "position_size": "総資金の2%以内"
            },
            "alternative_scenario": "メインシナリオが外れた場合は様子見推奨",
            "time_consideration": {
                "holding_period": "1-3日",
                "market_hours_note": "重要指標発表時は注意"
            },
            "confidence_level": "中～高",
            "additional_notes": f"RSI {algo_result['indicators']['rsi']:.1f}を考慮した戦略"
        }

    def _hybrid_recommendation(self, algo_result: Dict[str, Any], llm_result: Dict[str, Any]) -> Dict[str, Any]:
        """ハイブリッド推奨"""
        return {
            "final_action": algo_result["signal"],
            "confidence": (algo_result["confidence"] + 70) / 2,
            "key_points": [
                f"アルゴリズム: {algo_result['signal']} (信頼度{algo_result['confidence']:.0f}%)",
                f"トレンド: {algo_result['trend']}",
                f"RSI: {algo_result['indicators']['rsi']:.1f}"
            ],
            "execution_plan": {
                "entry": algo_result['key_levels']['current_price'],
                "stop_loss": algo_result['key_levels']['support_1'] if algo_result['signal'] == "BUY" else algo_result['key_levels']['resistance_1'],
                "take_profit": algo_result['key_levels']['resistance_1'] if algo_result['signal'] == "BUY" else algo_result['key_levels']['support_1'],
                "position_size": algo_result['position_size']
            }
        }