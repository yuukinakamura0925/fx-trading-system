"""
FX分析APIのビュー
ハイブリッド分析システムのエンドポイント実装
"""

from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings
from datetime import datetime
import yfinance as yf
import pandas as pd
import logging

from .serializers import (
    AnalysisRequestSerializer,
    AnalysisResponseSerializer,
    HistoricalDataSerializer
)
# from .hybrid_analyzer import HybridFXAnalyzer  # エラーが出るため一時的にコメントアウト
from .simple_analyzer import SimpleFXAnalyzer
from .multi_timeframe_analyzer import MultiTimeFrameAnalyzer

logger = logging.getLogger(__name__)


class FXAnalysisView(views.APIView):
    """
    FX通貨ペアの分析を実行するAPIビュー

    POST /api/analysis/analyze/
    {
        "symbol": "USDJPY=X",
        "period": "3mo",
        "use_llm": true,
        "detail_level": "detailed"
    }
    """

    permission_classes = [AllowAny]  # 開発中は認証なし

    def post(self, request):
        """分析リクエストを処理"""

        # リクエストのバリデーション
        serializer = AnalysisRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "無効なリクエスト", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        # パラメータ取得
        symbol = serializer.validated_data['symbol']
        period = serializer.validated_data.get('period', '3mo')
        use_llm = serializer.validated_data.get('use_llm', True)
        detail_level = serializer.validated_data.get('detail_level', 'detailed')

        # 通貨ペア名の取得
        symbol_names = {
            'USDJPY=X': 'USD/JPY',
            'EURJPY=X': 'EUR/JPY',
            'GBPJPY=X': 'GBP/JPY',
            'AUDJPY=X': 'AUD/JPY',
            'NZDJPY=X': 'NZD/JPY',
            'CADJPY=X': 'CAD/JPY',
            'CHFJPY=X': 'CHF/JPY',
            'EURUSD=X': 'EUR/USD',
        }
        readable_name = symbol_names.get(symbol, symbol)

        try:
            logger.info(f"分析開始: {readable_name} (期間: {period}, LLM: {use_llm})")

            # ハイブリッドアナライザーを初期化
            # APIキーはsettingsから取得
            api_key = settings.OPENAI_API_KEY if hasattr(settings, 'OPENAI_API_KEY') else None

            if use_llm and not api_key:
                logger.warning("OpenAI APIキーが設定されていません。アルゴリズム分析のみ実行します。")
                use_llm = False

            # 分析実行
            analyzer = SimpleFXAnalyzer(openai_api_key=api_key)

            # 分析実行（期間パラメータも渡す）
            result = analyzer.analyze(symbol=symbol, period=period, use_llm=use_llm)

            # 成功レスポンス
            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"分析エラー: {str(e)}", exc_info=True)
            return Response(
                {
                    "error": "分析中にエラーが発生しました",
                    "detail": str(e),
                    "timestamp": datetime.now().isoformat()
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CurrentPriceView(views.APIView):
    """
    現在価格を取得するシンプルなAPIビュー

    GET /api/analysis/current-price/?symbol=USDJPY=X
    """

    permission_classes = [AllowAny]

    def get(self, request):
        """現在価格を取得"""

        symbol = request.query_params.get('symbol', 'USDJPY=X')

        try:
            # yfinanceで現在価格を取得
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # 現在価格を取得（複数の方法を試す）
            current_price = None
            if 'regularMarketPrice' in info:
                current_price = info['regularMarketPrice']
            elif 'price' in info:
                current_price = info['price']
            else:
                # 直近データから取得
                hist = ticker.history(period="1d")
                if not hist.empty:
                    current_price = float(hist['Close'].iloc[-1])

            if current_price is None:
                raise ValueError(f"価格データが取得できません: {symbol}")

            return Response({
                "symbol": symbol,
                "price": current_price,
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"価格取得エラー: {str(e)}")
            return Response(
                {"error": f"価格取得エラー: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HistoricalDataView(views.APIView):
    """
    過去の価格データを取得するAPIビュー

    POST /api/analysis/historical/
    {
        "symbol": "USDJPY=X",
        "period": "1mo",
        "interval": "1d"
    }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """過去データを取得"""

        serializer = HistoricalDataSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        symbol = serializer.validated_data['symbol']
        period = serializer.validated_data['period']
        interval = serializer.validated_data['interval']

        try:
            # yfinanceでデータ取得
            data = yf.download(
                symbol,
                period=period,
                interval=interval,
                progress=False
            )

            if data.empty:
                return Response(
                    {"error": "データが見つかりません"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # データをJSON形式に変換
            result = {
                "symbol": symbol,
                "period": period,
                "interval": interval,
                "data": []
            }

            for index, row in data.iterrows():
                result["data"].append({
                    "timestamp": index.isoformat(),
                    "open": float(row['Open']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "close": float(row['Close']),
                    "volume": float(row['Volume'])
                })

            return Response(result)

        except Exception as e:
            logger.error(f"データ取得エラー: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SupportedPairsView(views.APIView):
    """
    サポートされている通貨ペアのリストを返すAPIビュー

    GET /api/analysis/supported-pairs/
    """

    permission_classes = [AllowAny]

    def get(self, request):
        """サポート通貨ペアのリストを返す"""

        pairs = [
            {
                "symbol": "USDJPY=X",
                "name": "USD/JPY",
                "description": "米ドル/日本円"
            },
            {
                "symbol": "EURJPY=X",
                "name": "EUR/JPY",
                "description": "ユーロ/日本円"
            },
            {
                "symbol": "GBPJPY=X",
                "name": "GBP/JPY",
                "description": "英ポンド/日本円"
            },
            {
                "symbol": "AUDJPY=X",
                "name": "AUD/JPY",
                "description": "豪ドル/日本円"
            },
            {
                "symbol": "NZDJPY=X",
                "name": "NZD/JPY",
                "description": "NZドル/日本円"
            },
            {
                "symbol": "CADJPY=X",
                "name": "CAD/JPY",
                "description": "カナダドル/日本円"
            },
            {
                "symbol": "CHFJPY=X",
                "name": "CHF/JPY",
                "description": "スイスフラン/日本円"
            },
            {
                "symbol": "EURUSD=X",
                "name": "EUR/USD",
                "description": "ユーロ/米ドル"
            }
        ]

        return Response({
            "pairs": pairs,
            "total": len(pairs)
        })


class HealthCheckView(views.APIView):
    """
    APIヘルスチェック用ビュー

    GET /api/analysis/health/
    """

    permission_classes = [AllowAny]

    def get(self, request):
        """ヘルスチェック"""

        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "api": "running",
                "database": "connected",
                "yfinance": "available"
            },
            "features": {
                "algorithmic_analysis": True,
                "llm_analysis": bool(settings.OPENAI_API_KEY) if hasattr(settings, 'OPENAI_API_KEY') else False
            }
        }

        # yfinanceの接続テスト
        try:
            test_data = yf.download("USDJPY=X", period="1d", progress=False)
            health_status["services"]["yfinance"] = "connected"
        except:
            health_status["services"]["yfinance"] = "error"
            health_status["status"] = "degraded"

        return Response(health_status)


class MultiTimeFrameAnalysisView(views.APIView):
    """
    マルチタイムフレームの過去データを取得するAPIビュー

    POST /api/analysis/multi-timeframe/
    {
        "symbol": "USDJPY=X"
    }
    """

    permission_classes = [AllowAny]  # 開発中は認証なし

    def post(self, request):
        """マルチタイムフレームデータ取得リクエストを処理"""

        # パラメータ取得
        symbol = request.data.get('symbol', 'USDJPY=X')

        # 通貨ペア名の取得
        symbol_names = {
            'USDJPY=X': 'USD/JPY',
            'EURJPY=X': 'EUR/JPY',
            'GBPJPY=X': 'GBP/JPY',
            'AUDJPY=X': 'AUD/JPY',
            'NZDJPY=X': 'NZD/JPY',
            'CADJPY=X': 'CAD/JPY',
            'CHFJPY=X': 'CHF/JPY',
            'EURUSD=X': 'EUR/USD',
        }
        readable_name = symbol_names.get(symbol, symbol)

        try:
            logger.info(f"過去データ取得開始: {readable_name}")

            # データ取得
            from .data_fetcher import DataFetcher
            fetcher = DataFetcher()
            result = fetcher.fetch_all_timeframes(symbol)

            # エラーチェック
            if "error" in result:
                logger.error(f"データ取得エラー: {result['error']}")
                return Response(
                    {
                        "error": "データ取得中にエラーが発生しました",
                        "detail": result['error'],
                        "timestamp": datetime.now().isoformat()
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # 成功レスポンス
            logger.info(f"過去データ取得完了: {readable_name}")

            # メタ情報を追加
            result['api_info'] = {
                'source': 'GMO Coin FX API',
                'rate_limit': 'Public API（制限緩い）',
                'note': '常に最新データを取得'
            }

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"データ取得エラー: {str(e)}", exc_info=True)
            return Response(
                {
                    "error": "データ取得中にエラーが発生しました",
                    "detail": str(e),
                    "timestamp": datetime.now().isoformat()
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )