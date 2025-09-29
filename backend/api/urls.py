from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# DRF Router - APIエンドポイントを自動生成
router = DefaultRouter()

# 各ViewSetをルーターに登録
router.register(r'currencies', views.CurrencyViewSet)        # /api/currencies/
router.register(r'market-data', views.MarketDataViewSet)     # /api/market-data/
router.register(r'strategies', views.StrategyViewSet)        # /api/strategies/
router.register(r'positions', views.PositionViewSet)        # /api/positions/
router.register(r'trades', views.TradeViewSet)              # /api/trades/
router.register(r'performance', views.StrategyPerformanceViewSet)  # /api/performance/

# URL パターン定義
urlpatterns = [
    # DRF RouterのURL群を含める
    path('', include(router.urls)),
    
    # 将来的に追加する可能性のあるカスタムエンドポイント
    # path('custom-endpoint/', views.custom_view, name='custom-endpoint'),
]

# 生成されるAPIエンドポイント一覧:
# GET    /api/currencies/                    # 全通貨ペア取得
# GET    /api/currencies/active/             # アクティブ通貨ペア取得
# GET    /api/market-data/                   # 市場データ取得
# GET    /api/market-data/latest/            # 最新価格取得
# GET    /api/market-data/?currency=USD_JPY  # 通貨ペア指定で取得
# GET    /api/positions/                     # 全ポジション取得
# GET    /api/positions/open/                # オープンポジション取得
# GET    /api/positions/summary/             # ポジションサマリー取得
# GET    /api/trades/                        # 全取引履歴取得
# GET    /api/trades/recent/                 # 直近の取引履歴取得
# GET    /api/performance/dashboard/         # ダッシュボード用成績取得