// FX分析・戦略システムコンポーネント
'use client'

import { useState, useEffect } from 'react'
import {
  TrendingUp,
  TrendingDown,
  Clock,
  Target,
  BarChart3,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Play,
  Pause
} from 'lucide-react'

// 分析結果の型定義
interface TimeframeAnalysis {
  timeframe: string
  trading_style: string
  description: string
  analysis: {
    current_price: number
    trend: string
    signal: string
    confidence: number
    strength: string
    rsi: number
    momentum: string
    volatility: number
    key_levels: {
      resistance: number
      support: number
      pivot: number
    }
  }
  entry_points: Array<{
    type: string
    price: number
    stop_loss: number
    take_profit: number
    timeframe: string
    reason: string
  }>
  strategy: {
    style: string
    holding_period: string
    profit_target: string
    stop_loss: string
    frequency: string
    best_sessions: string[]
    avoid_times: string[]
  }
  data_points: number
}

interface IntegratedStrategy {
  integrated_signal: string
  confidence: number
  signal_alignment: string
  recommended_strategies: Array<{
    timeframe: string
    style: string
    confidence: number
    entry_points: Array<{
      type: string
      price: number
      stop_loss: number
      take_profit: number
      timeframe: string
      reason: string
    }>
    priority: string
  }>
  risk_level: string
  market_timing: {
    current_session: string
    activity_level: string
    week_timing: string
    recommendation: string
  }
}

interface AnalysisResult {
  timestamp: string
  symbol: string
  timeframe_analyses: Record<string, TimeframeAnalysis>
  integrated_strategy: IntegratedStrategy
  market_session: {
    active_sessions: string[]
    optimal_for: string
  }
}

