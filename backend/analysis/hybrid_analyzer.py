"""
ハイブリッド為替分析システム
アルゴリズムベース分析とLLM分析の両方を提供

1. アルゴリズム分析: テクニカル指標を使った定量的分析
2. LLM分析: ChatGPT/Claude APIを使った定性的分析
3. ハイブリッド: 両方の結果を統合した総合判断
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import os

# テクニカル分析ライブラリ（talib代替の軽量版）
class TechnicalIndicators:
    """テクニカル指標計算クラス"""

    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        """単純移動平均"""
        return data.rolling(window=period).mean()

    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """指数移動平均"""
        return data.ewm(span=period, adjust=False).mean()

    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """RSI（相対力指数）"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def macd(data: pd.Series) -> Dict[str, pd.Series]:
        """MACD"""
        ema12 = data.ewm(span=12, adjust=False).mean()
        ema26 = data.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }

    @staticmethod
    def bollinger_bands(data: pd.Series, period: int = 20, std_dev: int = 2) -> Dict[str, pd.Series]:
        """ボリンジャーバンド"""
        middle = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return {
            'upper': upper,
            'middle': middle,
            'lower': lower
        }

    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Dict[str, pd.Series]:
        """ストキャスティクス"""
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=3).mean()
        return {
            'k': k_percent,
            'd': d_percent
        }


class TrendDirection(Enum):
    """トレンド方向の列挙型"""
    STRONG_UP = "強い上昇トレンド"
    UP = "上昇トレンド"
    NEUTRAL = "横ばい"
    DOWN = "下降トレンド"
    STRONG_DOWN = "強い下降トレンド"


class SignalStrength(Enum):
    """シグナル強度の列挙型"""
    VERY_STRONG = "非常に強い"
    STRONG = "強い"
    MODERATE = "中程度"
    WEAK = "弱い"
    VERY_WEAK = "非常に弱い"


@dataclass
class AlgorithmicAnalysis:
    """アルゴリズム分析結果"""
    trend_direction: TrendDirection
    signal_strength: SignalStrength
    entry_signal: str  # BUY/SELL/HOLD
    confidence: float  # 0-100%
    key_levels: Dict[str, float]  # サポート、レジスタンスなど
    indicators: Dict[str, float]  # 各種指標の現在値
    risk_reward_ratio: float
    suggested_position_size: float  # 推奨ポジションサイズ（%）
    analysis_summary: str


