// FX過去データ表示コンポーネント
'use client'

import { useState, useEffect } from 'react'
import {
  Clock,
  BarChart3,
  RefreshCw,
  AlertCircle,
  Play,
  Pause,
  Table,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  LineChart
} from 'lucide-react'
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Bar
} from 'recharts'

// OHLC データポイントの型定義
interface OHLCData {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

// タイムフレームデータの型定義
interface TimeframeData {
  timeframe: string
  description: string
  interval: string
  days: number
  data: OHLCData[]
  data_points: number
}

// API レスポンスの型定義
interface HistoricalDataResult {
  timestamp: string
  symbol: string
  timeframes: Record<string, TimeframeData>
  api_info?: {
    source: string
    rate_limit: string
    note: string
  }
}

export default function FXAnalysisStrategy() {
  // ステート管理
  const [selectedSymbol, setSelectedSymbol] = useState('USDJPY=X')
  const [historicalData, setHistoricalData] = useState<HistoricalDataResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [autoUpdate, setAutoUpdate] = useState(false)
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>('5m')
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(50)
  const [viewMode, setViewMode] = useState<'chart' | 'table'>('chart')

  // 通貨ペアオプション
  const currencyPairs = [
    { symbol: 'USDJPY=X', name: 'USD/JPY', description: '米ドル/日本円' },
    { symbol: 'EURJPY=X', name: 'EUR/JPY', description: 'ユーロ/日本円' },
    { symbol: 'GBPJPY=X', name: 'GBP/JPY', description: '英ポンド/日本円' },
    { symbol: 'AUDJPY=X', name: 'AUD/JPY', description: '豪ドル/日本円' },
    { symbol: 'EURUSD=X', name: 'EUR/USD', description: 'ユーロ/米ドル' }
  ]

  // データ取得関数
  const fetchData = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch('http://localhost:8000/api/analysis/multi-timeframe/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symbol: selectedSymbol
        })
      })

      if (!response.ok) {
        throw new Error(`データ取得エラー: ${response.status}`)
      }

      const result = await response.json()

      if (result.error) {
        throw new Error(result.error)
      }

      setHistoricalData(result)

      // フロントエンドでキャッシュ（localStorageに保存）
      const cacheKey = `fx_data_${selectedSymbol}`
      localStorage.setItem(cacheKey, JSON.stringify({
        data: result,
        timestamp: new Date().toISOString()
      }))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'データ取得中にエラーが発生しました')
    } finally {
      setLoading(false)
    }
  }

  // キャッシュからデータを読み込む関数
  const loadFromCache = () => {
    const cacheKey = `fx_data_${selectedSymbol}`
    const cached = localStorage.getItem(cacheKey)

    if (cached) {
      try {
        const { data } = JSON.parse(cached)
        setHistoricalData(data)
      } catch (e) {
        console.error('キャッシュ読み込みエラー:', e)
      }
    }
  }

  // 自動更新機能
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null

    if (autoUpdate) {
      interval = setInterval(() => {
        fetchData()
      }, 60000) // 1分ごとに更新
    }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [autoUpdate, selectedSymbol])

  // 初回データ取得（キャッシュから読み込んでから最新データ取得）
  useEffect(() => {
    loadFromCache() // まずキャッシュから読み込み
    fetchData() // その後最新データを取得
  }, [selectedSymbol])

  return (
    <div className="space-y-6">
      {/* ヘッダー・コントロールエリア */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">📊 FX過去データ表示</h2>
            <p className="text-gray-600">マルチタイムフレームの過去価格データ</p>
          </div>

          <div className="flex flex-col sm:flex-row gap-3">
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            >
              {currencyPairs.map((pair) => (
                <option key={pair.symbol} value={pair.symbol}>
                  {pair.name} - {pair.description}
                </option>
              ))}
            </select>

            <button
              onClick={fetchData}
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              <span>{loading ? 'データ取得中...' : 'データ取得'}</span>
            </button>

            <button
              onClick={() => setAutoUpdate(!autoUpdate)}
              className={`px-4 py-2 rounded-lg flex items-center space-x-2 ${
                autoUpdate
                  ? 'bg-green-600 text-white hover:bg-green-700'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {autoUpdate ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              <span>自動更新</span>
            </button>
          </div>
        </div>
      </div>

      {/* エラー表示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <div className="flex items-center space-x-2 text-red-600">
            <AlertCircle className="h-5 w-5" />
            <span className="font-medium">エラー</span>
          </div>
          <p className="text-red-700 mt-1">{error}</p>
        </div>
      )}

      {/* ローディング表示 */}
      {loading && !historicalData && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
          <RefreshCw className="h-12 w-12 text-blue-500 mx-auto mb-4 animate-spin" />
          <p className="text-gray-600">データを取得しています...</p>
        </div>
      )}

      {/* API情報表示 */}
      {historicalData?.api_info && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <BarChart3 className="h-5 w-5 text-blue-600 mt-0.5" />
            <div className="flex-1">
              <h4 className="font-semibold text-blue-900 mb-1">データソース情報</h4>
              <div className="text-sm text-blue-700 space-y-1">
                <div>📊 {historicalData.api_info.source}</div>
                <div>⚡ {historicalData.api_info.rate_limit}</div>
                <div>💾 {historicalData.api_info.note}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 過去データ表示 */}
      {historicalData && historicalData.timeframes && (
        <>
          {/* マルチタイムフレーム過去データサマリー */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center space-x-2">
              <Clock className="h-6 w-6 text-blue-600" />
              <span>🕐 マルチタイムフレーム過去データ</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {Object.entries(historicalData.timeframes).map(([timeframe, data]) => {
                const latestCandle = data.data && data.data.length > 0 ? data.data[data.data.length - 1] : null

                return (
                  <div
                    key={timeframe}
                    className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
                      selectedTimeframe === timeframe
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-blue-300'
                    }`}
                    onClick={() => {
                      setSelectedTimeframe(timeframe)
                      setCurrentPage(1) // ページをリセット
                    }}
                  >
                    <div className="text-center mb-3">
                      <h4 className="font-bold text-gray-800">{data.description}</h4>
                      <p className="text-sm text-gray-600">{timeframe}</p>
                    </div>

                    {latestCandle ? (
                      <div className="space-y-2">
                        <div className="text-center px-3 py-2 rounded-lg bg-gray-100">
                          <div className="font-bold text-lg">{latestCandle.close.toFixed(3)}</div>
                          <div className="text-xs text-gray-600">最新終値</div>
                        </div>

                        <div className="text-xs text-gray-600 space-y-1">
                          <div>始値: {latestCandle.open.toFixed(3)}</div>
                          <div>高値: {latestCandle.high.toFixed(3)}</div>
                          <div>安値: {latestCandle.low.toFixed(3)}</div>
                          <div>データポイント: {data.data_points}</div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center text-sm text-red-600">
                        データなし
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* 詳細データ表示（チャート/テーブル） */}
          {selectedTimeframe && historicalData.timeframes[selectedTimeframe] && (() => {
            const timeframeData = historicalData.timeframes[selectedTimeframe]
            const reversedData = [...timeframeData.data].reverse()
            const totalItems = reversedData.length
            const totalPages = Math.ceil(totalItems / itemsPerPage)
            const startIndex = (currentPage - 1) * itemsPerPage
            const endIndex = startIndex + itemsPerPage
            const currentData = reversedData.slice(startIndex, endIndex)

            // チャート用データ（最新200件）
            const chartData = reversedData.slice(0, 200).reverse().map(candle => ({
              time: new Date(candle.timestamp).toLocaleString('ja-JP', {
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
              }),
              open: candle.open,
              high: candle.high,
              low: candle.low,
              close: candle.close,
              timestamp: candle.timestamp
            }))

            return (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold text-gray-800 flex items-center space-x-2">
                    {viewMode === 'chart' ? (
                      <LineChart className="h-6 w-6 text-green-600" />
                    ) : (
                      <Table className="h-6 w-6 text-green-600" />
                    )}
                    <span>📋 {timeframeData.description} - 詳細データ</span>
                  </h3>

                  <div className="flex items-center gap-3">
                    {/* 表示モード切り替え */}
                    <div className="flex bg-gray-100 rounded-lg p-1">
                      <button
                        onClick={() => setViewMode('chart')}
                        className={`px-4 py-1 rounded-md text-sm font-medium transition-all ${
                          viewMode === 'chart'
                            ? 'bg-white text-blue-600 shadow-sm'
                            : 'text-gray-600 hover:text-gray-900'
                        }`}
                      >
                        <LineChart className="h-4 w-4 inline mr-1" />
                        チャート
                      </button>
                      <button
                        onClick={() => setViewMode('table')}
                        className={`px-4 py-1 rounded-md text-sm font-medium transition-all ${
                          viewMode === 'table'
                            ? 'bg-white text-blue-600 shadow-sm'
                            : 'text-gray-600 hover:text-gray-900'
                        }`}
                      >
                        <Table className="h-4 w-4 inline mr-1" />
                        テーブル
                      </button>
                    </div>

                    {viewMode === 'table' && (
                      <select
                        value={itemsPerPage}
                        onChange={(e) => {
                          setItemsPerPage(Number(e.target.value))
                          setCurrentPage(1)
                        }}
                        className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value={25}>25件/ページ</option>
                        <option value={50}>50件/ページ</option>
                        <option value={100}>100件/ページ</option>
                        <option value={200}>200件/ページ</option>
                      </select>
                    )}
                  </div>
                </div>

                {/* チャート表示 */}
                {viewMode === 'chart' && (
                  <div className="w-full" style={{ height: '500px' }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis
                          dataKey="time"
                          tick={{ fontSize: 12 }}
                          interval={Math.floor(chartData.length / 10)}
                        />
                        <YAxis
                          domain={['dataMin - 0.5', 'dataMax + 0.5']}
                          tick={{ fontSize: 12 }}
                        />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: 'white',
                            border: '1px solid #e5e7eb',
                            borderRadius: '8px',
                            padding: '12px'
                          }}
                          formatter={(value: any) => value.toFixed(3)}
                        />
                        <Legend />
                        <Line
                          type="monotone"
                          dataKey="close"
                          stroke="#2563eb"
                          strokeWidth={2}
                          dot={false}
                          name="終値"
                        />
                        <Line
                          type="monotone"
                          dataKey="high"
                          stroke="#10b981"
                          strokeWidth={1}
                          dot={false}
                          name="高値"
                          strokeDasharray="5 5"
                        />
                        <Line
                          type="monotone"
                          dataKey="low"
                          stroke="#ef4444"
                          strokeWidth={1}
                          dot={false}
                          name="安値"
                          strokeDasharray="5 5"
                        />
                      </ComposedChart>
                    </ResponsiveContainer>
                    <p className="text-sm text-gray-500 mt-4">
                      ※ 最新200件を表示しています（全{totalItems}件）
                    </p>
                  </div>
                )}

                {/* テーブル表示 */}
                {viewMode === 'table' && (
                  <>
                    <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          時刻
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          始値
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          高値
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          安値
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          終値
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          変動
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {currentData.map((candle, index) => {
                        const change = candle.close - candle.open
                        const changePercent = (change / candle.open) * 100
                        const isPositive = change >= 0

                        return (
                          <tr key={index} className="hover:bg-gray-50">
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                              {new Date(candle.timestamp).toLocaleString('ja-JP', {
                                month: '2-digit',
                                day: '2-digit',
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-900">
                              {candle.open.toFixed(3)}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-900">
                              {candle.high.toFixed(3)}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-900">
                              {candle.low.toFixed(3)}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-right font-medium text-gray-900">
                              {candle.close.toFixed(3)}
                            </td>
                            <td className={`px-4 py-3 whitespace-nowrap text-sm text-right font-medium ${
                              isPositive ? 'text-green-600' : 'text-red-600'
                            }`}>
                              {isPositive ? '+' : ''}{change.toFixed(3)} ({changePercent.toFixed(2)}%)
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>

                {/* ページネーションコントロール */}
                <div className="mt-6 flex items-center justify-between border-t border-gray-200 pt-4">
                  <div className="text-sm text-gray-600">
                    {startIndex + 1} - {Math.min(endIndex, totalItems)} / 全{totalItems}件
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setCurrentPage(1)}
                      disabled={currentPage === 1}
                      className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      title="最初のページ"
                    >
                      <ChevronsLeft className="h-4 w-4" />
                    </button>

                    <button
                      onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                      disabled={currentPage === 1}
                      className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      title="前のページ"
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </button>

                    <div className="flex items-center gap-1">
                      {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                        let pageNum
                        if (totalPages <= 5) {
                          pageNum = i + 1
                        } else if (currentPage <= 3) {
                          pageNum = i + 1
                        } else if (currentPage >= totalPages - 2) {
                          pageNum = totalPages - 4 + i
                        } else {
                          pageNum = currentPage - 2 + i
                        }

                        return (
                          <button
                            key={i}
                            onClick={() => setCurrentPage(pageNum)}
                            className={`px-3 py-1 rounded-lg ${
                              currentPage === pageNum
                                ? 'bg-blue-600 text-white'
                                : 'border border-gray-300 hover:bg-gray-50'
                            }`}
                          >
                            {pageNum}
                          </button>
                        )
                      })}
                    </div>

                    <button
                      onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                      disabled={currentPage === totalPages}
                      className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      title="次のページ"
                    >
                      <ChevronRight className="h-4 w-4" />
                    </button>

                    <button
                      onClick={() => setCurrentPage(totalPages)}
                      disabled={currentPage === totalPages}
                      className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      title="最後のページ"
                    >
                      <ChevronsRight className="h-4 w-4" />
                    </button>
                  </div>
                </div>
                  </>
                )}
              </div>
            )
          })()}
        </>
      )}
    </div>
  )
}