export default function FXAnalysisStrategy() {
  // ステート管理
  const [selectedSymbol, setSelectedSymbol] = useState('USDJPY=X')
  const [analysisData, setAnalysisData] = useState<AnalysisResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [autoUpdate, setAutoUpdate] = useState(false)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  // 通貨ペアオプション
  const currencyPairs = [
    { symbol: 'USDJPY=X', name: 'USD/JPY', description: '米ドル/日本円' },
    { symbol: 'EURJPY=X', name: 'EUR/JPY', description: 'ユーロ/日本円' },
    { symbol: 'GBPJPY=X', name: 'GBP/JPY', description: '英ポンド/日本円' },
    { symbol: 'AUDJPY=X', name: 'AUD/JPY', description: '豪ドル/日本円' },
    { symbol: 'EURUSD=X', name: 'EUR/USD', description: 'ユーロ/米ドル' }
  ]

  // 分析実行関数
  const runAnalysis = async () => {
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
        throw new Error(`分析エラー: ${response.status}`)
      }

      const result = await response.json()

      if (result.error) {
        throw new Error(result.error)
      }

      setAnalysisData(result)
      setLastUpdate(new Date())
    } catch (err) {
      setError(err instanceof Error ? err.message : '分析中にエラーが発生しました')
    } finally {
      setLoading(false)
    }
  }

  // 自動更新機能
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null

    if (autoUpdate) {
      interval = setInterval(() => {
        runAnalysis()
      }, 60000) // 1分ごとに更新
    }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [autoUpdate, selectedSymbol])

  // 初回データ取得
  useEffect(() => {
    runAnalysis()
  }, [selectedSymbol])

  // シグナルの色を取得
  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'BUY': return 'text-green-600 bg-green-50'
      case 'SELL': return 'text-red-600 bg-red-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  // 信頼度に基づく色を取得
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'text-green-600'
    if (confidence >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  // リスクレベルの色を取得
  const getRiskColor = (risk: string) => {
    switch (risk) {
      case '低': return 'text-green-600 bg-green-50'
      case '中': return 'text-yellow-600 bg-yellow-50'
      case '高': return 'text-red-600 bg-red-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  return (
    <div className="space-y-6">
      {/* ヘッダー・コントロールエリア */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">🎯 FX分析・戦略システム</h2>
            <p className="text-gray-600">マルチタイムフレーム分析による総合的な取引戦略</p>
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
              onClick={runAnalysis}
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              <span>{loading ? '分析中...' : '分析実行'}</span>
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

        {lastUpdate && (
          <div className="mt-4 text-sm text-gray-500">
            最終更新: {lastUpdate.toLocaleString('ja-JP')}
          </div>
        )}
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
      {loading && !analysisData && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
          <RefreshCw className="h-12 w-12 text-blue-500 mx-auto mb-4 animate-spin" />
          <p className="text-gray-600">分析を実行しています...</p>
        </div>
      )}

      {/* 分析結果表示 */}
      {analysisData && (
        <>
          {/* 統合判断カード */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center space-x-2">
              <CheckCircle className="h-6 w-6 text-green-600" />
              <span>📊 統合判断</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className={`text-2xl font-bold px-4 py-2 rounded-lg ${getSignalColor(analysisData.integrated_strategy.integrated_signal)}`}>
                  {analysisData.integrated_strategy.integrated_signal}
                </div>
                <p className="text-sm text-gray-600 mt-1">統合シグナル</p>
              </div>

              <div className="text-center">
                <div className={`text-2xl font-bold ${getConfidenceColor(analysisData.integrated_strategy.confidence)}`}>
                  {analysisData.integrated_strategy.confidence.toFixed(1)}%
                </div>
                <p className="text-sm text-gray-600 mt-1">信頼度</p>
              </div>

              <div className="text-center">
                <div className={`text-lg font-bold px-3 py-2 rounded-lg ${getRiskColor(analysisData.integrated_strategy.risk_level)}`}>
                  {analysisData.integrated_strategy.risk_level}
                </div>
                <p className="text-sm text-gray-600 mt-1">リスクレベル</p>
              </div>

              <div className="text-center">
                <div className="text-lg font-bold text-blue-600">
                  {analysisData.integrated_strategy.signal_alignment}
                </div>
                <p className="text-sm text-gray-600 mt-1">シグナル一致度</p>
              </div>
            </div>
          </div>

          {/* マルチタイムフレーム分析 */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center space-x-2">
              <Clock className="h-6 w-6 text-blue-600" />
              <span>🕐 マルチタイムフレーム分析</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {Object.entries(analysisData.timeframe_analyses).map(([timeframe, analysis]) => (
                <div key={timeframe} className="border border-gray-200 rounded-lg p-4">
                  <div className="text-center mb-3">
                    <h4 className="font-bold text-gray-800">{analysis.description}</h4>
                    <p className="text-sm text-gray-600">{timeframe}</p>
                  </div>

                  <div className="space-y-2">
                    <div className={`text-center px-3 py-2 rounded-lg ${getSignalColor(analysis.analysis.signal)}`}>
                      <div className="font-bold">{analysis.analysis.signal}</div>
                      <div className="text-sm">{analysis.analysis.confidence.toFixed(0)}%</div>
                    </div>

                    <div className="text-xs text-gray-600 space-y-1">
                      <div>保有期間: {analysis.strategy.holding_period}</div>
                      <div>利益目標: {analysis.strategy.profit_target}</div>
                      <div>RSI: {analysis.analysis.rsi.toFixed(1)}</div>
                      <div>トレンド: {analysis.analysis.trend}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 推奨エントリーポイント */}
          {analysisData.integrated_strategy.recommended_strategies.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center space-x-2">
                <Target className="h-6 w-6 text-purple-600" />
                <span>📍 推奨エントリーポイント</span>
              </h3>

              <div className="space-y-4">
                {analysisData.integrated_strategy.recommended_strategies.map((strategy, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h4 className="font-bold text-gray-800">{strategy.style}</h4>
                        <p className="text-sm text-gray-600">
                          時間軸: {strategy.timeframe} | 優先度: {strategy.priority} | 信頼度: {strategy.confidence}%
                        </p>
                      </div>
                      <div className={`px-3 py-1 rounded-lg text-sm font-medium ${
                        strategy.priority === '高' ? 'bg-red-100 text-red-800' :
                        strategy.priority === '中' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {strategy.priority}
                      </div>
                    </div>

                    {strategy.entry_points.map((entry, entryIndex) => (
                      <div key={entryIndex} className="bg-gray-50 rounded-lg p-3">
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-sm">
                          <div>
                            <span className="font-medium text-gray-700">エントリー:</span>
                            <div className="font-bold text-blue-600">{entry.price.toFixed(3)}円</div>
                          </div>
                          <div>
                            <span className="font-medium text-gray-700">利確:</span>
                            <div className="font-bold text-green-600">{entry.take_profit.toFixed(3)}円</div>
                          </div>
                          <div>
                            <span className="font-medium text-gray-700">損切:</span>
                            <div className="font-bold text-red-600">{entry.stop_loss.toFixed(3)}円</div>
                          </div>
                          <div>
                            <span className="font-medium text-gray-700">期間:</span>
                            <div className="text-gray-800">{entry.timeframe}</div>
                          </div>
                        </div>
                        <div className="mt-2 text-sm text-gray-600">
                          <strong>理由:</strong> {entry.reason}
                        </div>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 市場タイミング情報 */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center space-x-2">
              <BarChart3 className="h-6 w-6 text-green-600" />
              <span>⏰ 市場タイミング</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="font-bold text-lg text-blue-600">
                  {analysisData.integrated_strategy.market_timing.current_session}
                </div>
                <p className="text-sm text-gray-600">現在セッション</p>
              </div>

              <div className="text-center">
                <div className="font-bold text-lg text-purple-600">
                  {analysisData.integrated_strategy.market_timing.activity_level}
                </div>
                <p className="text-sm text-gray-600">活動レベル</p>
              </div>

              <div className="text-center">
                <div className="font-bold text-lg text-orange-600">
                  {analysisData.market_session.optimal_for}
                </div>
                <p className="text-sm text-gray-600">最適スタイル</p>
              </div>

              <div className="text-center">
                <div className="font-bold text-lg text-gray-800">
                  {analysisData.integrated_strategy.market_timing.recommendation}
                </div>
                <p className="text-sm text-gray-600">推奨</p>
              </div>
            </div>

            {analysisData.market_session.active_sessions.length > 0 && (
              <div className="mt-4 text-center">
                <p className="text-sm text-gray-600">
                  活動中市場: {analysisData.market_session.active_sessions.join(', ')}
                </p>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}