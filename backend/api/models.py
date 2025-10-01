from django.db import models
from core.models import Currency


class KLine(models.Model):
    """
    KLine（ローソク足）データモデル
    GMO APIから取得した四本値（OHLC: Open, High, Low, Close）を保存
    """

    # インターバルの選択肢（GMO APIの仕様に準拠）
    INTERVAL_CHOICES = [
        ('1min', '1分'),
        ('5min', '5分'),
        ('10min', '10分'),
        ('15min', '15分'),
        ('30min', '30分'),
        ('1hour', '1時間'),
        ('4hour', '4時間'),
        ('8hour', '8時間'),
        ('12hour', '12時間'),
        ('1day', '1日'),
        ('1week', '1週間'),
        ('1month', '1ヶ月'),
    ]

    # 価格タイプの選択肢
    PRICE_TYPE_CHOICES = [
        ('BID', '売値'),
        ('ASK', '買値'),
    ]

    # 通貨ペア（外部キー: core.Currency）
    currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name='klines',
        verbose_name='通貨ペア'
    )

    # 価格タイプ（BID or ASK）
    price_type = models.CharField(
        max_length=3,
        choices=PRICE_TYPE_CHOICES,
        verbose_name='価格タイプ'
    )

    # インターバル（時間足）
    interval = models.CharField(
        max_length=10,
        choices=INTERVAL_CHOICES,
        verbose_name='インターバル'
    )

    # 開始時刻（UNIXタイムスタンプをミリ秒から秒に変換して保存）
    open_time = models.DateTimeField(
        verbose_name='開始時刻',
        db_index=True  # 時系列検索のためインデックス作成
    )

    # 始値（Decimal型で高精度保存: 小数点5桁まで対応）
    open = models.DecimalField(
        max_digits=15,
        decimal_places=5,
        verbose_name='始値'
    )

    # 高値
    high = models.DecimalField(
        max_digits=15,
        decimal_places=5,
        verbose_name='高値'
    )

    # 安値
    low = models.DecimalField(
        max_digits=15,
        decimal_places=5,
        verbose_name='安値'
    )

    # 終値
    close = models.DecimalField(
        max_digits=15,
        decimal_places=5,
        verbose_name='終値'
    )

    # データ作成日時（自動設定）
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='作成日時'
    )

    class Meta:
        # テーブル名
        db_table = 'api_kline'

        # 通貨ペア、価格タイプ、インターバル、開始時刻の組み合わせで一意制約
        # （同じデータの重複登録を防ぐ）
        unique_together = ['currency', 'price_type', 'interval', 'open_time']

        # デフォルトの並び順: 開始時刻の降順（新しい順）
        ordering = ['-open_time']

        # 複合インデックス: 通貨ペア + 価格タイプ + インターバル + 開始時刻
        # （検索パフォーマンス向上のため）
        indexes = [
            models.Index(fields=['currency', 'price_type', 'interval', 'open_time']),
        ]

        verbose_name = 'KLineデータ'
        verbose_name_plural = 'KLineデータ'

    def __str__(self):
        """文字列表現"""
        return f"{self.currency.symbol} {self.price_type} {self.interval} - {self.open_time}"