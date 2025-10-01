'use client'

import { useEffect, useState } from 'react'
import { TrendingUp, TrendingDown, Clock, AlertCircle, Target } from 'lucide-react'

interface TFQESignal {
  signal: string
  reason: string
  strategy?: string
  confidence?: number
  entry?: number
  stop_loss?: number
  take_profit_1?: number
  take_profit_2?: number
  risk_pips?: number
  reward_pips?: number
  h1_trend?: string
  h1_adx?: number
  m15_price?: number
  m15_ema20?: number
  m15_atr?: number
  distance?: string
  timestamp: string
}

export default function TFQESignalWidget() {
  const [signal, setSignal] = useState<TFQESignal | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  const fetchSignal = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:8000/api/analysis/tfqe-signal/')

      if (!response.ok) {
        throw new Error('API呼び出し失敗')
      }

      const data = await response.json()
      setSignal(data)
      setLastUpdate(new Date())
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : '不明なエラー')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // 初回読み込み
    fetchSignal()

    // 15分ごとに更新
    const interval = setInterval(() => {
      fetchSignal()
    }, 15 * 60 * 1000) // 15分 = 900,000ミリ秒

    return () => clearInterval(interval)
  }, [])

  if (loading && !signal) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="text-center text-gray-500">
          <div className="mb-2">TFQE戦略シグナル</div>
          <div className="text-sm">読み込み中...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-700 rounded-lg p-6">
        <div className="flex items-center gap-2 text-red-400">
          <AlertCircle className="w-5 h-5" />
          <span>エラー: {error}</span>
        </div>
      </div>
    )
  }

  if (!signal) return null

  const getSignalColor = () => {
    return 'bg-white border-gray-200'
  }

  const getSignalIcon = () => {
    switch (signal.signal) {
      case 'BUY':
        return <TrendingUp className="w-6 h-6 text-green-400" />
      case 'SELL':
        return <TrendingDown className="w-6 h-6 text-red-400" />
      case 'WAITING_PULLBACK':
      case 'WAITING_RALLY':
        return <Clock className="w-6 h-6 text-yellow-400" />
      default:
        return <AlertCircle className="w-6 h-6 text-gray-400" />
    }
  }

  const getSignalText = () => {
    switch (signal.signal) {
      case 'BUY':
        return '買いシグナル'
      case 'SELL':
        return '売りシグナル'
      case 'WAITING_PULLBACK':
        return '押し目待ち'
      case 'WAITING_RALLY':
        return '戻り待ち'
      case 'NO_TREND':
        return 'トレンドなし'
      case 'OUT_OF_SESSION':
        return '取引時間外'
      default:
        return '待機中'
    }
  }

  return (
    <div className={`border rounded-lg p-6 ${getSignalColor()}`}>
      {/* ヘッダー */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          {getSignalIcon()}
          <div>
            <h3 className="text-lg font-semibold text-gray-800">
              TFQE戦略シグナル
            </h3>
            <p className="text-sm text-gray-500">
              最終更新: {lastUpdate.toLocaleTimeString('ja-JP')}
            </p>
          </div>
        </div>
        <button
          onClick={fetchSignal}
          disabled={loading}
          className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm text-white disabled:opacity-50"
        >
          {loading ? '更新中...' : '手動更新'}
        </button>
      </div>

      {/* シグナル表示 */}
      <div className="space-y-4">
        <div>
          <div className="text-2xl font-bold text-gray-900 mb-1">
            {getSignalText()}
          </div>
          <div className="text-gray-600">
            {signal.reason}
          </div>
        </div>

        {/* エントリー情報（BUY/SELLの場合のみ） */}
        {(signal.signal === 'BUY' || signal.signal === 'SELL') && (
          <div className="grid grid-cols-2 gap-4 mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <div>
              <div className="text-sm text-gray-500 mb-1">エントリー価格</div>
              <div className="text-xl font-bold text-gray-900">
                {signal.entry?.toFixed(3)} 円
              </div>
            </div>

            <div>
              <div className="text-sm text-gray-500 mb-1">信頼度</div>
              <div className="text-xl font-bold text-gray-900">
                {signal.confidence}%
              </div>
            </div>

            <div>
              <div className="text-sm text-gray-500 mb-1">損切り（SL）</div>
              <div className="text-lg font-semibold text-red-600">
                {signal.stop_loss?.toFixed(3)} 円
              </div>
              <div className="text-xs text-gray-500">
                リスク: {signal.risk_pips?.toFixed(1)} pips
              </div>
            </div>

            <div>
              <div className="text-sm text-gray-500 mb-1">利確1（TP1）</div>
              <div className="text-lg font-semibold text-green-600">
                {signal.take_profit_1?.toFixed(3)} 円
              </div>
              <div className="text-xs text-gray-500">
                リワード: {signal.reward_pips?.toFixed(1)} pips
              </div>
            </div>

            <div className="col-span-2">
              <div className="text-sm text-gray-500 mb-1">利確2（TP2）</div>
              <div className="text-lg font-semibold text-blue-600">
                {signal.take_profit_2?.toFixed(3)} 円
              </div>
              <div className="text-xs text-gray-500 mt-1">
                ※ TP1で半分利確 & 建値移動、残りはEMA20終値割れまで保持
              </div>
            </div>
          </div>
        )}

        {/* 待機中の情報 */}
        {(signal.signal === 'WAITING_PULLBACK' || signal.signal === 'WAITING_RALLY') && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">H1トレンド:</span>
              <span className="text-gray-900 font-semibold">{signal.h1_trend}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">現在価格:</span>
              <span className="text-gray-900">{signal.m15_price?.toFixed(3)} 円</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">EMA20:</span>
              <span className="text-gray-900">{signal.m15_ema20?.toFixed(3)} 円</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">EMA20からの乖離:</span>
              <span className={`font-semibold ${
                signal.distance?.startsWith('-') ? 'text-red-600' : 'text-green-600'
              }`}>
                {signal.distance}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* フッター */}
      <div className="mt-4 pt-4 border-t border-gray-200 text-xs text-gray-500">
        <div className="flex items-center gap-2">
          <Target className="w-4 h-4" />
          <span>取引時間: 16:00-24:00 JST</span>
          <span className="mx-2">|</span>
          <span>自動更新: 15分ごと</span>
        </div>
      </div>
    </div>
  )
}
