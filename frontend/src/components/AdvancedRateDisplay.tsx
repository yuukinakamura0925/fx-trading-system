/**
 * 高機能レート表示コンポーネント
 * - 更新間隔調整
 * - 通貨ペア選択
 * - タブ管理
 */

import React, { useEffect, useState, useRef } from 'react';
import { gmoFXClient, FormattedRate } from '@/lib/gmo-fx-client';
import {
  Play,
  Pause,
  Settings,
  RefreshCw,
  X,
  Clock,
  BookOpen,
  Plus
} from 'lucide-react';

// 通貨ペアの定義
const CURRENCY_PAIRS = [
  { symbol: 'USD_JPY', name: '米ドル/円', category: 'major' },
  { symbol: 'EUR_JPY', name: 'ユーロ/円', category: 'major' },
  { symbol: 'GBP_JPY', name: 'ポンド/円', category: 'major' },
  { symbol: 'AUD_JPY', name: '豪ドル/円', category: 'major' },
  { symbol: 'NZD_JPY', name: 'NZドル/円', category: 'minor' },
  { symbol: 'CAD_JPY', name: 'カナダドル/円', category: 'minor' },
  { symbol: 'CHF_JPY', name: 'スイスフラン/円', category: 'minor' },
  { symbol: 'TRY_JPY', name: 'トルコリラ/円', category: 'exotic' },
  { symbol: 'ZAR_JPY', name: '南アランド/円', category: 'exotic' },
  { symbol: 'MXN_JPY', name: 'メキシコペソ/円', category: 'exotic' },
  { symbol: 'EUR_USD', name: 'ユーロ/米ドル', category: 'major' },
  { symbol: 'GBP_USD', name: 'ポンド/米ドル', category: 'major' },
  { symbol: 'AUD_USD', name: '豪ドル/米ドル', category: 'major' },
  { symbol: 'NZD_USD', name: 'NZドル/米ドル', category: 'minor' },
];

// 更新間隔の選択肢
const UPDATE_INTERVALS = [
  { value: 1000, label: '1秒', description: '最高頻度' },
  { value: 2000, label: '2秒', description: '超高頻度' },
  { value: 3000, label: '3秒', description: '高頻度' },
  { value: 5000, label: '5秒', description: '標準' },
  { value: 10000, label: '10秒', description: '低頻度' },
  { value: 15000, label: '15秒', description: '省電力' },
  { value: 30000, label: '30秒', description: '超省電力' },
  { value: 60000, label: '1分', description: '長期監視' },
];

// タブの定義
interface CurrencyTab {
  id: string;
  name: string;
  symbols: string[];
  color: string;
}

const DEFAULT_TABS: CurrencyTab[] = [
  {
    id: 'major',
    name: 'メジャー',
    symbols: ['USD_JPY', 'EUR_JPY', 'GBP_JPY', 'EUR_USD'],
    color: 'blue'
  },
  {
    id: 'jpy',
    name: '円ペア',
    symbols: ['USD_JPY', 'EUR_JPY', 'GBP_JPY', 'AUD_JPY', 'NZD_JPY'],
    color: 'green'
  },
  {
    id: 'usd',
    name: 'ドルペア',
    symbols: ['EUR_USD', 'GBP_USD', 'AUD_USD', 'NZD_USD'],
    color: 'purple'
  }
];

interface AdvancedRateDisplayProps {
  initialInterval?: number;
  showSpread?: boolean;
  compact?: boolean;
}

