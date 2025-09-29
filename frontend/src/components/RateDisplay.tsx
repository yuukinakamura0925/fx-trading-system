/**
 * リアルタイムレート表示コンポーネント
 * GMO Public APIから直接レートを取得して表示
 */

import React, { useEffect, useState, useCallback } from 'react';
import { gmoFXClient, FormattedRate } from '@/lib/gmo-fx-client';

// レート表示のプロップス
interface RateDisplayProps {
  symbols?: string[];        // 表示する通貨ペア（未指定なら全て）
  updateInterval?: number;   // 更新間隔（ミリ秒）
  showSpread?: boolean;      // スプレッド表示
  compact?: boolean;         // コンパクト表示
}

/**
 * 個別レート表示コンポーネント
 */
const RateItem: React.FC<{ rate: FormattedRate; showSpread?: boolean }> = ({
  rate,
  showSpread = true
}) => {
  // 前回値との比較用
  const [previousBid, setPreviousBid] = useState(rate.bid);
  const [priceDirection, setPriceDirection] = useState<'up' | 'down' | 'none'>('none');

  useEffect(() => {
    if (rate.bid > previousBid) {
      setPriceDirection('up');
    } else if (rate.bid < previousBid) {
      setPriceDirection('down');
    }
    setPreviousBid(rate.bid);

    // アニメーション終了後にリセット
    const timer = setTimeout(() => setPriceDirection('none'), 500);
    return () => clearTimeout(timer);
  }, [rate.bid]);

  return (
    <div className="border rounded-lg p-4 bg-white shadow-sm hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="font-bold text-lg">{rate.symbol}</h3>
          <p className="text-sm text-gray-500">{rate.displayName}</p>
        </div>
        <div className="text-right">
          <div className={`text-2xl font-bold transition-colors duration-300 ${
            priceDirection === 'up' ? 'text-green-600' :
            priceDirection === 'down' ? 'text-red-600' :
            'text-gray-900'
          }`}>
            {rate.bid.toFixed(3)}
            {priceDirection === 'up' && <span className="text-xs ml-1">↑</span>}
            {priceDirection === 'down' && <span className="text-xs ml-1">↓</span>}
          </div>
          <div className="text-sm text-gray-600">
            Ask: {rate.ask.toFixed(3)}
          </div>
          {showSpread && (
            <div className="text-xs text-gray-500 mt-1">
              スプレッド: {rate.spreadPips.toFixed(1)}pips
            </div>
          )}
        </div>
      </div>
      <div className="mt-2 flex justify-between items-center">
        <span className={`text-xs px-2 py-1 rounded ${
          rate.status === 'OPEN'
            ? 'bg-green-100 text-green-800'
            : 'bg-gray-100 text-gray-600'
        }`}>
          {rate.status}
        </span>
        <span className="text-xs text-gray-400">
          {new Date(rate.timestamp).toLocaleTimeString('ja-JP')}
        </span>
      </div>
    </div>
  );
};

/**
 * リアルタイムレート表示メインコンポーネント
 */
export const RateDisplay: React.FC<RateDisplayProps> = ({
  symbols,
  updateInterval = 5000,
  showSpread = true,
  compact = false
}) => {
  const [rates, setRates] = useState<FormattedRate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [marketStatus, setMarketStatus] = useState<string>('UNKNOWN');
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  // レート取得処理
  const fetchRates = useCallback(async () => {
    try {
      // FXステータス確認
      const status = await gmoFXClient.getStatus();
      setMarketStatus(status.data.status);

      // レート取得
      const ticker = await gmoFXClient.getTicker();
      let formattedRates = gmoFXClient.formatRates(ticker);

      // 特定の通貨ペアでフィルター
      if (symbols && symbols.length > 0) {
        formattedRates = formattedRates.filter((rate: { symbol: string; }) =>
          symbols.includes(rate.symbol)
        );
      }

      setRates(formattedRates);
      setLastUpdate(new Date());
      setLoading(false);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '不明なエラー');
      setLoading(false);
    }
  }, [symbols]);

  // 定期更新の設定
  useEffect(() => {
    // 初回取得
    fetchRates();

    // 定期更新開始
    const cleanup = gmoFXClient.startRateMonitoring(
      (newRates: any[]) => {
        let filteredRates = newRates;
        if (symbols && symbols.length > 0) {
          filteredRates = newRates.filter(rate =>
            symbols.includes(rate.symbol)
          );
        }
        setRates(filteredRates);
        setLastUpdate(new Date());
      },
      updateInterval
    );

    return cleanup;
  }, [symbols, updateInterval]);

  // ローディング表示
  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3">レート取得中...</span>
      </div>
    );
  }

  // エラー表示
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        <strong>エラー:</strong> {error}
        <button
          onClick={fetchRates}
          className="ml-4 text-sm underline hover:no-underline"
        >
          再試行
        </button>
      </div>
    );
  }

  // マーケット状態表示
  const marketStatusColor =
    marketStatus === 'OPEN' ? 'bg-green-500' :
    marketStatus === 'CLOSE' ? 'bg-gray-500' :
    'bg-orange-500';

  return (
    <div className="space-y-4">
      {/* ヘッダー */}
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-3">
          <h2 className="text-xl font-bold">FXレート</h2>
          <div className={`w-3 h-3 rounded-full ${marketStatusColor} animate-pulse`}></div>
          <span className="text-sm text-gray-600">
            市場: {marketStatus}
          </span>
        </div>
        <div className="text-sm text-gray-500">
          最終更新: {lastUpdate.toLocaleTimeString('ja-JP')}
        </div>
      </div>

      {/* レート一覧 */}
      <div className={compact ? 'space-y-2' : 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'}>
        {rates.length > 0 ? (
          rates.map(rate => (
            <RateItem
              key={rate.symbol}
              rate={rate}
              showSpread={showSpread}
            />
          ))
        ) : (
          <div className="text-gray-500 text-center py-8 col-span-full">
            表示可能なレートがありません
          </div>
        )}
      </div>

      {/* 更新インジケーター */}
      <div className="flex justify-center">
        <div className="text-xs text-gray-400">
          {updateInterval / 1000}秒ごとに自動更新
        </div>
      </div>
    </div>
  );
};

export default RateDisplay;