"""
FX分析API用のシリアライザー
リクエスト/レスポンスのデータ構造を定義
"""

from rest_framework import serializers


class AnalysisRequestSerializer(serializers.Serializer):
    """分析リクエスト用シリアライザー"""

    # 通貨ペア（必須）
    symbol = serializers.ChoiceField(
        choices=[
            ('USDJPY=X', 'USD/JPY'),
            ('EURJPY=X', 'EUR/JPY'),
            ('GBPJPY=X', 'GBP/JPY'),
            ('AUDJPY=X', 'AUD/JPY'),
            ('NZDJPY=X', 'NZD/JPY'),
            ('CADJPY=X', 'CAD/JPY'),
            ('CHFJPY=X', 'CHF/JPY'),
            ('EURUSD=X', 'EUR/USD'),
        ],
        default='USDJPY=X',
        help_text='分析する通貨ペア'
    )

    # 分析期間（オプション）
    period = serializers.ChoiceField(
        choices=[
            ('1d', '1日'),
            ('5d', '5日'),
            ('1mo', '1ヶ月'),
            ('3mo', '3ヶ月'),
            ('6mo', '6ヶ月'),
            ('1y', '1年'),
        ],
        default='3mo',
        required=False,
        help_text='分析期間'
    )

    # LLM分析を使用するか（オプション）
    use_llm = serializers.BooleanField(
        default=True,
        required=False,
        help_text='LLM（ChatGPT）による分析を含めるか'
    )

    # 詳細レベル（オプション）
    detail_level = serializers.ChoiceField(
        choices=[
            ('basic', '基本'),
            ('detailed', '詳細'),
            ('full', '完全'),
        ],
        default='detailed',
        required=False,
        help_text='分析の詳細レベル'
    )


class TechnicalIndicatorsSerializer(serializers.Serializer):
    """テクニカル指標のシリアライザー"""
    price = serializers.FloatField()
    sma20 = serializers.FloatField()
    sma50 = serializers.FloatField()
    ema20 = serializers.FloatField()
    rsi = serializers.FloatField()
    macd = serializers.FloatField()
    macd_signal = serializers.FloatField()
    bb_upper = serializers.FloatField()
    bb_lower = serializers.FloatField()
    stoch_k = serializers.FloatField()
    stoch_d = serializers.FloatField()


class KeyLevelsSerializer(serializers.Serializer):
    """キーレベル（サポート・レジスタンス）のシリアライザー"""
    current_price = serializers.FloatField()
    resistance_1 = serializers.FloatField()
    resistance_2 = serializers.FloatField()
    support_1 = serializers.FloatField()
    support_2 = serializers.FloatField()
    pivot = serializers.FloatField()
    recent_high = serializers.FloatField()
    recent_low = serializers.FloatField()


class AlgorithmicAnalysisSerializer(serializers.Serializer):
    """アルゴリズム分析結果のシリアライザー"""
    trend = serializers.CharField()
    signal = serializers.CharField()
    confidence = serializers.FloatField()
    signal_strength = serializers.CharField()
    risk_reward_ratio = serializers.FloatField()
    position_size = serializers.FloatField()
    key_levels = KeyLevelsSerializer()
    indicators = TechnicalIndicatorsSerializer()
    summary = serializers.CharField()


class LLMAnalysisSerializer(serializers.Serializer):
    """LLM分析結果のシリアライザー"""
    market_psychology = serializers.CharField(required=False)
    entry_strategy = serializers.DictField(required=False)
    risk_management = serializers.DictField(required=False)
    alternative_scenario = serializers.CharField(required=False)
    time_consideration = serializers.DictField(required=False)
    confidence_level = serializers.CharField(required=False)
    additional_notes = serializers.CharField(required=False)


class HybridRecommendationSerializer(serializers.Serializer):
    """統合推奨のシリアライザー"""
    final_action = serializers.CharField()
    confidence = serializers.FloatField()
    key_points = serializers.ListField(
        child=serializers.CharField()
    )
    execution_plan = serializers.DictField()


class AnalysisResponseSerializer(serializers.Serializer):
    """分析レスポンス用シリアライザー"""
    timestamp = serializers.DateTimeField()
    symbol = serializers.CharField()
    algorithmic_analysis = AlgorithmicAnalysisSerializer()
    llm_analysis = LLMAnalysisSerializer(required=False)
    hybrid_recommendation = HybridRecommendationSerializer(required=False)

    # エラー情報（エラー時のみ）
    error = serializers.CharField(required=False)


class HistoricalDataSerializer(serializers.Serializer):
    """過去データ取得用シリアライザー"""
    symbol = serializers.ChoiceField(
        choices=[
            ('USDJPY=X', 'USD/JPY'),
            ('EURJPY=X', 'EUR/JPY'),
            ('GBPJPY=X', 'GBP/JPY'),
            ('AUDJPY=X', 'AUD/JPY'),
            ('EURUSD=X', 'EUR/USD'),
        ],
        default='USDJPY=X'
    )

    period = serializers.ChoiceField(
        choices=[
            ('1d', '1日'),
            ('5d', '5日'),
            ('1mo', '1ヶ月'),
            ('3mo', '3ヶ月'),
            ('6mo', '6ヶ月'),
            ('1y', '1年'),
            ('5y', '5年'),
            ('max', '最大'),
        ],
        default='1mo'
    )

    interval = serializers.ChoiceField(
        choices=[
            ('1m', '1分'),
            ('5m', '5分'),
            ('15m', '15分'),
            ('30m', '30分'),
            ('1h', '1時間'),
            ('1d', '1日'),
        ],
        default='1d'
    )