class AlgorithmicAnalyzer:
    """アルゴリズムベースの為替分析エンジン"""

    def __init__(self):
        self.indicators = TechnicalIndicators()

    def analyze(self, symbol: str = "USDJPY=X", period: str = "3mo") -> AlgorithmicAnalysis:
        """
        アルゴリズムによる分析実行

        Args:
            symbol: 通貨ペアシンボル
            period: 分析期間

        Returns:
            分析結果
        """
        # データ取得
        data = self._fetch_data(symbol, period)

        if data.empty:
            raise ValueError(f"データ取得失敗: {symbol}")

        # テクニカル指標を計算
        indicators = self._calculate_indicators(data)

        # トレンド判定
        trend = self._determine_trend(data, indicators)

        # エントリーシグナル生成
        signal = self._generate_signal(data, indicators, trend)

        # キーレベル（サポート・レジスタンス）を計算
        key_levels = self._calculate_key_levels(data)

        # リスクリワード比計算
        risk_reward = self._calculate_risk_reward(data, signal, key_levels)

        # ポジションサイズ計算
        position_size = self._calculate_position_size(indicators, trend)

        # サマリー生成
        summary = self._generate_algorithm_summary(trend, signal, indicators)

        return AlgorithmicAnalysis(
            trend_direction=trend,
            signal_strength=signal['strength'],
            entry_signal=signal['action'],
            confidence=signal['confidence'],
            key_levels=key_levels,
            indicators=indicators['current_values'],
            risk_reward_ratio=risk_reward,
            suggested_position_size=position_size,
            analysis_summary=summary
        )

    def _fetch_data(self, symbol: str, period: str) -> pd.DataFrame:
        """データ取得"""
        data = yf.download(symbol, period=period, interval="1d", progress=False)

        # データが空の場合の処理
        if data.empty:
            raise ValueError(f"データが取得できません: {symbol}")

        return data

    def _calculate_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """全テクニカル指標を計算"""
        close = data['Close']
        high = data['High']
        low = data['Low']

        # 移動平均
        sma20 = self.indicators.sma(close, 20)
        sma50 = self.indicators.sma(close, 50)
        ema20 = self.indicators.ema(close, 20)

        # RSI
        rsi = self.indicators.rsi(close)

        # MACD
        macd_data = self.indicators.macd(close)

        # ボリンジャーバンド
        bb_data = self.indicators.bollinger_bands(close)

        # ストキャスティクス
        stoch_data = self.indicators.stochastic(high, low, close)

        # 現在値を取得（.iloc[0]を使ってSeriesエラーを回避）
        current_values = {
            'price': float(close.iloc[-1].iloc[0]) if hasattr(close.iloc[-1], 'iloc') else float(close.iloc[-1]),
            'sma20': float(sma20.iloc[-1].iloc[0]) if hasattr(sma20.iloc[-1], 'iloc') and not pd.isna(sma20.iloc[-1].iloc[0]) else (float(sma20.iloc[-1]) if not pd.isna(sma20.iloc[-1]) else 0),
            'sma50': float(sma50.iloc[-1].iloc[0]) if hasattr(sma50.iloc[-1], 'iloc') and not pd.isna(sma50.iloc[-1].iloc[0]) else (float(sma50.iloc[-1]) if not pd.isna(sma50.iloc[-1]) else 0),
            'ema20': float(ema20.iloc[-1].iloc[0]) if hasattr(ema20.iloc[-1], 'iloc') and not pd.isna(ema20.iloc[-1].iloc[0]) else (float(ema20.iloc[-1]) if not pd.isna(ema20.iloc[-1]) else 0),
            'rsi': float(rsi.iloc[-1].iloc[0]) if hasattr(rsi.iloc[-1], 'iloc') and not pd.isna(rsi.iloc[-1].iloc[0]) else (float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50),
            'macd': float(macd_data['macd'].iloc[-1].iloc[0]) if hasattr(macd_data['macd'].iloc[-1], 'iloc') and not pd.isna(macd_data['macd'].iloc[-1].iloc[0]) else (float(macd_data['macd'].iloc[-1]) if not pd.isna(macd_data['macd'].iloc[-1]) else 0),
            'macd_signal': float(macd_data['signal'].iloc[-1].iloc[0]) if hasattr(macd_data['signal'].iloc[-1], 'iloc') and not pd.isna(macd_data['signal'].iloc[-1].iloc[0]) else (float(macd_data['signal'].iloc[-1]) if not pd.isna(macd_data['signal'].iloc[-1]) else 0),
            'bb_upper': float(bb_data['upper'].iloc[-1].iloc[0]) if hasattr(bb_data['upper'].iloc[-1], 'iloc') and not pd.isna(bb_data['upper'].iloc[-1].iloc[0]) else (float(bb_data['upper'].iloc[-1]) if not pd.isna(bb_data['upper'].iloc[-1]) else 0),
            'bb_lower': float(bb_data['lower'].iloc[-1].iloc[0]) if hasattr(bb_data['lower'].iloc[-1], 'iloc') and not pd.isna(bb_data['lower'].iloc[-1].iloc[0]) else (float(bb_data['lower'].iloc[-1]) if not pd.isna(bb_data['lower'].iloc[-1]) else 0),
            'stoch_k': float(stoch_data['k'].iloc[-1].iloc[0]) if hasattr(stoch_data['k'].iloc[-1], 'iloc') and not pd.isna(stoch_data['k'].iloc[-1].iloc[0]) else (float(stoch_data['k'].iloc[-1]) if not pd.isna(stoch_data['k'].iloc[-1]) else 50),
            'stoch_d': float(stoch_data['d'].iloc[-1].iloc[0]) if hasattr(stoch_data['d'].iloc[-1], 'iloc') and not pd.isna(stoch_data['d'].iloc[-1].iloc[0]) else (float(stoch_data['d'].iloc[-1]) if not pd.isna(stoch_data['d'].iloc[-1]) else 50),
        }

        return {
            'current_values': current_values,
            'series': {
                'sma20': sma20,
                'sma50': sma50,
                'ema20': ema20,
                'rsi': rsi,
                'macd': macd_data,
                'bb': bb_data,
                'stoch': stoch_data
            }
        }

    def _determine_trend(self, data: pd.DataFrame, indicators: Dict) -> TrendDirection:
        """トレンド判定ロジック"""
        current = indicators['current_values']

        # 移動平均のクロス判定
        ma_score = 0
        if current['sma20'] > current['sma50']:
            ma_score += 2
        if current['price'] > current['sma20']:
            ma_score += 1
        if current['price'] > current['sma50']:
            ma_score += 1

        # MACD判定
        macd_score = 0
        if current['macd'] > current['macd_signal']:
            macd_score += 2
        if current['macd'] > 0:
            macd_score += 1

        # 総合スコア
        total_score = ma_score + macd_score

        if total_score >= 6:
            return TrendDirection.STRONG_UP
        elif total_score >= 4:
            return TrendDirection.UP
        elif total_score >= 3:
            return TrendDirection.NEUTRAL
        elif total_score >= 1:
            return TrendDirection.DOWN
        else:
            return TrendDirection.STRONG_DOWN

    def _generate_signal(self, data: pd.DataFrame, indicators: Dict, trend: TrendDirection) -> Dict:
        """エントリーシグナル生成"""
        current = indicators['current_values']

        # シグナルスコア計算
        buy_score = 0
        sell_score = 0

        # RSIによる判定
        if current['rsi'] < 30:  # 売られすぎ
            buy_score += 3
        elif current['rsi'] < 40:
            buy_score += 1
        elif current['rsi'] > 70:  # 買われすぎ
            sell_score += 3
        elif current['rsi'] > 60:
            sell_score += 1

        # ストキャスティクスによる判定
        if current['stoch_k'] < 20:
            buy_score += 2
        elif current['stoch_k'] > 80:
            sell_score += 2

        # ボリンジャーバンドによる判定
        bb_position = (current['price'] - current['bb_lower']) / (current['bb_upper'] - current['bb_lower'])
        if bb_position < 0.2:  # 下部バンド付近
            buy_score += 2
        elif bb_position > 0.8:  # 上部バンド付近
            sell_score += 2

        # トレンドとの整合性
        if trend in [TrendDirection.STRONG_UP, TrendDirection.UP]:
            buy_score += 2
        elif trend in [TrendDirection.STRONG_DOWN, TrendDirection.DOWN]:
            sell_score += 2

        # シグナル決定
        if buy_score > sell_score and buy_score >= 5:
            action = "BUY"
            strength = self._calculate_signal_strength(buy_score)
            confidence = min(buy_score * 10, 95)
        elif sell_score > buy_score and sell_score >= 5:
            action = "SELL"
            strength = self._calculate_signal_strength(sell_score)
            confidence = min(sell_score * 10, 95)
        else:
            action = "HOLD"
            strength = SignalStrength.WEAK
            confidence = 30

        return {
            'action': action,
            'strength': strength,
            'confidence': confidence,
            'buy_score': buy_score,
            'sell_score': sell_score
        }

    def _calculate_signal_strength(self, score: int) -> SignalStrength:
        """シグナル強度を計算"""
        if score >= 10:
            return SignalStrength.VERY_STRONG
        elif score >= 8:
            return SignalStrength.STRONG
        elif score >= 6:
            return SignalStrength.MODERATE
        elif score >= 4:
            return SignalStrength.WEAK
        else:
            return SignalStrength.VERY_WEAK

    def _calculate_key_levels(self, data: pd.DataFrame) -> Dict[str, float]:
        """サポート・レジスタンスレベルを計算"""
        close = data['Close']
        high = data['High']
        low = data['Low']

        # 直近の高値・安値
        recent_high = float(high.tail(20).max())
        recent_low = float(low.tail(20).min())

        # ピボットポイント計算
        last_close = float(close.iloc[-1])
        last_high = float(high.iloc[-1])
        last_low = float(low.iloc[-1])

        pivot = (last_high + last_low + last_close) / 3
        r1 = 2 * pivot - last_low
        s1 = 2 * pivot - last_high
        r2 = pivot + (last_high - last_low)
        s2 = pivot - (last_high - last_low)

        return {
            'current_price': last_close,
            'resistance_1': r1,
            'resistance_2': r2,
            'support_1': s1,
            'support_2': s2,
            'pivot': pivot,
            'recent_high': recent_high,
            'recent_low': recent_low
        }

    def _calculate_risk_reward(self, data: pd.DataFrame, signal: Dict, key_levels: Dict) -> float:
        """リスクリワード比を計算"""
        current_price = key_levels['current_price']

        if signal['action'] == "BUY":
            # 買いの場合
            stop_loss = key_levels['support_1']
            take_profit = key_levels['resistance_1']
            risk = current_price - stop_loss
            reward = take_profit - current_price
        elif signal['action'] == "SELL":
            # 売りの場合
            stop_loss = key_levels['resistance_1']
            take_profit = key_levels['support_1']
            risk = stop_loss - current_price
            reward = current_price - take_profit
        else:
            return 0

        if risk > 0:
            return reward / risk
        return 0

    def _calculate_position_size(self, indicators: Dict, trend: TrendDirection) -> float:
        """推奨ポジションサイズを計算（リスク管理）"""
        current = indicators['current_values']

        # ボラティリティベースのサイズ調整
        if current['rsi'] > 70 or current['rsi'] < 30:
            base_size = 50  # 極端な水準では小さく
        else:
            base_size = 100

        # トレンド強度による調整
        if trend in [TrendDirection.STRONG_UP, TrendDirection.STRONG_DOWN]:
            trend_adjustment = 1.2
        elif trend == TrendDirection.NEUTRAL:
            trend_adjustment = 0.5
        else:
            trend_adjustment = 1.0

        return min(base_size * trend_adjustment, 100)

    def _generate_algorithm_summary(self, trend: TrendDirection, signal: Dict, indicators: Dict) -> str:
        """アルゴリズム分析のサマリー生成"""
        current = indicators['current_values']

        summary = f"""
【アルゴリズム分析結果】
トレンド: {trend.value}
シグナル: {signal['action']} (信頼度: {signal['confidence']}%)
RSI: {current['rsi']:.1f}
MACD状態: {'ブル' if current['macd'] > current['macd_signal'] else 'ベア'}
推奨アクション: {signal['action']}シグナル
        """.strip()

        return summary


