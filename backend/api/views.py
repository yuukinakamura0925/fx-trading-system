from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from .models import MarketData, GMOAPILog
from core.models import Currency
from trading.models import Strategy, Position, Trade, StrategyPerformance
from .serializers import (
    CurrencySerializer, MarketDataSerializer, StrategySerializer,
    PositionSerializer, TradeSerializer, StrategyPerformanceSerializer
)

class CurrencyViewSet(viewsets.ModelViewSet):
    """通貨ペア管理API"""
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """アクティブな通貨ペアのみ取得"""
        active_currencies = Currency.objects.filter(is_active=True)
        serializer = self.get_serializer(active_currencies, many=True)
        return Response(serializer.data)

class MarketDataViewSet(viewsets.ModelViewSet):
    """市場データAPI"""
    queryset = MarketData.objects.all()
    serializer_class = MarketDataSerializer
    
    def get_queryset(self):
        """フィルタリング機能付きのクエリセット"""
        queryset = MarketData.objects.all()
        
        # 通貨ペアでフィルタ
        currency = self.request.query_params.get('currency', None)
        if currency is not None:
            queryset = queryset.filter(currency__symbol=currency)
        
        # 時間範囲でフィルタ
        hours = self.request.query_params.get('hours', None)
        if hours is not None:
            start_time = timezone.now() - timedelta(hours=int(hours))
            queryset = queryset.filter(timestamp__gte=start_time)
        
        return queryset.order_by('-timestamp')
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """各通貨ペアの最新価格を取得"""
        currencies = Currency.objects.filter(is_active=True)
        latest_data = []
        
        for currency in currencies:
            latest_market_data = MarketData.objects.filter(currency=currency).first()
            if latest_market_data:
                serializer = self.get_serializer(latest_market_data)
                latest_data.append(serializer.data)
        
        return Response(latest_data)

class StrategyViewSet(viewsets.ModelViewSet):
    """取引戦略API"""
    queryset = Strategy.objects.all()
    serializer_class = StrategySerializer
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """アクティブな戦略のみ取得"""
        active_strategies = Strategy.objects.filter(is_active=True)
        serializer = self.get_serializer(active_strategies, many=True)
        return Response(serializer.data)

class PositionViewSet(viewsets.ModelViewSet):
    """ポジション管理API"""
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    
    @action(detail=False, methods=['get'])
    def open(self, request):
        """オープンポジションのみ取得"""
        open_positions = Position.objects.filter(status='OPEN')
        serializer = self.get_serializer(open_positions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """ポジション サマリー情報"""
        open_positions = Position.objects.filter(status='OPEN')
        total_positions = open_positions.count()
        total_pnl = sum([pos.calculate_pnl() for pos in open_positions])
        
        summary = {
            'total_positions': total_positions,
            'total_unrealized_pnl': total_pnl,
            'long_positions': open_positions.filter(side='BUY').count(),
            'short_positions': open_positions.filter(side='SELL').count(),
        }
        return Response(summary)

class TradeViewSet(viewsets.ModelViewSet):
    """取引履歴API"""
    queryset = Trade.objects.all()
    serializer_class = TradeSerializer
    
    def get_queryset(self):
        """フィルタリング機能付きのクエリセット"""
        queryset = Trade.objects.all()
        
        # 戦略でフィルタ
        strategy = self.request.query_params.get('strategy', None)
        if strategy is not None:
            queryset = queryset.filter(strategy__name=strategy)
        
        # ステータスでフィルタ
        status = self.request.query_params.get('status', None)
        if status is not None:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """直近の取引履歴を取得"""
        days = self.request.query_params.get('days', 7)
        start_date = timezone.now() - timedelta(days=int(days))
        recent_trades = Trade.objects.filter(created_at__gte=start_date)
        serializer = self.get_serializer(recent_trades, many=True)
        return Response(serializer.data)

class StrategyPerformanceViewSet(viewsets.ModelViewSet):
    """戦略成績API"""
    queryset = StrategyPerformance.objects.all()
    serializer_class = StrategyPerformanceSerializer
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """ダッシュボード用の成績サマリー"""
        recent_performance = StrategyPerformance.objects.filter(
            date__gte=timezone.now().date() - timedelta(days=30)
        )
        
        # 戦略別の成績集計
        strategy_summary = {}
        for perf in recent_performance:
            strategy_name = perf.strategy.name
            if strategy_name not in strategy_summary:
                strategy_summary[strategy_name] = {
                    'total_trades': 0,
                    'total_pnl': 0,
                    'win_rate': 0,
                    'best_day': 0,
                    'worst_day': 0
                }
            
            strategy_summary[strategy_name]['total_trades'] += perf.total_trades
            strategy_summary[strategy_name]['total_pnl'] += float(perf.total_pnl)
            strategy_summary[strategy_name]['best_day'] = max(
                strategy_summary[strategy_name]['best_day'], 
                float(perf.total_pnl)
            )
            strategy_summary[strategy_name]['worst_day'] = min(
                strategy_summary[strategy_name]['worst_day'], 
                float(perf.total_pnl)
            )
        
        return Response(strategy_summary)
