from rest_framework import serializers
from core.models import Currency
from trading.models import Strategy, Position, Trade, StrategyPerformance
from .models import KLine


class CurrencySerializer(serializers.ModelSerializer):
    """通貨ペア情報のJSON変換クラス"""
    class Meta:
        model = Currency
        fields = '__all__'  # 全フィールドを含める


class KLineSerializer(serializers.ModelSerializer):
    """
    KLine（ローソク足）データのJSON変換クラス
    GMO APIから取得した四本値データをJSON形式で提供
    """
    # 通貨ペアのシンボル名を追加（例: USD_JPY）
    currency_symbol = serializers.CharField(source='currency.symbol', read_only=True)

    class Meta:
        model = KLine
        fields = [
            'id',
            'currency',
            'currency_symbol',  # 読みやすさのため通貨ペア名も含める
            'price_type',       # BID or ASK
            'interval',         # 1min, 5min, 1hour など
            'open_time',        # 開始時刻
            'open',             # 始値
            'high',             # 高値
            'low',              # 安値
            'close',            # 終値
            'created_at'        # データ登録日時
        ]
        # 読み取り専用フィールド（データ登録後は変更不可）
        read_only_fields = ['id', 'currency_symbol', 'created_at']

class StrategySerializer(serializers.ModelSerializer):
    """取引戦略のJSON変換クラス"""
    class Meta:
        model = Strategy
        fields = '__all__'

class PositionSerializer(serializers.ModelSerializer):
    """ポジション情報のJSON変換クラス"""
    currency_symbol = serializers.CharField(source='currency.symbol', read_only=True)
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)
    current_pnl = serializers.SerializerMethodField()  # 現在の損益を計算
    
    class Meta:
        model = Position
        fields = ['id', 'strategy', 'strategy_name', 'currency', 'currency_symbol', 
                 'side', 'size', 'entry_price', 'current_price', 'stop_loss', 'take_profit',
                 'unrealized_pnl', 'current_pnl', 'status', 'opened_at', 'closed_at']
    
    def get_current_pnl(self, obj):
        """現在の損益を動的に計算"""
        return obj.calculate_pnl()

class TradeSerializer(serializers.ModelSerializer):
    """取引履歴のJSON変換クラス"""
    currency_symbol = serializers.CharField(source='currency.symbol', read_only=True)
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)
    
    class Meta:
        model = Trade
        fields = ['id', 'position', 'strategy', 'strategy_name', 'currency', 'currency_symbol',
                 'side', 'size', 'price', 'order_type', 'status', 'profit_loss', 
                 'commission', 'execution_time', 'created_at']

class StrategyPerformanceSerializer(serializers.ModelSerializer):
    """戦略成績のJSON変換クラス"""
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)
    
    class Meta:
        model = StrategyPerformance
        fields = ['id', 'strategy', 'strategy_name', 'date', 'total_trades', 
                 'winning_trades', 'losing_trades', 'total_pnl', 'max_drawdown', 
                 'win_rate', 'created_at']