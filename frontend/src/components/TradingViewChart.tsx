'use client'

import { useState, useEffect, useRef } from 'react'

interface TradingViewChartProps {
  symbol: string
  marketData: any[]
}

export default function TradingViewChart({ symbol, marketData }: TradingViewChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!containerRef.current) return

    // TradingViewウィジェットを埋め込み
    const script = document.createElement('script')
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js'
    script.type = 'text/javascript'
    script.async = true
    script.innerHTML = JSON.stringify({
      "autosize": true,
      "symbol": symbol.replace('_', ''),
      "interval": "5",
      "timezone": "Asia/Tokyo",
      "theme": "light",
      "style": "1",
      "locale": "ja",
      "toolbar_bg": "#f1f3f6",
      "enable_publishing": false,
      "allow_symbol_change": true,
      "container_id": "tradingview_chart",
      "hide_side_toolbar": false,
      "studies": [
        "Volume@tv-basicstudies"
      ]
    })

    // 既存のスクリプトをクリア
    containerRef.current.innerHTML = ''
    containerRef.current.appendChild(script)

    return () => {
      if (containerRef.current) {
        containerRef.current.innerHTML = ''
      }
    }
  }, [symbol])

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
          <div className="text-sm">
            <span className="text-gray-500">現在価格: </span>
            <span className="font-bold text-blue-600 font-mono">
              {marketData.find(m => m.currency_symbol === symbol)?.mid_price || '---'}
            </span>
          </div>
        </div>
        
        <div className="flex space-x-2">
          <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded">
            📈 プロチャート
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
          <span>📊 TradingView チャート</span>
          <span>🌐 リアルタイムデータ</span>
          <span>📅 5分足表示</span>
        </div>
        <div>
          <span>Powered by TradingView</span>
        </div>
      </div>
    </div>
  )
}