class LLMAnalyzer:
    """LLMベースの為替分析エンジン"""

    def __init__(self, api_key: Optional[str] = None):
        # 環境変数からAPIキーを取得
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')

        # Djangoの設定からも取得を試みる
        if not self.api_key:
            try:
                from django.conf import settings
                self.api_key = settings.OPENAI_API_KEY
            except:
                pass

    def analyze_with_prompt(self, market_data: Dict, algorithm_result: AlgorithmicAnalysis) -> Dict:
        """
        LLMにプロンプトを投げて分析

        Args:
            market_data: 市場データ
            algorithm_result: アルゴリズム分析結果

        Returns:
            LLM分析結果
        """
        # プロンプト構築
        prompt = self._build_analysis_prompt(market_data, algorithm_result)

        # ここでは実際のAPI呼び出しの代わりにモック応答を返す
        # 実際の実装では OpenAI API や Claude API を呼び出す
        llm_response = self._mock_llm_response(market_data, algorithm_result)

        return llm_response

    def _build_analysis_prompt(self, market_data: Dict, algorithm_result: AlgorithmicAnalysis) -> str:
        """LLM用プロンプトを構築"""

        prompt = f"""
あなたは経験豊富なFXトレーダーです。以下の市場データとテクニカル分析結果を基に、
総合的な相場分析と具体的なトレード戦略を提案してください。

## 現在の市場データ
- 通貨ペア: {market_data.get('symbol', 'USD/JPY')}
- 現在価格: {algorithm_result.key_levels['current_price']:.3f}
- RSI: {algorithm_result.indicators['rsi']:.1f}
- トレンド: {algorithm_result.trend_direction.value}

## テクニカル分析結果
- アルゴリズムシグナル: {algorithm_result.entry_signal}
- 信頼度: {algorithm_result.confidence}%
- リスクリワード比: {algorithm_result.risk_reward_ratio:.2f}

## キーレベル
- レジスタンス1: {algorithm_result.key_levels['resistance_1']:.3f}
- サポート1: {algorithm_result.key_levels['support_1']:.3f}
- 直近高値: {algorithm_result.key_levels['recent_high']:.3f}
- 直近安値: {algorithm_result.key_levels['recent_low']:.3f}

以下の観点から分析してください：

1. **市場心理分析**
   - 現在の市場参加者の心理状態
   - 買い圧力と売り圧力のバランス

2. **エントリー戦略**
   - 具体的なエントリータイミング
   - 推奨するオーダータイプ（成行/指値）
   - エントリー価格の目安

3. **リスク管理**
   - ストップロスの設定位置とその理由
   - テイクプロフィットの設定位置とその理由
   - ポジションサイズの推奨

4. **代替シナリオ**
   - メインシナリオが外れた場合の対処法
   - 注意すべき価格レベル

5. **時間軸の考慮**
   - このトレードの推奨保有期間
   - 東京・ロンドン・NYの各市場時間での注意点

回答は具体的で実践的な内容にしてください。
        """

        return prompt

    def _mock_llm_response(self, market_data: Dict, algorithm_result: AlgorithmicAnalysis) -> Dict:
        """モックLLM応答（実際はAPI呼び出し）"""

        # 実際の実装では、ここでOpenAI/Claude APIを呼び出す
        # response = openai.ChatCompletion.create(...)

        # モック応答
        mock_analysis = {
            "market_psychology": "現在の市場は慎重な楽観主義の状態。RSI値から判断すると、まだ上昇余地あり。",
            "entry_strategy": {
                "timing": "東京時間の仲値決定後、または欧州時間開始時",
                "order_type": "指値注文推奨",
                "entry_price": algorithm_result.key_levels['current_price'] * 0.999
            },
            "risk_management": {
                "stop_loss": algorithm_result.key_levels['support_1'],
                "take_profit": algorithm_result.key_levels['resistance_1'],
                "position_size": "総資金の2%以内"
            },
            "alternative_scenario": "サポート1を下回った場合は即座に損切り。その後は様子見。",
            "time_consideration": {
                "holding_period": "1-3日（スイングトレード）",
                "market_hours_note": "NY時間のFOMC議事録発表に注意"
            },
            "confidence_level": "中～高",
            "additional_notes": "ボラティリティが低下傾向なので、ブレイクアウト待ちも検討"
        }

        return mock_analysis


