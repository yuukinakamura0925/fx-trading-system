'use client'

import { useState, useEffect, useRef } from 'react'

interface TradingViewChartProps {
  symbol: string
}

// 時間足の選択肢
const TIME_INTERVALS = [
  { value: '1', label: '1分', description: '超短期' },
  { value: '5', label: '5分', description: '短期' },
  { value: '15', label: '15分', description: '中期' },
  { value: '60', label: '1時間', description: '長期' },
  { value: '240', label: '4時間', description: '超長期' },
  { value: 'D', label: '日足', description: 'デイリー' },
];

export default function TradingViewChart({ symbol }: TradingViewChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [selectedInterval, setSelectedInterval] = useState('1') // デフォルト1分
  const [isProChart, setIsProChart] = useState(false) // デフォルト軽量版

  useEffect(() => {
    // DOMが完全にマウントされるまで待機
    const timer = setTimeout(() => {
      if (!containerRef.current) return

      // 既存のスクリプトとウィジェットをクリア
      containerRef.current.innerHTML = ''

      // TradingViewウィジェットのコンテナを作成
      const widgetContainer = document.createElement('div')
      widgetContainer.className = 'tradingview-widget-container'
      widgetContainer.style.height = '100%'
      widgetContainer.style.width = '100%'

      const widgetInner = document.createElement('div')
      if (isProChart) {
        widgetInner.className = 'tradingview-widget-container__widget'
        widgetInner.id = 'tradingview_chart'
      } else {
        widgetInner.className = 'tradingview-widget-container__widget'
      }
      widgetInner.style.height = 'calc(100% - 32px)'
      widgetInner.style.width = '100%'

      widgetContainer.appendChild(widgetInner)

      const script = document.createElement('script')
      script.type = 'text/javascript'
      script.async = true

      if (isProChart) {
        // プロチャート（高機能版）
        script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js'
        script.innerHTML = JSON.stringify({
          "autosize": true,
          "symbol": `FX:${symbol.replace('_', '')}`,
          "interval": selectedInterval,
          "timezone": "Asia/Tokyo",
          "theme": "light",
          "style": "1",
          "locale": "ja",
          "toolbar_bg": "#f1f3f6",
          "enable_publishing": false,
          "allow_symbol_change": false,
          "hide_side_toolbar": false,
          "details": true,
          "hotlist": true,
          "calendar": true,
          "studies": ["Volume@tv-basicstudies"],
          "container_id": "tradingview_chart"
        })
      } else {
        // 軽量チャート（シンプル版）
        script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js'
        script.innerHTML = JSON.stringify({
          "symbol": `FX:${symbol.replace('_', '')}`,
          "width": "100%",
          "height": "100%",
          "locale": "ja",
          "dateRange": "12M",
          "colorTheme": "light",
          "trendLineColor": "rgba(41, 98, 255, 1)",
          "underLineColor": "rgba(41, 98, 255, 0.3)",
          "underLineBottomColor": "rgba(41, 98, 255, 0)",
          "isTransparent": false,
          "autosize": true,
          "largeChartUrl": ""
        })
      }

      widgetContainer.appendChild(script)
      containerRef.current.appendChild(widgetContainer)
    }, 100)

    return () => {
      clearTimeout(timer)
      if (containerRef.current) {
        containerRef.current.innerHTML = ''
      }
    }
  }, [symbol, selectedInterval, isProChart])

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      {/* ヘッダー */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <h3 className="text-xl font-bold text-gray-800">{symbol} チャート</h3>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm text-gray-500">TradingView</span>
          </div>
          {isProChart && (
            <div className="text-sm text-gray-600">
              {TIME_INTERVALS.find(t => t.value === selectedInterval)?.label}足
            </div>
          )}
        </div>

        <div className="flex items-center space-x-3">
          {/* プロ版時の時間足選択 */}
          {isProChart && (
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">時間足:</span>
              <select
                value={selectedInterval}
                onChange={(e) => setSelectedInterval(e.target.value)}
                className="px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {TIME_INTERVALS.map(interval => (
                  <option key={interval.value} value={interval.value}>
                    {interval.label}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* チャート切り替えボタン */}
          <button
            onClick={() => setIsProChart(!isProChart)}
            className={`px-3 py-1 text-sm font-medium rounded transition-colors ${
              isProChart
                ? 'bg-purple-100 text-purple-700 hover:bg-purple-200'
                : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
            }`}
          >
            {isProChart ? '📊 プロチャート' : '📈 軽量チャート'}
          </button>

          {/* 切り替えヒント */}
          <span className="text-xs text-gray-500">
            クリックで切り替え
          </span>
        </div>
      </div>

      {/* TradingViewチャート */}
      <div className="h-96 w-full border border-gray-200 rounded-lg overflow-hidden">
        <div 
          ref={containerRef}
          id="tradingview_chart"
          className="w-full h-full"
        />
      </div>

      {/* フッター */}
      <div className="mt-4 flex justify-between items-center text-xs text-gray-500">
        <div className="flex items-center space-x-4">
          <span>📊 TradingView {isProChart ? 'プロ' : '軽量'}チャート</span>
          <span>🌐 リアルタイムデータ</span>
          {isProChart ? (
            <span>📅 {TIME_INTERVALS.find(t => t.value === selectedInterval)?.label}足表示</span>
          ) : (
            <span>📈 シンプル表示</span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <span>Powered by TradingView</span>
          {isProChart && (
            <span className="px-2 py-1 bg-purple-50 text-purple-600 rounded">
              高機能版
            </span>
          )}
        </div>
      </div>
    </div>
  )
}