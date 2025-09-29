import random
import time
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class MockMarketData:
    """モック市場データクラス"""
    symbol: str
    bid: Decimal
    ask: Decimal
    timestamp: datetime
    volume: int = 0
    
    @property
    def spread(self) -> Decimal:
        """スプレッド計算"""
        return self.ask - self.bid
    
    @property
    def mid_price(self) -> Decimal:
        """中値計算"""
        return (self.bid + self.ask) / 2

class GMOMockClient:
    """GMO API のモッククライアント
    
    本物のGMO APIの代わりにダミーデータを生成する
    リアルタイム価格変動をシミュレーション
    """
    
    def __init__(self):
        # 通貨ペア別の基準価格設定
        self.base_prices = {
            'USD_JPY': Decimal('150.123'),
            'EUR_JPY': Decimal('162.456'),
            'GBP_JPY': Decimal('185.789'),
            'EUR_USD': Decimal('1.0850'),
            'GBP_USD': Decimal('1.2650'),
            'AUD_USD': Decimal('0.6780'),
        }
        
        # 通貨ペア別のスプレッド設定（pip単位）
        self.spreads = {
            'USD_JPY': Decimal('0.003'),    # 0.3pip
            'EUR_JPY': Decimal('0.004'),    # 0.4pip  
            'GBP_JPY': Decimal('0.006'),    # 0.6pip
            'EUR_USD': Decimal('0.00008'),  # 0.8pip
            'GBP_USD': Decimal('0.00012'),  # 1.2pip
            'AUD_USD': Decimal('0.00015'),  # 1.5pip
        }
        
        # 価格変動率設定（1回の変動幅）
        self.volatility = {
            'USD_JPY': 0.0002,    # 約0.03円
            'EUR_JPY': 0.0003,    # 約0.05円
            'GBP_JPY': 0.0004,    # 約0.07円
            'EUR_USD': 0.0001,    # 約0.01セント
            'GBP_USD': 0.0001,    # 約0.01セント
            'AUD_USD': 0.0001,    # 約0.01セント
        }
        
        # 現在価格（変動する）
        self.current_prices = self.base_prices.copy()
        
        print("🎯 GMO Mock Client 初期化完了")
        print(f"📊 対応通貨ペア: {list(self.base_prices.keys())}")
    
    def get_ticker(self, symbol: str) -> Optional[MockMarketData]:
        """
        指定通貨ペアのリアルタイム価格を取得
        
        Args:
            symbol (str): 通貨ペア（例: 'USD_JPY'）
            
        Returns:
            MockMarketData: 価格データ、または None（存在しない通貨ペア）
        """
        if symbol not in self.base_prices:
            print(f"❌ 未対応通貨ペア: {symbol}")
            return None
        
        # 価格を微変動させる（ランダムウォーク）
        self._update_price(symbol)
        
        # bid価格 = 現在価格 - スプレッドの半分
        spread = self.spreads[symbol]
        current_price = self.current_prices[symbol]
        
        bid = current_price - (spread / 2)
        ask = current_price + (spread / 2)
        
        # 小数点精度を通貨ペアに応じて調整
        if 'JPY' in symbol:
            # 円ペアは小数点3桁
            bid = bid.quantize(Decimal('0.001'))
            ask = ask.quantize(Decimal('0.001'))
        else:
            # その他は小数点5桁
            bid = bid.quantize(Decimal('0.00001'))
            ask = ask.quantize(Decimal('0.00001'))
        
        # ランダムな出来高生成
        volume = random.randint(50000, 500000)
        
        market_data = MockMarketData(
            symbol=symbol,
            bid=bid,
            ask=ask,
            timestamp=datetime.now(),
            volume=volume
        )
        
        print(f"📈 {symbol}: Bid={bid}, Ask={ask}, Spread={market_data.spread}")
        return market_data
    
    def _update_price(self, symbol: str):
        """
        価格をランダムに変動させる
        
        Args:
            symbol (str): 通貨ペア
        """
        volatility = self.volatility[symbol]
        base_price = self.base_prices[symbol]
        current_price = self.current_prices[symbol]
        
        # ランダムな変動率 (-volatility ~ +volatility)
        change_rate = Decimal(str(random.uniform(-volatility, volatility)))
        
        # 価格更新（Decimal型同士の計算）
        new_price = current_price * (Decimal('1') + change_rate)
        
        # 基準価格から大きく外れすぎないように制限（±5%以内）
        max_deviation = base_price * Decimal('0.05')
        min_price = base_price - max_deviation
        max_price = base_price + max_deviation
        
        # 価格範囲制限
        new_price = max(min_price, min(max_price, new_price))
        
        self.current_prices[symbol] = new_price
    
    def get_all_tickers(self) -> List[MockMarketData]:
        """
        全通貨ペアの最新価格を取得
        
        Returns:
            List[MockMarketData]: 全通貨ペアの価格データ
        """
        all_data = []
        for symbol in self.base_prices.keys():
            data = self.get_ticker(symbol)
            if data:
                all_data.append(data)
        
        print(f"📊 全通貨ペア価格取得完了: {len(all_data)}件")
        return all_data
    
    def simulate_price_feed(self, symbol: str, duration_seconds: int = 60):
        """
        指定時間の間、リアルタイム価格変動をシミュレート
        
        Args:
            symbol (str): 通貨ペア
            duration_seconds (int): シミュレート時間（秒）
        """
        print(f"🔄 価格フィードシミュレート開始: {symbol} ({duration_seconds}秒間)")
        
        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            data = self.get_ticker(symbol)
            if data:
                yield data
            
            # 1秒間隔で更新
            time.sleep(1)
        
        print(f"✅ 価格フィードシミュレート終了: {symbol}")
    
    def get_account_info(self) -> Dict:
        """
        口座情報のモックデータ
        
        Returns:
            Dict: 口座情報
        """
        return {
            'account_id': 'MOCK_ACCOUNT_123',
            'balance': Decimal('1000000.00'),  # 100万円
            'currency': 'JPY',
            'margin_ratio': Decimal('1000.0'),  # 1000倍レバレッジ
            'available_margin': Decimal('950000.00'),
            'used_margin': Decimal('50000.00'),
            'unrealized_pnl': Decimal('12500.50'),
            'total_positions': 3,
            'last_updated': datetime.now().isoformat()
        }
    
    def place_mock_order(self, symbol: str, side: str, size: int, 
                        order_type: str = 'MARKET') -> Dict:
        """
        モック注文発注
        
        Args:
            symbol (str): 通貨ペア
            side (str): 'BUY' または 'SELL'
            size (int): 取引数量
            order_type (str): 注文種別
            
        Returns:
            Dict: 注文結果
        """
        # 現在価格取得
        market_data = self.get_ticker(symbol)
        if not market_data:
            return {'status': 'ERROR', 'message': f'Unknown symbol: {symbol}'}
        
        # 約定価格決定
        if side == 'BUY':
            execution_price = market_data.ask
        else:
            execution_price = market_data.bid
        
        # ランダムな注文ID生成
        order_id = f"MOCK_{int(time.time())}_{random.randint(1000, 9999)}"
        
        order_result = {
            'order_id': order_id,
            'symbol': symbol,
            'side': side,
            'size': size,
            'order_type': order_type,
            'status': 'EXECUTED',
            'execution_price': str(execution_price),
            'execution_time': datetime.now().isoformat(),
            'commission': str(Decimal(size) * Decimal('0.002')),  # 0.002円/通貨
        }
        
        print(f"✅ モック注文約定: {side} {size} {symbol} @ {execution_price}")
        return order_result

