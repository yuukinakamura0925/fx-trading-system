"""
マルチタイムフレーム分析システム
長期・中期・短期・超短期の時間軸で総合的なFX戦略を立案

時間軸設定:
- 長期戦略: 日足（スイングトレード、数週間〜数ヶ月）
- 中期戦略: 4時間足（ポジショントレード、数日〜数週間）
- 短期戦略: 1時間足（デイトレード、数時間〜1日）
- 超短期戦略: 5分足（スキャルピング、数分〜数時間）
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import openai
import os
import json

class TimeFrame(Enum):
    """時間軸の定義"""
    ULTRA_SHORT = "5m"    # 超短期: 5分足（スキャルピング）
    SHORT = "1h"          # 短期: 1時間足（デイトレード）
    MEDIUM = "4h"         # 中期: 4時間足（ポジショントレード）
    LONG = "1d"           # 長期: 日足（スイングトレード）

class TradingStyle(Enum):
    """トレードスタイルの定義"""
    SCALPING = "スキャルピング"
    DAY_TRADING = "デイトレード"
    POSITION_TRADING = "ポジショントレード"
    SWING_TRADING = "スイングトレード"

@dataclass
class TimeFrameAnalysis:
    """時間軸別分析結果"""
    timeframe: str
    trading_style: str
    trend: str
    signal: str
    confidence: float
    entry_points: List[Dict]
    key_levels: Dict[str, float]
    risk_reward: float
    volatility: float
    momentum: str

class MultiTimeFrameAnalyzer:
    """マルチタイムフレーム分析クラス"""

    def __init__(self, openai_api_key: Optional[str] = None):
        """
        初期化

        Args:
            openai_api_key: OpenAI APIキー（指定しない場合は環境変数から取得）
        """
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')

        # OpenAI APIキーが設定されている場合はLLM分析を有効化
        # 一時的に無効化（コスト削減のため）
        self.llm_enabled = False  # bool(self.openai_api_key)

        # if self.llm_enabled:
        #     # 新しいOpenAI client初期化
        #     from openai import OpenAI
        #     self.openai_client = OpenAI(api_key=self.openai_api_key)

        # 時間軸設定
        self.timeframes = {
            TimeFrame.ULTRA_SHORT: {
                "period": "1d",
                "interval": "5m",
                "style": TradingStyle.SCALPING,
                "description": "5分足スキャルピング"
            },
            TimeFrame.SHORT: {
                "period": "5d",
                "interval": "1h",
                "style": TradingStyle.DAY_TRADING,
                "description": "1時間足デイトレード"
            },
            TimeFrame.MEDIUM: {
                "period": "1mo",
                "interval": "4h",
                "style": TradingStyle.POSITION_TRADING,
                "description": "4時間足ポジショントレード"
            },
            TimeFrame.LONG: {
                "period": "3mo",
                "interval": "1d",
                "style": TradingStyle.SWING_TRADING,
                "description": "日足スイングトレード"
            }
        }

    def analyze_all_timeframes(self, symbol: str = "USDJPY=X") -> Dict[str, Any]:
        """
        全時間軸での分析を実行

        Args:
            symbol: 通貨ペアシンボル

        Returns:
            マルチタイムフレーム分析結果
        """
        try:
            analyses = {}

            # 各時間軸で分析実行
            for timeframe, config in self.timeframes.items():
                analysis = self._analyze_timeframe(
                    symbol=symbol,
                    timeframe=timeframe,
                    config=config
                )
                analyses[timeframe.value] = analysis

            # 統合戦略を生成
            integrated_strategy = self._generate_integrated_strategy(analyses)

            # 基本結果を作成
            result = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "timeframe_analyses": analyses,
                "integrated_strategy": integrated_strategy,
                "market_session": self._get_current_market_session()
            }

            # LLM分析を追加（APIキーが設定されている場合）
            # 一時的に無効化（コスト削減のため）
            # if self.llm_enabled:
            #     llm_result = self._llm_analysis(result, symbol)
            #     result["llm_analysis"] = llm_result

            return result

        except Exception as e:
            return {"error": str(e)}

    def _analyze_timeframe(self, symbol: str, timeframe: TimeFrame, config: Dict) -> Dict[str, Any]:
        """単一時間軸での分析"""

        # データ取得
        data = yf.download(
            symbol,
            period=config["period"],
            interval=config["interval"],
            progress=False
        )

        if data.empty:
            return {"error": f"データ取得失敗: {timeframe.value}"}

        # MultiIndex対応
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        # 基本分析
        analysis_result = self._perform_technical_analysis(data, timeframe)

        # エントリーポイント探知
        entry_points = self._find_entry_points(data, timeframe, analysis_result)

        # 時間軸特有の戦略
        timeframe_strategy = self._get_timeframe_strategy(timeframe, analysis_result)

        return {
            "timeframe": timeframe.value,
            "trading_style": config["style"].value,
            "description": config["description"],
            "analysis": analysis_result,
            "entry_points": entry_points,
            "strategy": timeframe_strategy,
            "data_points": len(data)
        }

    def _perform_technical_analysis(self, data: pd.DataFrame, timeframe: TimeFrame) -> Dict[str, Any]:
        """テクニカル分析実行"""

        close = data['Close']
        high = data['High']
        low = data['Low']

        # 現在価格
        current_price = float(close.iloc[-1])

        # 移動平均（時間軸に応じて期間調整）
        if timeframe == TimeFrame.ULTRA_SHORT:
            sma_short, sma_long = 5, 20  # 5分足用
        elif timeframe == TimeFrame.SHORT:
            sma_short, sma_long = 10, 25  # 1時間足用
        elif timeframe == TimeFrame.MEDIUM:
            sma_short, sma_long = 12, 26  # 4時間足用
        else:
            sma_short, sma_long = 20, 50  # 日足用

        sma_s = close.rolling(window=sma_short).mean()
        sma_l = close.rolling(window=sma_long).mean()

        current_sma_s = float(sma_s.iloc[-1]) if not pd.isna(sma_s.iloc[-1]) else current_price
        current_sma_l = float(sma_l.iloc[-1]) if not pd.isna(sma_l.iloc[-1]) else current_price

        # RSI（時間軸に応じて期間調整）
        rsi_period = 14 if timeframe != TimeFrame.ULTRA_SHORT else 9
        rsi = self._calculate_rsi(close, rsi_period)
        current_rsi = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50

        # ボラティリティ計算
        returns = close.pct_change()
        volatility = float(returns.std() * 100) if len(returns) > 1 else 0

        # トレンド判定
        trend = self._determine_trend(current_price, current_sma_s, current_sma_l)

        # モメンタム判定
        momentum = self._calculate_momentum(close, timeframe)

        # シグナル生成
        signal_info = self._generate_timeframe_signal(
            current_rsi, trend, momentum, timeframe
        )

        # サポート・レジスタンス
        recent_periods = min(20, len(data))
        recent_high = float(high.tail(recent_periods).max())
        recent_low = float(low.tail(recent_periods).min())

        return {
            "current_price": current_price,
            "trend": trend,
            "signal": signal_info["action"],
            "confidence": signal_info["confidence"],
            "strength": signal_info["strength"],
            "sma_short": current_sma_s,
            "sma_long": current_sma_l,
            "rsi": current_rsi,
            "momentum": momentum,
            "volatility": volatility,
            "key_levels": {
                "resistance": recent_high,
                "support": recent_low,
                "pivot": (recent_high + recent_low + current_price) / 3
            }
        }

    def _find_entry_points(self, data: pd.DataFrame, timeframe: TimeFrame, analysis: Dict) -> List[Dict]:
        """エントリーポイント探知"""

        entry_points = []
        current_price = analysis["current_price"]

        # 時間軸別エントリー戦略
        if timeframe == TimeFrame.ULTRA_SHORT:
            # スキャルピング: 短時間の価格変動を狙う
            entry_points.extend(self._scalping_entry_points(data, analysis))

        elif timeframe == TimeFrame.SHORT:
            # デイトレード: 日中の値動きを狙う
            entry_points.extend(self._daytrading_entry_points(data, analysis))

        elif timeframe == TimeFrame.MEDIUM:
            # ポジショントレード: 数日のトレンドを狙う
            entry_points.extend(self._position_trading_entry_points(data, analysis))

        else:  # LONG
            # スイングトレード: 長期トレンドを狙う
            entry_points.extend(self._swing_trading_entry_points(data, analysis))

        return entry_points

    def _scalping_entry_points(self, data: pd.DataFrame, analysis: Dict) -> List[Dict]:
        """スキャルピング用エントリーポイント"""
        points = []
        current_price = analysis["current_price"]

        # 短期的な押し目・戻りを狙う
        if analysis["signal"] == "BUY":
            points.append({
                "type": "押し目買い",
                "price": current_price * 0.9995,  # 0.05%下
                "stop_loss": current_price * 0.999,   # 0.1%下
                "take_profit": current_price * 1.0015, # 0.15%上
                "timeframe": "1-5分",
                "reason": "短期上昇トレンドの押し目"
            })
        elif analysis["signal"] == "SELL":
            points.append({
                "type": "戻り売り",
                "price": current_price * 1.0005,  # 0.05%上
                "stop_loss": current_price * 1.001,   # 0.1%上
                "take_profit": current_price * 0.9985, # 0.15%下
                "timeframe": "1-5分",
                "reason": "短期下降トレンドの戻り"
            })

        return points

    def _daytrading_entry_points(self, data: pd.DataFrame, analysis: Dict) -> List[Dict]:
        """デイトレード用エントリーポイント"""
        points = []
        current_price = analysis["current_price"]

        # 1時間足のトレンドフォロー
        if analysis["signal"] == "BUY" and analysis["confidence"] > 60:
            points.append({
                "type": "トレンドフォロー買い",
                "price": current_price * 0.999,   # 0.1%下
                "stop_loss": current_price * 0.995,   # 0.5%下
                "take_profit": current_price * 1.01,  # 1%上
                "timeframe": "1-4時間",
                "reason": "1時間足上昇トレンド継続"
            })
        elif analysis["signal"] == "SELL" and analysis["confidence"] > 60:
            points.append({
                "type": "トレンドフォロー売り",
                "price": current_price * 1.001,   # 0.1%上
                "stop_loss": current_price * 1.005,   # 0.5%上
                "take_profit": current_price * 0.99,  # 1%下
                "timeframe": "1-4時間",
                "reason": "1時間足下降トレンド継続"
            })

        return points

    def _position_trading_entry_points(self, data: pd.DataFrame, analysis: Dict) -> List[Dict]:
        """ポジショントレード用エントリーポイント"""
        points = []
        current_price = analysis["current_price"]

        # 4時間足の中期トレンド
        if analysis["signal"] == "BUY":
            points.append({
                "type": "中期トレンド買い",
                "price": current_price * 0.995,   # 0.5%下
                "stop_loss": current_price * 0.985,   # 1.5%下
                "take_profit": current_price * 1.03,  # 3%上
                "timeframe": "3-7日",
                "reason": "4時間足中期上昇トレンド"
            })
        elif analysis["signal"] == "SELL":
            points.append({
                "type": "中期トレンド売り",
                "price": current_price * 1.005,   # 0.5%上
                "stop_loss": current_price * 1.015,   # 1.5%上
                "take_profit": current_price * 0.97,  # 3%下
                "timeframe": "3-7日",
                "reason": "4時間足中期下降トレンド"
            })

        return points

    def _swing_trading_entry_points(self, data: pd.DataFrame, analysis: Dict) -> List[Dict]:
        """スイングトレード用エントリーポイント"""
        points = []
        current_price = analysis["current_price"]

        # 日足の長期トレンド
        if analysis["signal"] == "BUY":
            points.append({
                "type": "長期トレンド買い",
                "price": current_price * 0.99,    # 1%下
                "stop_loss": current_price * 0.97,    # 3%下
                "take_profit": current_price * 1.05,  # 5%上
                "timeframe": "1-4週間",
                "reason": "日足長期上昇トレンド"
            })
        elif analysis["signal"] == "SELL":
            points.append({
                "type": "長期トレンド売り",
                "price": current_price * 1.01,    # 1%上
                "stop_loss": current_price * 1.03,    # 3%上
                "take_profit": current_price * 0.95,  # 5%下
                "timeframe": "1-4週間",
                "reason": "日足長期下降トレンド"
            })

        return points

    def _generate_integrated_strategy(self, analyses: Dict) -> Dict[str, Any]:
        """時間軸統合戦略の生成"""

        # 各時間軸のシグナルを集計
        signals = {}
        confidences = {}

        for timeframe, analysis in analyses.items():
            if "analysis" in analysis:
                signals[timeframe] = analysis["analysis"]["signal"]
                confidences[timeframe] = analysis["analysis"]["confidence"]

        # 重み付けスコア計算（長期 > 中期 > 短期 > 超短期）
        weights = {"1d": 4, "4h": 3, "1h": 2, "5m": 1}

        buy_score = 0
        sell_score = 0
        total_weight = 0

        for timeframe, signal in signals.items():
            weight = weights.get(timeframe, 1)
            confidence = confidences.get(timeframe, 50)

            if signal == "BUY":
                buy_score += weight * confidence
            elif signal == "SELL":
                sell_score += weight * confidence

            total_weight += weight

        # 統合シグナル決定
        if buy_score > sell_score and buy_score > total_weight * 30:
            integrated_signal = "BUY"
            integrated_confidence = min(buy_score / total_weight, 95)
        elif sell_score > buy_score and sell_score > total_weight * 30:
            integrated_signal = "SELL"
            integrated_confidence = min(sell_score / total_weight, 95)
        else:
            integrated_signal = "HOLD"
            integrated_confidence = 40

        # 推奨戦略選択
        recommended_strategies = self._select_recommended_strategies(analyses, integrated_signal)

        return {
            "integrated_signal": integrated_signal,
            "confidence": integrated_confidence,
            "signal_alignment": self._check_signal_alignment(signals),
            "recommended_strategies": recommended_strategies,
            "risk_level": self._assess_overall_risk(analyses),
            "market_timing": self._assess_market_timing()
        }

    def _get_timeframe_strategy(self, timeframe: TimeFrame, analysis: Dict) -> Dict[str, Any]:
        """時間軸特有の戦略を取得"""

        if timeframe == TimeFrame.ULTRA_SHORT:
            return {
                "style": "スキャルピング",
                "holding_period": "1-30分",
                "profit_target": "5-15pips",
                "stop_loss": "3-8pips",
                "frequency": "1日10-50回",
                "best_sessions": ["東京仲値", "ロンドン序盤", "NY序盤"],
                "avoid_times": ["東京昼休み", "欧州昼食", "重要指標前後"]
            }
        elif timeframe == TimeFrame.SHORT:
            return {
                "style": "デイトレード",
                "holding_period": "1-12時間",
                "profit_target": "20-50pips",
                "stop_loss": "15-30pips",
                "frequency": "1日1-5回",
                "best_sessions": ["東京時間", "ロンドン時間", "NY時間"],
                "avoid_times": ["週末クローズ前", "重要指標直前"]
            }
        elif timeframe == TimeFrame.MEDIUM:
            return {
                "style": "ポジショントレード",
                "holding_period": "1-7日",
                "profit_target": "50-150pips",
                "stop_loss": "30-80pips",
                "frequency": "週1-3回",
                "best_sessions": ["週初", "重要指標後"],
                "avoid_times": ["週末", "祝日前"]
            }
        else:  # LONG
            return {
                "style": "スイングトレード",
                "holding_period": "1週間-1ヶ月",
                "profit_target": "100-500pips",
                "stop_loss": "50-200pips",
                "frequency": "月1-4回",
                "best_sessions": ["月初", "四半期末"],
                "avoid_times": ["年末年始", "夏季休暇"]
            }

    def _select_recommended_strategies(self, analyses: Dict, integrated_signal: str) -> List[Dict]:
        """推奨戦略の選択"""
        recommendations = []

        # 各時間軸での強いシグナルを推奨戦略として選択
        for timeframe, analysis in analyses.items():
            if "analysis" in analysis and "entry_points" in analysis:
                if (analysis["analysis"]["signal"] == integrated_signal and
                    analysis["analysis"]["confidence"] > 65):

                    recommendations.append({
                        "timeframe": timeframe,
                        "style": analysis["trading_style"],
                        "confidence": analysis["analysis"]["confidence"],
                        "entry_points": analysis["entry_points"][:2],  # 上位2つ
                        "priority": self._get_strategy_priority(timeframe, analysis["analysis"]["confidence"])
                    })

        # 信頼度順でソート
        recommendations.sort(key=lambda x: x["confidence"], reverse=True)
        return recommendations[:3]  # 上位3つの戦略

    def _get_strategy_priority(self, timeframe: str, confidence: float) -> str:
        """戦略の優先度を決定"""
        if confidence > 80:
            return "高"
        elif confidence > 65:
            return "中"
        else:
            return "低"

    def _check_signal_alignment(self, signals: Dict) -> str:
        """シグナルの一致度をチェック"""
        buy_count = sum(1 for s in signals.values() if s == "BUY")
        sell_count = sum(1 for s in signals.values() if s == "SELL")
        total = len(signals)

        if buy_count >= total * 0.75:
            return "強い買い合意"
        elif sell_count >= total * 0.75:
            return "強い売り合意"
        elif buy_count > sell_count:
            return "買い優勢"
        elif sell_count > buy_count:
            return "売り優勢"
        else:
            return "方向感なし"

    def _assess_overall_risk(self, analyses: Dict) -> str:
        """総合リスクレベルの評価"""
        volatilities = []
        for analysis in analyses.values():
            if "analysis" in analysis:
                volatilities.append(analysis["analysis"]["volatility"])

        if not volatilities:
            return "不明"

        avg_volatility = sum(volatilities) / len(volatilities)

        if avg_volatility > 2.0:
            return "高"
        elif avg_volatility > 1.0:
            return "中"
        else:
            return "低"

    def _assess_market_timing(self) -> Dict[str, str]:
        """市場タイミングの評価"""
        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()

        # 市場セッション判定
        if 0 <= hour < 7:
            session = "ウェリントン/シドニー"
            activity = "低"
        elif 7 <= hour < 15:
            session = "東京"
            activity = "中"
        elif 15 <= hour < 21:
            session = "ロンドン"
            activity = "高"
        else:
            session = "ニューヨーク"
            activity = "高"

        # 週のタイミング
        if weekday in [0, 1]:
            week_timing = "週初（方向性不明）"
        elif weekday in [2, 3]:
            week_timing = "週中（トレンド継続）"
        else:
            week_timing = "週末（ポジション調整）"

        return {
            "current_session": session,
            "activity_level": activity,
            "week_timing": week_timing,
            "recommendation": self._get_timing_recommendation(session, weekday)
        }

    def _get_timing_recommendation(self, session: str, weekday: int) -> str:
        """タイミング推奨"""
        if session in ["ロンドン", "ニューヨーク"] and weekday in [1, 2, 3]:
            return "積極的トレード推奨"
        elif session == "東京" and weekday in [1, 2]:
            return "慎重なトレード推奨"
        else:
            return "様子見推奨"

    def _get_current_market_session(self) -> Dict[str, str]:
        """現在の市場セッション情報"""
        now = datetime.now()
        hour = now.hour

        sessions = {
            "tokyo": {"start": 9, "end": 15, "name": "東京市場"},
            "london": {"start": 16, "end": 1, "name": "ロンドン市場"},
            "newyork": {"start": 22, "end": 5, "name": "ニューヨーク市場"}
        }

        active_sessions = []
        for session_id, info in sessions.items():
            if info["start"] <= hour or hour <= info["end"]:
                active_sessions.append(info["name"])

        return {
            "active_sessions": active_sessions,
            "optimal_for": "デイトレード" if len(active_sessions) >= 2 else "スキャルピング"
        }

    # 共通のヘルパーメソッド
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """RSI計算"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _determine_trend(self, price: float, sma_short: float, sma_long: float) -> str:
        """トレンド判定"""
        if sma_short > sma_long and price > sma_short:
            return "強い上昇"
        elif sma_short > sma_long:
            return "上昇"
        elif sma_short < sma_long and price < sma_short:
            return "強い下降"
        elif sma_short < sma_long:
            return "下降"
        else:
            return "レンジ"

    def _calculate_momentum(self, close: pd.Series, timeframe: TimeFrame) -> str:
        """モメンタム計算"""
        if len(close) < 10:
            return "不明"

        # 直近の価格変化率
        periods = 5 if timeframe == TimeFrame.ULTRA_SHORT else 10
        change = (close.iloc[-1] - close.iloc[-periods]) / close.iloc[-periods] * 100

        if change > 1:
            return "強い"
        elif change > 0.2:
            return "やや強い"
        elif change > -0.2:
            return "中立"
        elif change > -1:
            return "やや弱い"
        else:
            return "弱い"

    def _generate_timeframe_signal(self, rsi: float, trend: str, momentum: str, timeframe: TimeFrame) -> Dict:
        """時間軸別シグナル生成"""
        confidence = 50.0
        strength = "中程度"

        # 基本的なシグナル判定
        if "上昇" in trend and rsi < 70:
            action = "BUY"
            confidence = 70.0
            if momentum in ["強い", "やや強い"]:
                confidence += 10
            strength = "強い" if confidence > 75 else "中程度"
        elif "下降" in trend and rsi > 30:
            action = "SELL"
            confidence = 70.0
            if momentum in ["弱い", "やや弱い"]:
                confidence += 10
            strength = "強い" if confidence > 75 else "中程度"
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

        # 時間軸による信頼度調整
        if timeframe == TimeFrame.LONG:
            confidence *= 1.1  # 長期は信頼度高
        elif timeframe == TimeFrame.ULTRA_SHORT:
            confidence *= 0.9  # 超短期は信頼度やや低

        return {
            "action": action,
            "confidence": min(confidence, 95),
            "strength": strength
        }

    def _llm_analysis(self, algorithmic_results: Dict, symbol: str) -> Dict[str, Any]:
        """
        OpenAI APIを使用したLLM分析

        Args:
            algorithmic_results: アルゴリズム分析結果
            symbol: 通貨ペアシンボル

        Returns:
            LLM分析結果
        """
        if not self.llm_enabled:
            return {"error": "OpenAI APIキーが設定されていません"}

        try:
            # アルゴリズム結果の要約
            timeframe_summaries = []
            for tf, analysis in algorithmic_results.get("timeframe_analyses", {}).items():
                timeframe_summaries.append(
                    f"{tf}({analysis['description']}): {analysis['analysis']['signal']} "
                    f"信頼度{analysis['analysis']['confidence']:.0f}%, "
                    f"トレンド: {analysis['analysis']['trend']}, "
                    f"RSI: {analysis['analysis']['rsi']:.1f}"
                )

            # 統合戦略情報
            integrated = algorithmic_results.get("integrated_strategy", {})

            # プロンプト作成
            prompt = f"""
あなたは経験豊富なFXトレーダーです。以下の技術分析結果を基に、市場心理と戦略的な洞察を提供してください。

## 通貨ペア: {symbol}
## 分析時刻: {algorithmic_results.get('timestamp', '')}

## 技術分析結果:
{chr(10).join(timeframe_summaries)}

## 統合判断:
- 統合シグナル: {integrated.get('integrated_signal', 'N/A')}
- 信頼度: {integrated.get('confidence', 0):.1f}%
- リスクレベル: {integrated.get('risk_level', 'N/A')}
- 現在セッション: {integrated.get('market_timing', {}).get('current_session', 'N/A')}

以下の観点で分析してください:

1. **市場心理の解釈**: なぜこのような技術的シグナルが発生しているか
2. **ファンダメンタル要因**: 経済指標や地政学的要因で注意すべき点
3. **リスク要因**: 想定外の動きが起こる可能性とその理由
4. **戦略的提案**: より具体的なエントリー・エグジット戦略
5. **代替シナリオ**: メインシナリオが外れた場合の対応

簡潔で実用的なアドバイスを日本語で提供してください。
"""

            # OpenAI API呼び出し（新しいインターフェース）
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # より安価で利用可能なモデル
                messages=[
                    {"role": "system", "content": "あなたは経験豊富なFXトレーダーとして、技術分析に基づいた実用的なアドバイスを提供します。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )

            llm_analysis = response.choices[0].message.content

            # 構造化された結果を返す
            return {
                "llm_analysis": llm_analysis,
                "market_psychology": self._extract_market_psychology(llm_analysis),
                "risk_factors": self._extract_risk_factors(llm_analysis),
                "strategic_recommendations": self._extract_strategic_recommendations(llm_analysis),
                "alternative_scenarios": self._extract_alternative_scenarios(llm_analysis),
                "confidence_assessment": "高" if integrated.get('confidence', 0) > 70 else "中" if integrated.get('confidence', 0) > 50 else "低"
            }

        except Exception as e:
            return {
                "error": f"LLM分析エラー: {str(e)}",
                "fallback_analysis": "アルゴリズム分析のみでの判断をお勧めします"
            }

    def _extract_market_psychology(self, analysis: str) -> str:
        """市場心理の抽出"""
        lines = analysis.split('\n')
        for i, line in enumerate(lines):
            if '市場心理' in line or '心理' in line:
                # 次の数行を取得
                psychology_lines = lines[i:i+3]
                return ' '.join([l.strip() for l in psychology_lines if l.strip()])
        return "市場参加者の心理状況を注視する必要があります。"

    def _extract_risk_factors(self, analysis: str) -> List[str]:
        """リスク要因の抽出"""
        lines = analysis.split('\n')
        risk_factors = []
        capture_risks = False

        for line in lines:
            if 'リスク' in line or '注意' in line:
                capture_risks = True
                continue
            if capture_risks and line.strip():
                if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                    risk_factors.append(line.strip())
                elif len(risk_factors) > 0:
                    break

        return risk_factors if risk_factors else ["市場のボラティリティに注意"]

    def _extract_strategic_recommendations(self, analysis: str) -> List[str]:
        """戦略的推奨の抽出"""
        lines = analysis.split('\n')
        recommendations = []
        capture_strategy = False

        for line in lines:
            if '戦略' in line or '提案' in line or '推奨' in line:
                capture_strategy = True
                continue
            if capture_strategy and line.strip():
                if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                    recommendations.append(line.strip())
                elif len(recommendations) > 0:
                    break

        return recommendations if recommendations else ["テクニカル分析に基づいた慎重な取引を推奨"]

    def _extract_alternative_scenarios(self, analysis: str) -> str:
        """代替シナリオの抽出"""
        lines = analysis.split('\n')
        for i, line in enumerate(lines):
            if '代替' in line or 'シナリオ' in line or '外れた場合' in line:
                # 次の数行を取得
                scenario_lines = lines[i:i+3]
                return ' '.join([l.strip() for l in scenario_lines if l.strip()])
        return "メインシナリオが外れた場合は、損切りを徹底し、新たな分析を行ってください。"