/**
 * 全市場データ表示コンポーネント
 * - 開閉可能なセクション
 * - 全てのGMO APIデータを表示
 */

import React, { useEffect, useState, useRef } from 'react';
import {
  gmoFXClient,
  FormattedRate,
  OrderBooksResponse,
  TradeEntry,
  KlineResponse,
  SymbolsResponse
} from '@/lib/gmo-fx-client';
import {
  ChevronDown,
  ChevronUp,
  Activity,
  BarChart3,
  TrendingUp,
  Settings,
  Clock,
  RefreshCw
} from 'lucide-react';

interface AllMarketDataProps {
  initialInterval?: number;
  selectedSymbol?: string;
}

export const AllMarketData: React.FC<AllMarketDataProps> = ({
  initialInterval = 10000,
  selectedSymbol = 'USD_JPY'
}) => {
  // ステート管理
  const [rates, setRates] = useState<FormattedRate[]>([]);
  const [orderBooks, setOrderBooks] = useState<OrderBooksResponse | null>(null);
  const [trades, setTrades] = useState<TradeEntry[]>([]);
  const [klines, setKlines] = useState<KlineResponse | null>(null);
  const [symbols, setSymbols] = useState<SymbolsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(true);
  const [updateInterval, setUpdateInterval] = useState(initialInterval);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  // WebSocket参照
  const tradesWsRef = useRef<WebSocket | null>(null);

  // 開閉状態管理
  const [expandedSections, setExpandedSections] = useState({
    rates: true,
    orderbooks: false,
    trades: false,
    klines: false,
    symbols: false
  });

  // セクション開閉トグル
  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // REST APIデータ取得
  const fetchRestData = async () => {
    try {
      setLoading(true);

      // 並行してREST APIデータ取得
      const [
        tickerResponse,
        orderBooksResponse,
        klinesResponse,
        symbolsResponse
      ] = await Promise.all([
        gmoFXClient.getTicker(),
        gmoFXClient.getOrderBooks(selectedSymbol),
        gmoFXClient.getKlines(selectedSymbol, '1min', new Date().toISOString().split('T')[0].replace(/-/g, '')),
        gmoFXClient.getSymbols()
      ]);

      // データを整形・設定
      const formattedRates = gmoFXClient.formatRates(tickerResponse);
      setRates(formattedRates);
      setOrderBooks(orderBooksResponse);
      setKlines(klinesResponse);
      setSymbols(symbolsResponse);

      setLastUpdate(new Date());
      setLoading(false);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '不明なエラー');
      setLoading(false);
    }
  };

  // WebSocketでTrades購読
  const subscribeToTrades = () => {
    if (tradesWsRef.current) {
      tradesWsRef.current.close();
    }

    const ws = gmoFXClient.subscribeToTrades(
      selectedSymbol,
      (trade) => {
        setTrades(prev => [trade, ...prev.slice(0, 19)]); // 最新20件を保持
      },
      (error) => {
        console.error('Trades WebSocketエラー:', error);
      }
    );

    tradesWsRef.current = ws;
  };

  // 定期更新の設定
  useEffect(() => {
    if (!isRunning) return;

    fetchRestData();
    subscribeToTrades();

    const interval = setInterval(fetchRestData, updateInterval);

    return () => {
      clearInterval(interval);
      if (tradesWsRef.current) {
        tradesWsRef.current.close();
      }
    };
  }, [updateInterval, isRunning, selectedSymbol]);

  // セクションコンポーネント
  const Section: React.FC<{
    title: string;
    icon: React.ReactNode;
    sectionKey: keyof typeof expandedSections;
    children: React.ReactNode;
    count?: number;
  }> = ({ title, icon, sectionKey, children, count }) => {
    const isExpanded = expandedSections[sectionKey];

    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <button
          onClick={() => toggleSection(sectionKey)}
          className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center space-x-3">
            {icon}
            <h3 className="text-lg font-bold text-gray-800">{title}</h3>
            {count !== undefined && (
              <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">
                {count}件
              </span>
            )}
          </div>
          {isExpanded ? (
            <ChevronUp className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          )}
        </button>

        {isExpanded && (
          <div className="px-4 pb-4 border-t border-gray-100">
            {children}
          </div>
        )}
      </div>
    );
  };

  // レート表示コンポーネント
  const RatesSection = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
      {rates.slice(0, 6).map(rate => (
        <div key={rate.symbol} className="border rounded-lg p-3">
          <div className="flex justify-between items-center">
            <div>
              <div className="font-bold">{rate.symbol}</div>
              <div className="text-sm text-gray-500">{rate.displayName}</div>
            </div>
            <div className="text-right">
              <div className="font-bold">{rate.bid.toFixed(3)}</div>
              <div className="text-sm text-gray-600">Ask: {rate.ask.toFixed(3)}</div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );

  // 板情報表示コンポーネント
  const OrderBooksSection = () => {
    if (!orderBooks?.data?.[0]) return <div className="text-gray-500 text-center py-4">データなし</div>;

    const orderBook = orderBooks.data[0];
    return (
      <div className="mt-4">
        <div className="grid grid-cols-2 gap-4">
          {/* 売り板 */}
          <div>
            <h4 className="font-bold text-red-600 mb-2">売り板 (Ask)</h4>
            <div className="space-y-1">
              {orderBook.asks.slice(0, 10).map((ask, index) => (
                <div key={index} className="flex justify-between text-sm bg-red-50 p-2 rounded">
                  <span>{parseFloat(ask.price).toFixed(3)}</span>
                  <span>{parseFloat(ask.size).toFixed(0)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* 買い板 */}
          <div>
            <h4 className="font-bold text-blue-600 mb-2">買い板 (Bid)</h4>
            <div className="space-y-1">
              {orderBook.bids.slice(0, 10).map((bid, index) => (
                <div key={index} className="flex justify-between text-sm bg-blue-50 p-2 rounded">
                  <span>{parseFloat(bid.price).toFixed(3)}</span>
                  <span>{parseFloat(bid.size).toFixed(0)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  // 約定履歴表示コンポーネント
  const TradesSection = () => {
    if (!trades || trades.length === 0) {
      return (
        <div className="text-gray-500 text-center py-4">
          WebSocket接続中...リアルタイム約定履歴を取得しています
        </div>
      );
    }

    return (
      <div className="mt-4">
        <div className="space-y-2">
          {trades.slice(0, 20).map((trade, index) => (
            <div key={index} className="flex justify-between items-center p-2 border rounded">
              <div className="flex items-center space-x-3">
                <span className={`px-2 py-1 rounded text-xs font-bold ${
                  trade.side === 'BUY' ? 'bg-blue-100 text-blue-800' : 'bg-red-100 text-red-800'
                }`}>
                  {trade.side}
                </span>
                <span className="font-mono">{parseFloat(trade.price).toFixed(3)}</span>
              </div>
              <div className="text-right">
                <div className="text-sm">{parseFloat(trade.size).toFixed(0)}</div>
                <div className="text-xs text-gray-500">
                  {new Date(trade.timestamp).toLocaleTimeString('ja-JP')}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // ローソク足表示コンポーネント
  const KlinesSection = () => {
    if (!klines?.data) return <div className="text-gray-500 text-center py-4">データなし</div>;

    return (
      <div className="mt-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {klines.data.slice(-10).map((kline, index) => (
            <div key={index} className="border rounded p-3">
              <div className="text-sm text-gray-500 mb-1">
                {new Date(kline.openTime).toLocaleString('ja-JP')}
              </div>
              <div className="grid grid-cols-4 gap-2 text-sm">
                <div>開: {parseFloat(kline.open).toFixed(3)}</div>
                <div>高: {parseFloat(kline.high).toFixed(3)}</div>
                <div>安: {parseFloat(kline.low).toFixed(3)}</div>
                <div>終: {parseFloat(kline.close).toFixed(3)}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // 取引ルール表示コンポーネント
  const SymbolsSection = () => {
    if (!symbols?.data) return <div className="text-gray-500 text-center py-4">データなし</div>;

    return (
      <div className="mt-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {symbols.data.map((symbol, index) => (
            <div key={index} className="border rounded p-3">
              <div className="font-bold mb-2">{symbol.symbol}</div>
              <div className="text-sm space-y-1">
                <div>最小注文: {symbol.minOpenOrderSize}</div>
                <div>最大注文: {symbol.maxOrderSize}</div>
                <div>注文単位: {symbol.sizeStep}</div>
                <div>価格単位: {symbol.tickSize}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-3">
          <h2 className="text-xl font-bold">全市場データ</h2>
          <div className="text-sm text-gray-500">
            対象: {selectedSymbol}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsRunning(!isRunning)}
            className={`px-3 py-2 rounded text-sm font-medium ${
              isRunning
                ? 'bg-red-100 text-red-600 hover:bg-red-200'
                : 'bg-green-100 text-green-600 hover:bg-green-200'
            }`}
          >
            {isRunning ? '停止' : '開始'}
          </button>

          <button
            onClick={() => {
              fetchRestData();
              subscribeToTrades();
            }}
            className="p-2 rounded bg-blue-100 text-blue-600 hover:bg-blue-200"
            title="手動更新"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* ステータス */}
      <div className="text-sm text-gray-500">
        最終更新: {lastUpdate.toLocaleTimeString('ja-JP')} |
        更新間隔: {updateInterval / 1000}秒 |
        ステータス: {isRunning ? '自動更新中' : '停止中'}
      </div>

      {/* エラー表示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          <strong>エラー:</strong> {error}
        </div>
      )}

      {/* ローディング */}
      {loading && (
        <div className="flex justify-center items-center p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3">データ取得中...</span>
        </div>
      )}

      {/* データセクション */}
      {!loading && (
        <div className="space-y-4">
          {/* レート情報 */}
          <Section
            title="リアルタイムレート"
            icon={<Activity className="h-5 w-5 text-green-600" />}
            sectionKey="rates"
            count={rates.length}
          >
            <RatesSection />
          </Section>

          {/* 板情報 */}
          <Section
            title="板情報 (OrderBooks)"
            icon={<BarChart3 className="h-5 w-5 text-blue-600" />}
            sectionKey="orderbooks"
          >
            <OrderBooksSection />
          </Section>

          {/* 約定履歴 */}
          <Section
            title="約定履歴 (Trades)"
            icon={<TrendingUp className="h-5 w-5 text-purple-600" />}
            sectionKey="trades"
          >
            <TradesSection />
          </Section>

          {/* ローソク足 */}
          <Section
            title="ローソク足 (Klines)"
            icon={<BarChart3 className="h-5 w-5 text-orange-600" />}
            sectionKey="klines"
          >
            <KlinesSection />
          </Section>

          {/* 取引ルール */}
          <Section
            title="取引ルール (Symbols)"
            icon={<Settings className="h-5 w-5 text-gray-600" />}
            sectionKey="symbols"
          >
            <SymbolsSection />
          </Section>
        </div>
      )}
    </div>
  );
};

export default AllMarketData;