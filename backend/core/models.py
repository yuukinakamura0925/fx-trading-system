from django.db import models
from django.utils import timezone

class Currency(models.Model):
    """通貨ペア管理"""
    symbol = models.CharField(max_length=10, unique=True)  # USD_JPY, EUR_USD等
    base_currency = models.CharField(max_length=3)  # USD, EUR等
    quote_currency = models.CharField(max_length=3)  # JPY, USD等
    pip_size = models.DecimalField(max_digits=10, decimal_places=5, default=0.0001)
    min_trade_size = models.IntegerField(default=1000)  # 最小取引単位
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.symbol
    
    class Meta:
        db_table = 'currencies'

class TradingSession(models.Model):
    """取引セッション管理"""
    name = models.CharField(max_length=50)  # 東京, ロンドン, ニューヨーク
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'trading_sessions'