class HybridFXAnalyzer:
    """ハイブリッド分析システム（アルゴリズム + LLM）"""

    def __init__(self, llm_api_key: Optional[str] = None):
        self.algo_analyzer = AlgorithmicAnalyzer()
        self.llm_analyzer = LLMAnalyzer(llm_api_key)

    def analyze(self, symbol: str = "USDJPY=X", use_llm: bool = True) -> Dict[str, Any]:
        """
        完全な分析を実行

        Args:
            symbol: 通貨ペアシンボル
            use_llm: LLM分析を使用するか

        Returns:
            統合分析結果
        """
        try:
            # アルゴリズム分析
            algo_result = self.algo_analyzer.analyze(symbol)

            result = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "algorithmic_analysis": {
                    "trend": algo_result.trend_direction.value,
                    "signal": algo_result.entry_signal,
                    "confidence": algo_result.confidence,
                    "signal_strength": algo_result.signal_strength.value,
                    "risk_reward_ratio": algo_result.risk_reward_ratio,
                    "position_size": algo_result.suggested_position_size,
                    "key_levels": algo_result.key_levels,
                    "indicators": algo_result.indicators,
                    "summary": algo_result.analysis_summary
                }
            }

            # LLM分析（オプション）
            if use_llm:
                market_data = {"symbol": symbol}
                llm_result = self.llm_analyzer.analyze_with_prompt(market_data, algo_result)
                result["llm_analysis"] = llm_result

                # 統合判断
                result["hybrid_recommendation"] = self._generate_hybrid_recommendation(
                    algo_result, llm_result
                )

            return result

        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _generate_hybrid_recommendation(self, algo_result: AlgorithmicAnalysis, llm_result: Dict) -> Dict:
        """アルゴリズムとLLMの分析を統合"""

        # 両方の分析から総合的な推奨を生成
        recommendation = {
            "final_action": algo_result.entry_signal,  # アルゴリズムを優先
            "confidence": (algo_result.confidence + 70) / 2,  # 平均化
            "key_points": [
                f"アルゴリズム: {algo_result.entry_signal} (信頼度{algo_result.confidence}%)",
                f"LLM推奨: {llm_result.get('entry_strategy', {}).get('timing', 'N/A')}",
                f"リスクリワード比: {algo_result.risk_reward_ratio:.2f}"
            ],
            "execution_plan": {
                "entry": algo_result.key_levels['current_price'],
                "stop_loss": algo_result.key_levels['support_1'] if algo_result.entry_signal == "BUY" else algo_result.key_levels['resistance_1'],
                "take_profit": algo_result.key_levels['resistance_1'] if algo_result.entry_signal == "BUY" else algo_result.key_levels['support_1'],
                "position_size": algo_result.suggested_position_size
            }
        }

        return recommendation


