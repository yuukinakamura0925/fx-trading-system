"""
URL configuration for fx_trading project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

# URL設定 - どのURLがどの機能に繋がるかを定義
urlpatterns = [
    # Django管理画面
    path('admin/', admin.site.urls),
    
    # API エンドポイント - /api/ で始まるURLは全てAPIアプリが処理
    path('api/', include('api.urls')),
    
    # DRF のブラウザブルAPI（開発用）
    path('api-auth/', include('rest_framework.urls')),
]

# 生成されるURL構造:
# http://localhost:8000/admin/                    # Django管理画面
# http://localhost:8000/api/currencies/           # 通貨ペアAPI
# http://localhost:8000/api/market-data/          # 市場データAPI
# http://localhost:8000/api/positions/            # ポジションAPI
# http://localhost:8000/api/trades/               # 取引履歴API
# http://localhost:8000/api/performance/          # 戦略成績API
