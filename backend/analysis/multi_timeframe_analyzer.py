"""
マルチタイムフレーム分析システム
長期・中期・短期・超短期の時間軸で総合的なFX戦略を立案

時間軸設定:
- 長期戦略: 日足（スイングトレード、数週間〜数ヶ月）
- 中期戦略: 4時間足（ポジショントレード、数日〜数週間）
- 短期戦略: 1時間足（デイトレード、数時間〜1日）
- 超短期戦略: 5分足（スキャルピング、数分〜数時間）
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import os
import json
from .gmo_client import GMOFXClient

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

        # GMO APIクライアント初期化
        self.gmo_client = GMOFXClient()

        # if self.llm_enabled:
        #     # 新しいOpenAI client初期化
        #     from openai import OpenAI
        #     self.openai_client = OpenAI(api_key=self.openai_api_key)

        # 時間軸設定（GMO APIの取得可能範囲に合わせて調整）
        self.timeframes = {
            TimeFrame.ULTRA_SHORT: {
                "days": 1,           # 1日分
                "interval": "5m",
                "style": TradingStyle.SCALPING,
                "description": "5分足スキャルピング"
            },
            TimeFrame.SHORT: {
                "days": 5,           # 5日分
                "interval": "1h",
                "style": TradingStyle.DAY_TRADING,
                "description": "1時間足デイトレード"
            },
            TimeFrame.MEDIUM: {
                "days": 7,           # 7日分（GMO API制限対策）
                "interval": "4h",
                "style": TradingStyle.POSITION_TRADING,
                "description": "4時間足ポジショントレード"
            },
            TimeFrame.LONG: {
                "days": 10,          # 10日分（GMO API制限対策）
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
        """単一時間軸での分析（GMO API使用）"""

        import logging
        logger = logging.getLogger(__name__)

        try:
            # シンボル変換（USDJPY=X -> USD_JPY）
            gmo_symbol = symbol.replace("=X", "").replace("JPY", "_JPY").replace("USD", "USD")
            if "_" not in gmo_symbol:
                gmo_symbol = f"{gmo_symbol[:3]}_{gmo_symbol[3:]}"

            logger.info(f"データ取得開始: {gmo_symbol} {timeframe.value} (days={config['days']}, interval={config['interval']})")

            # GMO APIからデータ取得
            data = self.gmo_client.get_klines_multi_days(
                symbol=gmo_symbol,
                interval=config["interval"],
                days=config["days"],
                price_type="ASK"
            )

            logger.info(f"データ取得完了: {gmo_symbol} {timeframe.value} - {len(data)} rows")

            if data.empty:
                return {
                    "error": f"データ取得失敗: {timeframe.value}",
                    "details": f"GMO APIからデータを取得できませんでした (symbol={gmo_symbol}, days={config['days']}, interval={config['interval']})"
                }

        except Exception as e:
            # 例外が発生した場合
            logger.error(f"データ取得例外: {symbol} {timeframe.value} - {str(e)}")
            return {
                "error": f"データ取得エラー: {timeframe.value}",
                "details": str(e)
            }

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

    def _format_patterns(self, patterns: List) -> List[Dict]:
        """パターン情報をJSON形式にフォーマット"""
        formatted = []
        for pattern in patterns[:3]:  # 上位3パターンのみ
            formatted.append({
                "type": pattern.type.value,
                "confidence": pattern.confidence,
                "prediction": pattern.prediction,
                "target_price": pattern.target_price,
                "stop_loss": pattern.stop_loss,
                "description": pattern.description,
                "key_levels": pattern.key_levels
            })
        return formatted

    def _predict_next_move(self, analysis: Dict, patterns: List, timeframe: TimeFrame) -> Dict[str, Any]:
        """
        次の動きを予測（パターン + テクニカル指標の統合分析）

        Args:
            analysis: テクニカル分析結果
            patterns: 検出されたチャートパターン
            timeframe: 時間軸

        Returns:
            次の動き予測情報
        """

        current_price = analysis["current_price"]
        trend = analysis["trend"]
        rsi = analysis["rsi"]
        signal = analysis["signal"]
        confidence = analysis["confidence"]

        # 時間軸ごとの予測期間と期待変動幅
        timeframe_config = {
            TimeFrame.ULTRA_SHORT: {
                "period": "今後15-30分",
                "expected_move_pct": 0.1,  # 0.1%
                "volatility_factor": 1.5
            },
            TimeFrame.SHORT: {
                "period": "今後2-4時間",
                "expected_move_pct": 0.3,  # 0.3%
                "volatility_factor": 1.2
            },
            TimeFrame.MEDIUM: {
                "period": "今後12-24時間",
                "expected_move_pct": 0.8,  # 0.8%
                "volatility_factor": 1.0
            },
            TimeFrame.LONG: {
                "period": "今後3-7日",
                "expected_move_pct": 2.0,  # 2%
                "volatility_factor": 0.8
            }
        }

        config = timeframe_config[timeframe]
        period_text = config["period"]
        base_move_pct = config["expected_move_pct"]

        # === パターンベースの予測 ===
        pattern_predictions = []
        pattern_bias = "中立"  # 上昇 / 下降 / 中立
        pattern_target = None
        pattern_confidence_boost = 0

        if patterns:
            # 信頼度の高いパターンから分析
            top_patterns = sorted(patterns, key=lambda p: p.confidence, reverse=True)[:2]

            for pattern in top_patterns:
                pred_direction = "上昇" if "上昇" in pattern.prediction or "買い" in pattern.prediction or "反発" in pattern.prediction else \
                                 "下降" if "下降" in pattern.prediction or "売り" in pattern.prediction or "反落" in pattern.prediction else \
                                 "様子見"

                pattern_predictions.append({
                    "pattern_name": pattern.type.value,
                    "direction": pred_direction,
                    "confidence": pattern.confidence,
                    "target": pattern.target_price,
                    "reason": pattern.description
                })

                # パターンの方向性を判定（最も信頼度の高いパターンを採用）
                if pattern == top_patterns[0]:
                    pattern_bias = pred_direction
                    pattern_target = pattern.target_price
                    # パターン信頼度が高い場合、全体の信頼度をブースト
                    if pattern.confidence > 75:
                        pattern_confidence_boost = 10
                    elif pattern.confidence > 65:
                        pattern_confidence_boost = 5

        # === テクニカル指標ベースの予測 ===
        # 1. 基本方向性の決定（パターンとシグナルの統合）
        if pattern_bias == "上昇" and signal == "BUY":
            final_direction = "上昇"
            direction_confidence = min(100, confidence + pattern_confidence_boost + 10)  # 一致でブースト
        elif pattern_bias == "下降" and signal == "SELL":
            final_direction = "下降"
            direction_confidence = min(100, confidence + pattern_confidence_boost + 10)
        elif pattern_bias != "中立" and pattern_bias != "様子見":
            # パターンとシグナルが不一致の場合
            final_direction = pattern_bias  # パターンを優先
            direction_confidence = max(40, confidence - 10)  # 信頼度は下げる
        elif signal == "BUY":
            final_direction = "上昇"
            direction_confidence = confidence
        elif signal == "SELL":
            final_direction = "下降"
            direction_confidence = confidence
        else:
            final_direction = "横ばい"
            direction_confidence = confidence

        # 2. 目標価格の計算
        if pattern_target:
            # パターンの目標価格を優先
            target_price = pattern_target
        else:
            # テクニカル指標から算出
            if final_direction == "上昇":
                target_price = current_price * (1 + base_move_pct / 100)
            elif final_direction == "下降":
                target_price = current_price * (1 - base_move_pct / 100)
            else:
                target_price = current_price

        # 3. サポート/レジスタンスレベル
        if final_direction == "上昇":
            support_level = current_price * (1 - base_move_pct / 200)  # 半分の変動幅
            resistance_level = target_price * 1.001
        elif final_direction == "下降":
            support_level = target_price * 0.999
            resistance_level = current_price * (1 + base_move_pct / 200)
        else:
            support_level = current_price * 0.998
            resistance_level = current_price * 1.002

        # 4. RSIとトレンドからの追加洞察
        rsi_insight = ""
        if rsi > 70:
            rsi_insight = "⚠️ RSI過熱（70超）: 調整の可能性あり"
            if final_direction == "上昇":
                rsi_insight += "。上昇継続には強い買い圧力が必要"
        elif rsi < 30:
            rsi_insight = "⚠️ RSI売られすぎ（30未満）: 反発の可能性あり"
            if final_direction == "下降":
                rsi_insight += "。下落継続には強い売り圧力が必要"
        elif 45 <= rsi <= 55:
            rsi_insight = "RSI中立（45-55）: 明確な方向感なし"
        else:
            rsi_insight = f"RSI {rsi:.1f}: 健全な水準"

        trend_insight = ""
        if trend == "上昇":
            if final_direction == "上昇":
                trend_insight = "✅ トレンドフォロー: 上昇トレンド継続中"
            elif final_direction == "下降":
                trend_insight = "⚠️ トレンド転換の兆候: 上昇→下降へ転換の可能性"
            else:
                trend_insight = "上昇トレンド中の調整局面"
        elif trend == "下降":
            if final_direction == "下降":
                trend_insight = "✅ トレンドフォロー: 下降トレンド継続中"
            elif final_direction == "上昇":
                trend_insight = "⚠️ トレンド転換の兆候: 下降→上昇へ転換の可能性"
            else:
                trend_insight = "下降トレンド中の調整局面"
        else:  # レンジ
            trend_insight = "📊 レンジ相場: ブレイクアウト待ち"

        # 5. 信頼度レベルの文字列化
        if direction_confidence > 75:
            confidence_text = "高"
            confidence_emoji = "🟢"
        elif direction_confidence > 55:
            confidence_text = "中"
            confidence_emoji = "🟡"
        else:
            confidence_text = "低"
            confidence_emoji = "🔴"

        # 6. 総合サマリーの生成
        summary_parts = [
            f"{period_text}は{final_direction}方向",
            f"目標{target_price:.3f}付近",
            f"信頼度{direction_confidence:.0f}%（{confidence_text}）"
        ]

        if pattern_predictions:
            summary_parts.append(f"パターン: {pattern_predictions[0]['pattern_name']}")

        summary = "。".join(summary_parts)

        # 7. シナリオ分析（複数のシナリオ提示）
        scenarios = []

        # メインシナリオ
        scenarios.append({
            "name": "メインシナリオ",
            "probability": direction_confidence,
            "direction": final_direction,
            "target": round(target_price, 3),
            "description": f"{final_direction}トレンド継続。{target_price:.3f}を目指す展開"
        })

        # 代替シナリオ（逆方向）
        if final_direction == "上昇":
            alt_direction = "下降"
            alt_target = current_price * (1 - base_move_pct / 100)
            alt_probability = 100 - direction_confidence
        elif final_direction == "下降":
            alt_direction = "上昇"
            alt_target = current_price * (1 + base_move_pct / 100)
            alt_probability = 100 - direction_confidence
        else:
            alt_direction = "ブレイクアウト"
            alt_target = current_price
            alt_probability = 40

        scenarios.append({
            "name": "代替シナリオ",
            "probability": alt_probability,
            "direction": alt_direction,
            "target": round(alt_target, 3),
            "description": f"予想外の{alt_direction}。{alt_target:.3f}方向への動き"
        })

        # 結果を返す
        return {
            "direction": final_direction,
            "confidence": round(direction_confidence, 1),
            "confidence_level": confidence_text,
            "confidence_emoji": confidence_emoji,
            "period": period_text,
            "current_price": round(current_price, 3),
            "target_price": round(target_price, 3),
            "support_level": round(support_level, 3),
            "resistance_level": round(resistance_level, 3),
            "expected_move_pct": base_move_pct,
            "rsi_insight": rsi_insight,
            "trend_insight": trend_insight,
            "pattern_insights": pattern_predictions,
            "scenarios": scenarios,
            "summary": summary
        }

    def _evaluate_with_strategies(
        self,
        analysis: Dict[str, Any],
        patterns: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        全ての登録戦略でシグナルを評価

        Args:
            analysis: テクニカル分析結果
            patterns: 検出されたパターン

        Returns:
            各戦略での評価結果リスト
        """

        evaluations = []

        # 全戦略を評価
        for strategy_name in strategy_engine.strategies.keys():
            evaluation = strategy_engine.evaluate_signal(
                strategy_name,
                analysis,
                patterns
            )

            # エラーがなければ追加
            if "error" not in evaluation:
                evaluations.append({
                    "strategy_name": strategy_name,
                    "should_enter": evaluation["should_enter"],
                    "signal": evaluation["signal"],
                    "strength": evaluation["strength"].name if hasattr(evaluation["strength"], "name") else str(evaluation["strength"]),
                    "confidence": evaluation["confidence"],
                    "reasons": evaluation["reasons"],
                    "warnings": evaluation["warnings"],
                    "risk_management": {
                        "entry_price": evaluation.get("entry_price"),
                        "stop_loss": evaluation.get("stop_loss"),
                        "take_profit": evaluation.get("take_profit")
                    } if evaluation["should_enter"] else None
                })

        # エントリー推奨順にソート
        evaluations.sort(
            key=lambda x: (x["should_enter"], x["confidence"]),
            reverse=True
        )

        return evaluations

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
        """
        時間軸別シグナル生成（改善版）
        複数指標を組み合わせた信頼度計算
        """
        # 指標別スコア計算
        scores = {
            'trend': 0,      # トレンド方向スコア
            'rsi': 0,        # RSI位置スコア
            'momentum': 0,   # モメンタムスコア
            'confluence': 0  # 指標一致度スコア
        }

        # 1. トレンド分析
        if "強い上昇" in trend:
            scores['trend'] = 30
            base_action = "BUY"
        elif "上昇" in trend:
            scores['trend'] = 20
            base_action = "BUY"
        elif "強い下降" in trend:
            scores['trend'] = 30
            base_action = "SELL"
        elif "下降" in trend:
            scores['trend'] = 20
            base_action = "SELL"
        else:
            scores['trend'] = 0
            base_action = "HOLD"

        # 2. RSI分析（買われすぎ・売られすぎ）
        if rsi < 30:  # 売られすぎ → 買いシグナル
            scores['rsi'] = 25
            rsi_action = "BUY"
        elif rsi < 40:
            scores['rsi'] = 15
            rsi_action = "BUY"
        elif rsi > 70:  # 買われすぎ → 売りシグナル
            scores['rsi'] = 25
            rsi_action = "SELL"
        elif rsi > 60:
            scores['rsi'] = 15
            rsi_action = "SELL"
        else:  # 中立
            scores['rsi'] = 5
            rsi_action = "HOLD"

        # 3. モメンタム分析
        if momentum in ["強い", "やや強い"]:
            scores['momentum'] = 20
        elif momentum in ["弱い", "やや弱い"]:
            scores['momentum'] = 20
        else:
            scores['momentum'] = 5

        # 4. 指標の一致度（confluence）チェック
        signals = [base_action, rsi_action]
        if base_action == rsi_action and base_action != "HOLD":
            scores['confluence'] = 25  # 指標が一致
        elif base_action != "HOLD" and rsi_action == "HOLD":
            scores['confluence'] = 10  # 部分一致
        else:
            scores['confluence'] = 0   # 不一致

        # 最終アクション決定（多数決）
        buy_count = signals.count("BUY")
        sell_count = signals.count("SELL")

        if buy_count > sell_count:
            final_action = "BUY"
        elif sell_count > buy_count:
            final_action = "SELL"
        else:
            final_action = "HOLD"

        # 信頼度計算（0-100）
        raw_confidence = sum(scores.values())

        # 時間軸による重み付け
        if timeframe == TimeFrame.LONG:
            raw_confidence *= 1.15  # 長期: +15%
        elif timeframe == TimeFrame.MEDIUM:
            raw_confidence *= 1.05  # 中期: +5%
        elif timeframe == TimeFrame.ULTRA_SHORT:
            raw_confidence *= 0.85  # 超短期: -15%

        confidence = min(raw_confidence, 95)  # 最大95%

        # 強度判定
        if confidence >= 75:
            strength = "強い"
        elif confidence >= 55:
            strength = "中程度"
        else:
            strength = "弱い"

        return {
            "action": final_action,
            "confidence": confidence,
            "strength": strength,
            "scores": scores  # デバッグ用
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