# デモ実行関数
def demo():
    """デモ実行"""
    print("=" * 60)
    print("🤖 ハイブリッドFX分析システム デモ")
    print("=" * 60)

    analyzer = HybridFXAnalyzer()

    # 複数の通貨ペアで分析
    symbols = [
        ("USDJPY=X", "USD/JPY"),
        ("EURJPY=X", "EUR/JPY"),
    ]

    for symbol, name in symbols:
        print(f"\n📊 {name} 分析中...")
        result = analyzer.analyze(symbol, use_llm=True)

        if "error" not in result:
            # アルゴリズム分析結果
            algo = result['algorithmic_analysis']
            print(f"\n【アルゴリズム分析】")
            print(f"トレンド: {algo['trend']}")
            print(f"シグナル: {algo['signal']} (信頼度: {algo['confidence']:.1f}%)")
            print(f"リスクリワード比: {algo['risk_reward_ratio']:.2f}")
            print(f"推奨ポジションサイズ: {algo['position_size']:.0f}%")

            # キーレベル
            levels = algo['key_levels']
            print(f"\n【価格レベル】")
            print(f"現在価格: {levels['current_price']:.3f}")
            print(f"レジスタンス: {levels['resistance_1']:.3f}")
            print(f"サポート: {levels['support_1']:.3f}")

            # LLM分析結果（あれば）
            if 'llm_analysis' in result:
                llm = result['llm_analysis']
                print(f"\n【LLM分析】")
                print(f"市場心理: {llm.get('market_psychology', 'N/A')}")
                print(f"推奨保有期間: {llm.get('time_consideration', {}).get('holding_period', 'N/A')}")

            # ハイブリッド推奨
            if 'hybrid_recommendation' in result:
                hybrid = result['hybrid_recommendation']
                print(f"\n【統合推奨】")
                print(f"最終判断: {hybrid['final_action']}")
                print(f"総合信頼度: {hybrid['confidence']:.1f}%")

                exec_plan = hybrid['execution_plan']
                print(f"\n【実行計画】")
                print(f"エントリー: {exec_plan['entry']:.3f}")
                print(f"ストップロス: {exec_plan['stop_loss']:.3f}")
                print(f"利確: {exec_plan['take_profit']:.3f}")
                print(f"ポジションサイズ: {exec_plan['position_size']:.0f}%")

        print("\n" + "-" * 60)

    print("\n✅ 分析完了！")


if __name__ == "__main__":
    demo()