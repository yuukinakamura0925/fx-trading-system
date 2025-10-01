from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from datetime import datetime, timedelta
import requests
import json
# APIモデル
from core.models import Currency
from trading.models import Strategy, Position, Trade, StrategyPerformance
from .models import KLine
from .serializers import (
    CurrencySerializer, StrategySerializer,
    PositionSerializer, TradeSerializer, StrategyPerformanceSerializer,
    KLineSerializer
)


# GMO API プロキシビュー（CORS回避用）
class GMOProxyView(APIView):
    """
    GMOコインPublic APIのプロキシエンドポイント
    フロントエンドからのCORSエラーを回避するため、
    バックエンド経由でGMO APIにアクセス
    """

    def get(self, request, endpoint):
        """
        GMO Public APIへのGETリクエストをプロキシ

        Args:
            endpoint: APIエンドポイント名（status, ticker, klines, symbols）
        """
        base_url = 'https://forex-api.coin.z.com/public/v1'

        # エンドポイントマッピング
        endpoints = {
            'status': '/status',
            'ticker': '/ticker',
            'klines': '/klines',
            'symbols': '/symbols',
            'orderbooks': '/orderbooks'
            # 注意: tradesはWebSocketのみでREST APIなし
        }

        if endpoint not in endpoints:
            return Response(
                {'error': f'Unknown endpoint: {endpoint}'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            # GMO APIへリクエスト
            url = base_url + endpoints[endpoint]

            # クエリパラメータをそのまま転送
            params = request.query_params.dict()

            response = requests.get(url, params=params)
            response.raise_for_status()

            # GMOからのレスポンスをそのまま返す
            return Response(response.json())

        except requests.exceptions.RequestException as e:
            return Response(
                {'error': f'GMO API request failed: {str(e)}'},
                status=status.HTTP_502_BAD_GATEWAY
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


class KLineViewSet(viewsets.ModelViewSet):
    """
    KLine（ローソク足）データAPI
    GMO APIから取得した四本値データの管理と取得
    """
    queryset = KLine.objects.all()
    serializer_class = KLineSerializer

    def get_queryset(self):
        """
        フィルタリング機能付きのクエリセット
        クエリパラメータで通貨ペア、価格タイプ、インターバルなどでフィルタ可能
        """
        queryset = KLine.objects.all()

        # 通貨ペアでフィルタ（例: ?symbol=USD_JPY）
        symbol = self.request.query_params.get('symbol', None)
        if symbol:
            queryset = queryset.filter(currency__symbol=symbol)

        # 価格タイプでフィルタ（例: ?price_type=ASK）
        price_type = self.request.query_params.get('price_type', None)
        if price_type:
            queryset = queryset.filter(price_type=price_type.upper())

        # インターバルでフィルタ（例: ?interval=1min）
        interval = self.request.query_params.get('interval', None)
        if interval:
            queryset = queryset.filter(interval=interval)

        # 日時範囲でフィルタ（例: ?start_time=2023-01-01&end_time=2023-12-31）
        start_time = self.request.query_params.get('start_time', None)
        end_time = self.request.query_params.get('end_time', None)
        if start_time:
            queryset = queryset.filter(open_time__gte=start_time)
        if end_time:
            queryset = queryset.filter(open_time__lte=end_time)

        # order_byは必ずスライスの前に実行
        queryset = queryset.order_by('-open_time')

        # 取得件数制限（例: ?limit=100）
        # 注意: スライスは最後に実行すること
        limit = self.request.query_params.get('limit', None)
        if limit:
            queryset = queryset[:int(limit)]

        return queryset

    @action(detail=False, methods=['post'])
    def fetch_from_gmo(self, request):
        """
        GMO APIからKLineデータを取得してDBに保存

        Request Body:
        {
            "symbol": "USD_JPY",
            "price_type": "ASK",
            "interval": "1min",
            "date": "20231028"
        }
        """
        symbol = request.data.get('symbol')
        price_type = request.data.get('price_type')
        interval = request.data.get('interval')
        date = request.data.get('date')

        # 必須パラメータチェック
        if not all([symbol, price_type, interval, date]):
            return Response(
                {'error': 'symbol, price_type, interval, date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 通貨ペア取得
            currency = Currency.objects.get(symbol=symbol)

            # GMO APIからKLineデータ取得
            base_url = 'https://forex-api.coin.z.com/public/v1/klines'
            params = {
                'symbol': symbol,
                'priceType': price_type,
                'interval': interval,
                'date': date
            }

            response = requests.get(base_url, params=params)
            response.raise_for_status()
            gmo_data = response.json()

            if gmo_data.get('status') != 0:
                return Response(
                    {'error': 'GMO API returned error', 'details': gmo_data},
                    status=status.HTTP_502_BAD_GATEWAY
                )

            # データベースに保存
            saved_count = 0
            for item in gmo_data.get('data', []):
                # UNIXタイムスタンプ（ミリ秒）をDateTimeに変換
                open_time = datetime.fromtimestamp(int(item['openTime']) / 1000)

                # get_or_create: 既存データがあれば取得、なければ作成
                kline, created = KLine.objects.get_or_create(
                    currency=currency,
                    price_type=price_type.upper(),
                    interval=interval,
                    open_time=open_time,
                    defaults={
                        'open': item['open'],
                        'high': item['high'],
                        'low': item['low'],
                        'close': item['close']
                    }
                )

                if created:
                    saved_count += 1

            return Response({
                'message': f'Successfully fetched and saved {saved_count} KLine records',
                'total_received': len(gmo_data.get('data', [])),
                'saved': saved_count,
                'skipped': len(gmo_data.get('data', [])) - saved_count
            })

        except Currency.DoesNotExist:
            return Response(
                {'error': f'Currency {symbol} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except requests.exceptions.RequestException as e:
            return Response(
                {'error': f'GMO API request failed: {str(e)}'},
                status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            return Response(
                {'error': f'Unexpected error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