export const AdvancedRateDisplay: React.FC<AdvancedRateDisplayProps> = ({
  initialInterval = 10000, // デフォルトをより長めに（10秒）
  showSpread = true,
  compact = false
}) => {
  // ステート管理
  const [rates, setRates] = useState<FormattedRate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(true);
  const [updateInterval, setUpdateInterval] = useState(initialInterval);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [marketStatus, setMarketStatus] = useState<string>('UNKNOWN');

  // タブとフィルター関連
  const [tabs, setTabs] = useState<CurrencyTab[]>(DEFAULT_TABS);
  const [activeTabId, setActiveTabId] = useState('major');
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>(DEFAULT_TABS[0].symbols);
  const [showSettings, setShowSettings] = useState(false);
  const [showTabManager, setShowTabManager] = useState(false);

  // 価格履歴管理（useRefで最新値を参照）
  const priceHistoryRef = useRef<Record<string, number>>({});
  const [priceDirections, setPriceDirections] = useState<Record<string, 'up' | 'down' | 'none'>>({});

  // アクティブなタブ
  const activeTab = tabs.find(tab => tab.id === activeTabId);

  // 定期更新の設定
  useEffect(() => {
    if (!isRunning) return;

    const fetchData = async () => {
      try {
        // FXステータス確認
        const status = await gmoFXClient.getStatus();
        setMarketStatus(status.data.status);

        // レート取得
        const ticker = await gmoFXClient.getTicker();
        let formattedRates = gmoFXClient.formatRates(ticker);

        // 選択された通貨ペアでフィルター
        formattedRates = formattedRates.filter(rate =>
          selectedSymbols.includes(rate.symbol)
        );


        // 価格変動を検出
        const newDirections: Record<string, 'up' | 'down' | 'none'> = {};
        const currentPriceHistory = priceHistoryRef.current;

        formattedRates.forEach(rate => {
          const symbol = rate.symbol;
          const currentPrice = rate.bid;
          const previousPrice = currentPriceHistory[symbol];

          if (previousPrice !== undefined) {
            const changeThreshold = symbol.includes('JPY') ? 0.001 : 0.00001;
            const priceChange = Math.abs(currentPrice - previousPrice);

            if (priceChange >= changeThreshold) {
              if (currentPrice > previousPrice) {
                newDirections[symbol] = 'up';
              } else {
                newDirections[symbol] = 'down';
              }
            } else {
              newDirections[symbol] = 'none';
            }
          } else {
            newDirections[symbol] = 'none';
          }
        });

        // 価格履歴を更新
        const newHistory: Record<string, number> = {};
        formattedRates.forEach(rate => {
          newHistory[rate.symbol] = rate.bid;
        });
        priceHistoryRef.current = newHistory;

        // 価格方向を更新
        setPriceDirections({...newDirections});

        setRates(formattedRates);
        setLastUpdate(new Date());
        setLoading(false);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : '不明なエラー');
        setLoading(false);
      }
    };

    // 初回取得
    fetchData();

    // 定期更新
    const interval = setInterval(fetchData, updateInterval);

    return () => clearInterval(interval);
  }, [updateInterval, isRunning, selectedSymbols]); // 最小限の依存関係のみ

  // タブ変更時の処理
  useEffect(() => {
    const tab = tabs.find(t => t.id === activeTabId);
    if (tab) {
      setSelectedSymbols(tab.symbols);
    }
  }, [activeTabId, tabs]);

  // 更新の開始/停止
  const toggleUpdates = () => {
    setIsRunning(!isRunning);
  };

  // 手動更新
  const manualUpdate = async () => {
    try {
      const status = await gmoFXClient.getStatus();
      setMarketStatus(status.data.status);

      const ticker = await gmoFXClient.getTicker();
      let formattedRates = gmoFXClient.formatRates(ticker);

      formattedRates = formattedRates.filter(rate =>
        selectedSymbols.includes(rate.symbol)
      );

      // 価格変動を検出
      const newDirections: Record<string, 'up' | 'down' | 'none'> = {};
      const currentPriceHistory = priceHistoryRef.current;

      formattedRates.forEach(rate => {
        const symbol = rate.symbol;
        const currentPrice = rate.bid;
        const previousPrice = currentPriceHistory[symbol];

        if (previousPrice !== undefined) {
          const changeThreshold = symbol.includes('JPY') ? 0.001 : 0.00001;
          const priceChange = Math.abs(currentPrice - previousPrice);

          if (priceChange >= changeThreshold) {
            if (currentPrice > previousPrice) {
              newDirections[symbol] = 'up';
            } else {
              newDirections[symbol] = 'down';
            }
          } else {
            newDirections[symbol] = 'none';
          }
        } else {
          newDirections[symbol] = 'none';
        }
      });

      // 価格履歴を更新
      const newHistory: Record<string, number> = {};
      formattedRates.forEach(rate => {
        newHistory[rate.symbol] = rate.bid;
      });
      priceHistoryRef.current = newHistory;

      // 価格方向を更新
      setPriceDirections(newDirections);

      setRates(formattedRates);
      setLastUpdate(new Date());
      setLoading(false);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '不明なエラー');
      setLoading(false);
    }
  };

  // 更新間隔の変更
  const handleIntervalChange = (newInterval: number) => {
    setUpdateInterval(newInterval);
  };

  // 新しいタブの作成
  const createNewTab = () => {
    const newTab: CurrencyTab = {
      id: `tab_${Date.now()}`,
      name: `カスタム${tabs.length + 1}`,
      symbols: ['USD_JPY'],
      color: 'gray'
    };
    setTabs([...tabs, newTab]);
    setActiveTabId(newTab.id);
  };

  // タブの削除
  const deleteTab = (tabId: string) => {
    if (tabs.length <= 1) return; // 最低1つは残す

    const newTabs = tabs.filter(tab => tab.id !== tabId);
    setTabs(newTabs);

    if (activeTabId === tabId) {
      setActiveTabId(newTabs[0].id);
    }
  };

  // タブの設定更新
  const updateTab = (tabId: string, updates: Partial<CurrencyTab>) => {
    setTabs(tabs.map(tab =>
      tab.id === tabId ? { ...tab, ...updates } : tab
    ));
  };

  // 設定パネル
  const SettingsPanel = () => (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg w-80">
      <div className="flex justify-between items-center p-3 border-b border-gray-100">
        <h3 className="font-bold text-sm">⚙️ 表示設定</h3>
        <button
          onClick={() => setShowSettings(false)}
          className="p-1 hover:bg-gray-100 rounded text-gray-400 hover:text-gray-600"
        >
          <X className="h-3 w-3" />
        </button>
      </div>

      <div className="p-3">
        {/* 更新間隔設定 */}
        <div className="mb-3">
          <label className="flex items-center text-xs font-medium text-gray-700 mb-2">
            <Clock className="h-3 w-3 mr-1" />
            更新間隔
          </label>
          <div className="grid grid-cols-3 gap-1">
            {UPDATE_INTERVALS.map(interval => (
              <button
                key={interval.value}
                onClick={() => handleIntervalChange(interval.value)}
                className={`p-2 text-xs rounded border transition-colors ${
                  updateInterval === interval.value
                    ? 'bg-blue-500 border-blue-500 text-white'
                    : 'hover:bg-gray-50 border-gray-200 text-gray-700'
                }`}
              >
                <div className="font-medium">{interval.label}</div>
              </button>
            ))}
          </div>
        </div>

        {/* 現在の設定表示 */}
        <div className="text-xs bg-gray-50 p-2 rounded border">
          <div className="flex justify-between items-center mb-1">
            <span className="text-gray-600">更新間隔:</span>
            <span className="font-medium">{updateInterval / 1000}秒</span>
          </div>
          <div className="flex justify-between items-center mb-1">
            <span className="text-gray-600">表示通貨:</span>
            <span className="font-medium">{selectedSymbols.length}ペア</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600">ステータス:</span>
            <span className={`font-medium ${isRunning ? 'text-green-600' : 'text-red-600'}`}>
              {isRunning ? '●更新中' : '⏸停止中'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );

  // タブ管理パネル
  const TabManagerPanel = () => (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg w-96 max-h-96 overflow-y-auto">
      <div className="flex justify-between items-center p-3 border-b border-gray-100 sticky top-0 bg-white">
        <h3 className="font-bold text-sm">📁 タブ管理</h3>
        <button
          onClick={() => setShowTabManager(false)}
          className="p-1 hover:bg-gray-100 rounded text-gray-400 hover:text-gray-600"
        >
          <X className="h-3 w-3" />
        </button>
      </div>

      <div className="p-3">
        {/* 既存タブの編集 */}
        <div className="space-y-2 mb-3">
          {tabs.map(tab => (
            <div key={tab.id} className="border border-gray-200 rounded p-2">
              <div className="flex justify-between items-center mb-2">
                <input
                  type="text"
                  value={tab.name}
                  onChange={(e) => updateTab(tab.id, { name: e.target.value })}
                  className="text-sm font-medium bg-transparent border-none focus:outline-none flex-1"
                />
                {tabs.length > 1 && (
                  <button
                    onClick={() => deleteTab(tab.id)}
                    className="text-red-500 hover:bg-red-50 p-1 rounded ml-2"
                  >
                    <X className="h-3 w-3" />
                  </button>
                )}
              </div>

              {/* 通貨ペア選択 */}
              <div className="text-xs text-gray-600 mb-1">
                選択中: {tab.symbols.length}ペア
              </div>
              <div className="grid grid-cols-3 gap-1">
                {CURRENCY_PAIRS.map(pair => (
                  <label key={pair.symbol} className="flex items-center text-xs">
                    <input
                      type="checkbox"
                      checked={tab.symbols.includes(pair.symbol)}
                      onChange={(e) => {
                        const newSymbols = e.target.checked
                          ? [...tab.symbols, pair.symbol]
                          : tab.symbols.filter(s => s !== pair.symbol);
                        updateTab(tab.id, { symbols: newSymbols });
                      }}
                      className="mr-1 w-3 h-3"
                    />
                    <span className="truncate">{pair.symbol}</span>
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* 新しいタブ作成 */}
        <button
          onClick={createNewTab}
          className="w-full p-2 border border-dashed border-gray-300 rounded hover:bg-gray-50 text-xs flex items-center justify-center"
        >
          <Plus className="h-3 w-3 mr-1" />
          新しいタブを作成
        </button>
      </div>
    </div>
  );

  // レートアイテムコンポーネント
  const RateItem: React.FC<{ rate: FormattedRate }> = ({ rate }) => {
    const priceDirection = priceDirections[rate.symbol] || 'none';

    return (
      <div
        className="border rounded p-2 shadow-sm hover:shadow transition-all duration-300"
        style={{
          // 価格変動をカード背景色で表現
          backgroundColor:
            priceDirection === 'up' ? '#f0f9ff' :     // 淺い青
            priceDirection === 'down' ? '#fef2f2' :   // 淺い赤
            '#ffffff',                                // 白
          borderColor:
            priceDirection === 'up' ? '#3b82f6' :     // 青のボーダー
            priceDirection === 'down' ? '#ef4444' :   // 赤のボーダー
            '#e5e7eb',                                // グレーのボーダー
          borderWidth: priceDirection !== 'none' ? '2px' : '1px'
        }}
      >
        <div className="flex justify-between items-center mb-1">
          <div className="font-bold text-sm">
            {rate.symbol}
            {priceDirection === 'up' && <span className="ml-1 text-blue-600 text-xs">↑</span>}
            {priceDirection === 'down' && <span className="ml-1 text-red-600 text-xs">↓</span>}
          </div>
          <span className={`text-xs px-1 py-0.5 rounded ${
            rate.status === 'OPEN'
              ? 'bg-blue-100 text-blue-700'
              : 'bg-gray-100 text-gray-600'
          }`}>
            {rate.status}
          </span>
        </div>

        <div className="text-right mb-1">
          <div className="font-bold text-gray-900">
            {rate.bid.toFixed(3)}
          </div>
          <div className="text-xs text-gray-600">
            {rate.ask.toFixed(3)}
          </div>
        </div>

        {showSpread && (
          <div className="text-xs text-gray-500 text-center">
            {rate.spreadPips.toFixed(1)}p
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* ヘッダー */}
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-3">
          <h2 className="text-xl font-bold">FXレート（高機能版）</h2>
          <div className={`w-3 h-3 rounded-full animate-pulse ${
            marketStatus === 'OPEN' ? 'bg-green-500' :
            marketStatus === 'CLOSE' ? 'bg-gray-500' :
            'bg-orange-500'
          }`}></div>
          <span className="text-sm text-gray-600">
            市場: {marketStatus}
          </span>
        </div>

        {/* コントロールボタン */}
        <div className="flex items-center space-x-2">
          <button
            onClick={toggleUpdates}
            className={`p-2 rounded ${
              isRunning
                ? 'bg-red-100 text-red-600 hover:bg-red-200'
                : 'bg-green-100 text-green-600 hover:bg-green-200'
            }`}
            title={isRunning ? '更新停止' : '更新開始'}
          >
            {isRunning ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          </button>

          <button
            onClick={manualUpdate}
            className="p-2 rounded bg-blue-100 text-blue-600 hover:bg-blue-200"
            title="手動更新"
          >
            <RefreshCw className="h-4 w-4" />
          </button>

          <div className="relative">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="p-2 rounded bg-gray-100 text-gray-600 hover:bg-gray-200"
              title="設定"
            >
              <Settings className="h-4 w-4" />
            </button>
            {showSettings && (
              <div className="absolute top-10 right-0 z-10">
                <SettingsPanel />
              </div>
            )}
          </div>

          <div className="relative">
            <button
              onClick={() => setShowTabManager(!showTabManager)}
              className="p-2 rounded bg-purple-100 text-purple-600 hover:bg-purple-200"
              title="タブ管理"
            >
              <BookOpen className="h-4 w-4" />
            </button>
            {showTabManager && (
              <div className="absolute top-10 right-0 z-10">
                <TabManagerPanel />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* タブナビゲーション */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTabId(tab.id)}
            className={`px-3 py-2 text-sm font-medium rounded transition-colors ${
              activeTabId === tab.id
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            {tab.name}
            <span className="ml-1 text-xs text-gray-400">
              ({tab.symbols.length})
            </span>
          </button>
        ))}
      </div>

      {/* ステータス情報 */}
      <div className="flex justify-between items-center text-sm text-gray-500">
        <div>
          更新間隔: {updateInterval / 1000}秒 |
          表示中: {selectedSymbols.length}ペア |
          ステータス: {isRunning ? '自動更新中' : '停止中'}
        </div>
        <div>
          最終更新: {lastUpdate.toLocaleTimeString('ja-JP')}
        </div>
      </div>

      {/* エラー表示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          <strong>エラー:</strong> {error}
          <button
            onClick={manualUpdate}
            className="ml-4 text-sm underline hover:no-underline"
          >
            再試行
          </button>
        </div>
      )}

      {/* ローディング表示 */}
      {loading && (
        <div className="flex justify-center items-center p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3">レート取得中...</span>
        </div>
      )}

      {/* レート一覧 */}
      {!loading && (
        <div className={compact
          ? 'space-y-1'
          : 'grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-2'
        }>
          {rates.length > 0 ? (
            rates.map(rate => (
              <RateItem key={rate.symbol} rate={rate} />
            ))
          ) : (
            <div className="text-gray-500 text-center py-8 col-span-full">
              表示可能なレートがありません
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AdvancedRateDisplay;