# 使用例とテスト用関数
def test_mock_client():
    """モッククライアントのテスト"""
    print("🧪 GMO Mock Client テスト開始\n")
    
    # クライアント初期化
    client = GMOMockClient()
    
    # 1. 単一通貨ペア価格取得
    print("\n1. USD_JPY 価格取得:")
    usd_jpy = client.get_ticker('USD_JPY')
    if usd_jpy:
        print(f"   Bid: {usd_jpy.bid}, Ask: {usd_jpy.ask}")
        print(f"   Spread: {usd_jpy.spread}, Mid: {usd_jpy.mid_price}")
    
    # 2. 全通貨ペア価格取得  
    print("\n2. 全通貨ペア価格取得:")
    all_tickers = client.get_all_tickers()
    for ticker in all_tickers:
        print(f"   {ticker.symbol}: {ticker.mid_price}")
    
    # 3. 口座情報取得
    print("\n3. 口座情報取得:")
    account = client.get_account_info()
    print(f"   残高: {account['balance']} {account['currency']}")
    print(f"   含み損益: {account['unrealized_pnl']}")
    
    # 4. モック注文
    print("\n4. モック注文テスト:")
    order = client.place_mock_order('USD_JPY', 'BUY', 10000)
    print(f"   注文ID: {order['order_id']}")
    print(f"   約定価格: {order['execution_price']}")
    
    print("\n✅ テスト完了")

if __name__ == "__main__":
    test_mock_client()