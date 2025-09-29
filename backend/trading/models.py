from django.db import models
from django.utils import timezone
from core.models import Currency

class Strategy(models.Model):
    """取引戦略管理"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    risk_percent = models.DecimalField(max_digits=5, decimal_places=2, default=2.0)  # リスク%
    max_positions = models.IntegerField(default=5)  # 最大ポジション数
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'strategies'

class Position(models.Model):
    """ポジション管理"""
    SIDE_CHOICES = [
        ('BUY', '買い'),
        ('SELL', '売り'),
    ]
    
    STATUS_CHOICES = [
        ('OPEN', '建玉中'),
        ('CLOSED', '決済済'),
        ('PARTIAL', '一部決済'),
    ]
    
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    side = models.CharField(max_length=4, choices=SIDE_CHOICES)
    size = models.BigIntegerField()  # 取引数量
    entry_price = models.DecimalField(max_digits=10, decimal_places=5)
    current_price = models.DecimalField(max_digits=10, decimal_places=5, null=True)
    stop_loss = models.DecimalField(max_digits=10, decimal_places=5, null=True)
    take_profit = models.DecimalField(max_digits=10, decimal_places=5, null=True)
    unrealized_pnl = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    realized_pnl = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPEN')
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    def calculate_pnl(self, current_price=None):
        """損益計算"""
        if not current_price:
            current_price = self.current_price
        if not current_price:
            return 0
            
        price_diff = current_price - self.entry_price
        if self.side == 'SELL':
            price_diff = -price_diff
            
        # JPY建ての場合（USD/JPY等）
        if self.currency.quote_currency == 'JPY':
            return float(price_diff * self.size)
        else:
            # その他の通貨ペア
            return float(price_diff * self.size * current_price)
    
    def __str__(self):
        return f"{self.currency.symbol} {self.side} {self.size} @ {self.entry_price}"
    
    class Meta:
        db_table = 'positions'
        ordering = ['-opened_at']

class Trade(models.Model):
    """取引履歴"""
    SIDE_CHOICES = [
        ('BUY', '買い'),
        ('SELL', '売り'),
    ]
    
    ORDER_TYPE_CHOICES = [
        ('MARKET', '成行'),
        ('LIMIT', '指値'),
        ('STOP', '逆指値'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', '注文中'),
        ('EXECUTED', '約定'),
        ('CANCELLED', 'キャンセル'),
        ('REJECTED', '拒否'),
    ]
    
    position = models.ForeignKey(Position, on_delete=models.CASCADE, null=True, blank=True)
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    side = models.CharField(max_length=4, choices=SIDE_CHOICES)
    size = models.BigIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=5)
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    profit_loss = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    commission = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    execution_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.currency.symbol} {self.side} {self.size} @ {self.price}"
    
    class Meta:
        db_table = 'trades'
        ordering = ['-created_at']

class StrategyPerformance(models.Model):
    """戦略パフォーマンス"""
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    date = models.DateField()
    total_trades = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    losing_trades = models.IntegerField(default=0)
    total_pnl = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    max_drawdown = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def calculate_win_rate(self):
        """勝率計算"""
        if self.total_trades > 0:
            self.win_rate = (self.winning_trades / self.total_trades) * 100
        return self.win_rate
    
    def __str__(self):
        return f"{self.strategy.name} - {self.date}"
    
    class Meta:
        db_table = 'strategy_performance'
        unique_together = ['strategy', 'date']
        ordering = ['-date']
