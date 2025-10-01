from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# DRF Router - APIエンドポイントを自動生成
router = DefaultRouter()

# 各ViewSetをルーターに登録
router.register(r'currencies', views.CurrencyViewSet)        # /api/currencies/
router.register(r'klines', views.KLineViewSet)              # /api/klines/
router.register(r'strategies', views.StrategyViewSet)        # /api/strategies/
router.register(r'positions', views.PositionViewSet)        # /api/positions/
router.register(r'trades', views.TradeViewSet)              # /api/trades/
router.register(r'performance', views.StrategyPerformanceViewSet)  # /api/performance/

# URL パターン定義
urlpatterns = [
    # DRF RouterのURL群を含める
    path('', include(router.urls)),

    # GMO API プロキシエンドポイント（CORS回避用）
    path('gmo/<str:endpoint>/', views.GMOProxyView.as_view(), name='gmo-proxy'),
]

# 生成されるAPIエンドポイント一覧:
# GET    /api/currencies/                    # 全通貨ペア取得
# GET    /api/currencies/active/             # アクティブ通貨ペア取得
# GET    /api/klines/                        # KLineデータ一覧取得
# POST   /api/klines/fetch_from_gmo/         # GMOからKLineデータを取得・保存
# GET    /api/strategies/                    # 全戦略取得
# GET    /api/strategies/active/             # アクティブ戦略取得
# GET    /api/positions/                     # 全ポジション取得
# GET    /api/positions/open/                # オープンポジション取得
# GET    /api/positions/summary/             # ポジションサマリー取得
# GET    /api/trades/                        # 全取引履歴取得
# GET    /api/trades/recent/                 # 直近の取引履歴取得
# GET    /api/performance/dashboard/         # ダッシュボード用成績取得
#
# GMO API プロキシ:
# GET    /api/gmo/status/                    # GMO API ステータス
# GET    /api/gmo/ticker/                    # GMO API レート情報
# GET    /api/gmo/klines/                    # GMO API ローソク足（プロキシ）
# GET    /api/gmo/symbols/                   # GMO API 通貨ペア情報
# GET    /api/gmo/orderbooks/                # GMO API 板情報