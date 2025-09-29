from django.db import models
from core.models import Currency

class MarketData(models.Model):
    """市場価格データ"""
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(db_index=True)
    bid = models.DecimalField(max_digits=10, decimal_places=5)  # 売値
    ask = models.DecimalField(max_digits=10, decimal_places=5)  # 買値
    spread = models.DecimalField(max_digits=8, decimal_places=5, null=True)  # スプレッド
    volume = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def mid_price(self):
        """中値計算"""
        return (self.bid + self.ask) / 2
    
    def save(self, *args, **kwargs):
        """スプレッド自動計算"""
        if self.bid and self.ask:
            self.spread = self.ask - self.bid
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.currency.symbol} - {self.timestamp}"
    
    class Meta:
        db_table = 'market_data'
        indexes = [
            models.Index(fields=['currency', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']

class GMOAPILog(models.Model):
    """GMO API呼び出しログ"""
    endpoint = models.CharField(max_length=200)
    method = models.CharField(max_length=10)  # GET, POST等
    status_code = models.IntegerField()
    response_time = models.FloatField()  # ミリ秒
    request_data = models.JSONField(null=True, blank=True)
    response_data = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.method} {self.endpoint} - {self.status_code}"
    
    class Meta:
        db_table = 'gmo_api_logs'
        ordering = ['-created_at']
