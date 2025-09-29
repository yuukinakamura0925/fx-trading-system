from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import sys
import os

# プロジェクトのルートをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))

from mock_data.gmo_mock_client import GMOMockClient
from core.models import Currency
from trading.models import Strategy
from api.models import MarketData

class Command(BaseCommand):
    """
    モックデータをデータベースに投入するDjango管理コマンド
    
    使用方法:
    python manage.py populate_mock_data
    python manage.py populate_mock_data --currencies-only  # 通貨ペアのみ
    python manage.py populate_mock_data --market-data-only # 市場データのみ
    """
    help = 'モックデータをデータベースに投入'

    def add_arguments(self, parser):
        """コマンドライン引数の定義"""
        parser.add_argument(
            '--currencies-only',
            action='store_true',
            help='通貨ペアのみ作成',
        )
        parser.add_argument(
            '--market-data-only',
            action='store_true',
            help='市場データのみ作成',
        )
        parser.add_argument(
            '--samples',
            type=int,
            default=100,
            help='市場データのサンプル数（デフォルト: 100）',
        )

    def handle(self, *args, **options):
        """メイン処理"""
        self.stdout.write(
            self.style.SUCCESS('🚀 モックデータ投入開始')
        )

        # モッククライアント初期化
        mock_client = GMOMockClient()

        if not options['market_data_only']:
            self.create_currencies(mock_client)
            self.create_strategies()

        if not options['currencies_only']:
            samples = options['samples']
            self.create_market_data(mock_client, samples)

        self.stdout.write(
            self.style.SUCCESS('✅ モックデータ投入完了')
        )

    def create_currencies(self, mock_client):
        """通貨ペアを作成"""
        self.stdout.write('📊 通貨ペア作成中...')
        
        # モッククライアントから通貨ペア情報を取得
        currency_configs = {
            'USD_JPY': {'base': 'USD', 'quote': 'JPY', 'pip_size': '0.001'},
            'EUR_JPY': {'base': 'EUR', 'quote': 'JPY', 'pip_size': '0.001'},
            'GBP_JPY': {'base': 'GBP', 'quote': 'JPY', 'pip_size': '0.001'},
            'EUR_USD': {'base': 'EUR', 'quote': 'USD', 'pip_size': '0.00001'},
            'GBP_USD': {'base': 'GBP', 'quote': 'USD', 'pip_size': '0.00001'},
            'AUD_USD': {'base': 'AUD', 'quote': 'USD', 'pip_size': '0.00001'},
        }

        created_count = 0
        for symbol, config in currency_configs.items():
            currency, created = Currency.objects.get_or_create(
                symbol=symbol,
                defaults={
                    'base_currency': config['base'],
                    'quote_currency': config['quote'],
                    'pip_size': Decimal(config['pip_size']),
                    'min_trade_size': 1000,
                    'is_active': True,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'  ✅ {symbol} 作成')
            else:
                self.stdout.write(f'  ⚠️ {symbol} 既存')

        self.stdout.write(
            self.style.SUCCESS(f'📊 通貨ペア: {created_count}件新規作成')
        )

    def create_strategies(self):
        """取引戦略を作成"""
        self.stdout.write('🎯 取引戦略作成中...')
        
        strategies = [
            {
                'name': '21時戦略',
                'description': 'NY市場オープン時の価格変動を狙う戦略',
                'risk_percent': Decimal('2.0'),
                'max_positions': 3,
            },
            {
                'name': 'スキャルピング戦略',
                'description': '短期間の小さな利益を積み重ねる戦略',
                'risk_percent': Decimal('1.0'),
                'max_positions': 5,
            },
            {
                'name': 'トレンドフォロー戦略',
                'description': '長期トレンドに追従する戦略',
                'risk_percent': Decimal('3.0'),
                'max_positions': 2,
            },
        ]

        created_count = 0
        for strategy_data in strategies:
            strategy, created = Strategy.objects.get_or_create(
                name=strategy_data['name'],
                defaults=strategy_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'  ✅ {strategy_data["name"]} 作成')
            else:
                self.stdout.write(f'  ⚠️ {strategy_data["name"]} 既存')

        self.stdout.write(
            self.style.SUCCESS(f'🎯 戦略: {created_count}件新規作成')
        )

    def create_market_data(self, mock_client, samples):
        """市場データを作成"""
        self.stdout.write(f'📈 市場データ作成中... ({samples}サンプル)')
        
        # データベースの通貨ペアを取得
        currencies = Currency.objects.filter(is_active=True)
        
        if not currencies.exists():
            self.stdout.write(
                self.style.ERROR('❌ 通貨ペアが見つかりません。先に通貨ペアを作成してください。')
            )
            return

        total_created = 0
        
        for currency in currencies:
            self.stdout.write(f'  📊 {currency.symbol} のデータ作成中...')
            
            created_count = 0
            for i in range(samples):
                # モック価格データ取得
                mock_data = mock_client.get_ticker(currency.symbol)
                if not mock_data:
                    continue
                
                # 過去のランダムな時刻を生成（過去24時間以内）
                import random
                from datetime import timedelta
                hours_ago = random.uniform(0, 24)
                timestamp = timezone.now() - timedelta(hours=hours_ago)
                
                # MarketDataオブジェクト作成
                market_data = MarketData.objects.create(
                    currency=currency,
                    timestamp=timestamp,
                    bid=mock_data.bid,
                    ask=mock_data.ask,
                    volume=mock_data.volume,
                )
                
                created_count += 1
                
                # 価格を少し変動させる（次のサンプル用）
                mock_client._update_price(currency.symbol)
            
            self.stdout.write(f'    ✅ {created_count}件作成')
            total_created += created_count

        self.stdout.write(
            self.style.SUCCESS(f'📈 市場データ: 合計{total_created}件作成')
        )