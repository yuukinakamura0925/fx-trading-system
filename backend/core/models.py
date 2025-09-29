from django.db import models

class Currency(models.Model):
    """通貨ペア管理（GMO API用の基本情報のみ）"""
    symbol = models.CharField(max_length=10, unique=True)  # USD_JPY, EUR_USD等
    display_name = models.CharField(max_length=20, default='')  # 米ドル/円等
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.symbol} ({self.display_name})"

    class Meta:
        db_table = 'currencies'
