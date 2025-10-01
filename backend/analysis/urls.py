"""
FX分析APIのURLルーティング
"""

from django.urls import path
from .views import (
    FXAnalysisView,
    CurrentPriceView,
    HistoricalDataView,
    SupportedPairsView,
    HealthCheckView,
    MultiTimeFrameAnalysisView
)
from .tfqe_views import TFQESignalView

app_name = 'analysis'

urlpatterns = [
    # TFQE戦略シグナル（メイン）
    path('tfqe-signal/', TFQESignalView.as_view(), name='tfqe-signal'),

    # メイン分析エンドポイント
    path('analyze/', FXAnalysisView.as_view(), name='analyze'),

    # マルチタイムフレーム分析エンドポイント
    path('multi-timeframe/', MultiTimeFrameAnalysisView.as_view(), name='multi-timeframe'),

    # 現在価格取得
    path('current-price/', CurrentPriceView.as_view(), name='current-price'),

    # 過去データ取得
    path('historical/', HistoricalDataView.as_view(), name='historical'),

    # サポート通貨ペア一覧
    path('supported-pairs/', SupportedPairsView.as_view(), name='supported-pairs'),

    # ヘルスチェック
    path('health/', HealthCheckView.as_view(), name='health'),
]

# 生成されるエンドポイント:
# POST http://localhost:8000/api/analysis/analyze/            # シンプル分析実行
# POST http://localhost:8000/api/analysis/multi-timeframe/    # マルチタイムフレーム分析
# GET  http://localhost:8000/api/analysis/current-price/      # 現在価格
# POST http://localhost:8000/api/analysis/historical/         # 過去データ
# GET  http://localhost:8000/api/analysis/supported-pairs/    # 通貨ペア一覧
# GET  http://localhost:8000/api/analysis/health/             # ヘルスチェック