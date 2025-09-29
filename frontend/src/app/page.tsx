// FX取引システム メインダッシュボード
'use client'

import { useState, useEffect } from 'react'
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  BarChart3, 
  Activity, 
  Settings,
  Home,
  Target,
  PieChart,
  FileText,
  Bell,
  User,
  LogOut,
  Menu,
  X
} from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import dynamic from 'next/dynamic'

// TradingViewチャートを動的インポート（SSR無効化）
const TradingViewChart = dynamic(
  () => import('../components/TradingViewChart'),
  { 
    ssr: false,
    loading: () => (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
            <p className="text-gray-500">チャートを読み込み中...</p>
          </div>
        </div>
      </div>
    )
  }
)

// APIからの市場データ型定義
interface MarketData {
  id: number
  currency_symbol: string
  bid: string
  ask: string
  mid_price: string
  spread: string
  timestamp: string
}

// ポジション情報型定義
interface Position {
  id: number
  currency_symbol: string
  side: 'BUY' | 'SELL'
  size: number
  entry_price: string
  current_price: string
  current_pnl: number
  status: string
}

// ポジションサマリー型定義
interface PositionSummary {
  total_positions: number
  total_unrealized_pnl: number
  long_positions: number
  short_positions: number
}

export default function TradingDashboard() {
  // ステート管理
  const [marketData, setMarketData] = useState<MarketData[]>([])
  const [positions, setPositions] = useState<Position[]>([])
  const [summary, setSummary] = useState<PositionSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [activeMenu, setActiveMenu] = useState('dashboard')
  const [selectedSymbol, setSelectedSymbol] = useState('USD_JPY')

  // APIからデータを取得する関数
  const fetchData = async () => {
    try {
      // 最新市場データ取得
      const marketResponse = await fetch('http://localhost:8000/api/market-data/latest/')
      const marketData = await marketResponse.json()
      setMarketData(marketData)

      // オープンポジション取得
      const positionsResponse = await fetch('http://localhost:8000/api/positions/open/')
      const positionsData = await positionsResponse.json()
      setPositions(positionsData)

      // ポジションサマリー取得
      const summaryResponse = await fetch('http://localhost:8000/api/positions/summary/')
      const summaryData = await summaryResponse.json()
      setSummary(summaryData)

      setLoading(false)
    } catch (error) {
      console.error('データ取得エラー:', error)
      setLoading(false)
    }
  }

  // コンポーネント初期化時とリアルタイム更新
  useEffect(() => {
    fetchData()
    // 30秒ごとにデータ更新
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  // ローディング画面
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">🔄 データ読み込み中...</div>
      </div>
    )
  }

  // サイドメニューの項目
  const menuItems = [
    { id: 'dashboard', label: 'ダッシュボード', icon: Home },
    { id: 'positions', label: 'ポジション', icon: Target },
    { id: 'strategies', label: '戦略', icon: PieChart },
    { id: 'reports', label: 'レポート', icon: FileText },
    { id: 'settings', label: '設定', icon: Settings },
  ]

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* サイドバー */}
      <div className={`${sidebarOpen ? 'w-64' : 'w-20'} bg-white border-r border-gray-200 transition-all duration-300 ease-in-out shadow-lg fixed left-0 top-0 h-full z-30`}>
        {/* ロゴエリア */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-gray-200">
          {sidebarOpen && (
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <TrendingUp className="h-5 w-5 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-800">FX Trading</span>
            </div>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 rounded-lg hover:bg-gray-100 text-gray-600 hover:text-gray-800"
          >
            {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>

        {/* メニュー項目 */}
        <nav className="mt-6 px-3">
          {menuItems.map((item) => {
            const Icon = item.icon
            return (
              <button
                key={item.id}
                onClick={() => setActiveMenu(item.id)}
                className={`w-full flex items-center px-3 py-3 mb-2 rounded-lg text-left transition-colors ${
                  activeMenu === item.id
                    ? 'bg-blue-50 text-blue-600 border-r-2 border-blue-600'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-800'
                }`}
              >
                <Icon className={`h-5 w-5 ${sidebarOpen ? 'mr-3' : 'mx-auto'}`} />
                {sidebarOpen && <span className="font-medium">{item.label}</span>}
              </button>
            )
          })}
        </nav>

        {/* ユーザーエリア */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 bg-white">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
              <User className="h-4 w-4 text-gray-600" />
            </div>
            {sidebarOpen && (
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-800">トレーダー</p>
                <p className="text-xs text-gray-500">trader@example.com</p>
              </div>
            )}
            <button className="p-1 text-gray-400 hover:text-gray-600">
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* メインコンテンツエリア */}
      <div className={`flex-1 flex flex-col transition-all duration-300 ease-in-out ${sidebarOpen ? 'ml-64' : 'ml-20'}`}>
        {/* トップヘッダー */}
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shadow-sm">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">
              {menuItems.find(item => item.id === activeMenu)?.label || 'ダッシュボード'}
            </h1>
            <p className="text-sm text-gray-500">
              最終更新: {new Date().toLocaleTimeString('ja-JP')}
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <button className="p-2 text-gray-400 hover:text-gray-600 relative">
              <Bell className="h-5 w-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            </button>
            <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
              <User className="h-4 w-4 text-gray-600" />
            </div>
          </div>
        </header>

        {/* メインコンテンツ */}
        <main className="flex-1 p-6 bg-gray-50">
          {activeMenu === 'dashboard' && (
            <div className="space-y-6">
              {/* サマリーカード */}
              {summary && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-500 font-medium">総ポジション数</p>
                        <p className="text-2xl font-bold text-gray-900 mt-1">{summary.total_positions}</p>
                      </div>
                      <div className="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center">
                        <BarChart3 className="h-6 w-6 text-blue-600" />
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-500 font-medium">含み損益</p>
                        <p className={`text-2xl font-bold mt-1 ${summary.total_unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          ¥{summary.total_unrealized_pnl.toLocaleString()}
                        </p>
                      </div>
                      <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${summary.total_unrealized_pnl >= 0 ? 'bg-green-50' : 'bg-red-50'}`}>
                        <DollarSign className={`h-6 w-6 ${summary.total_unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`} />
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-500 font-medium">買いポジション</p>
                        <p className="text-2xl font-bold text-green-600 mt-1">{summary.long_positions}</p>
                      </div>
                      <div className="w-12 h-12 bg-green-50 rounded-lg flex items-center justify-center">
                        <TrendingUp className="h-6 w-6 text-green-600" />
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-500 font-medium">売りポジション</p>
                        <p className="text-2xl font-bold text-red-600 mt-1">{summary.short_positions}</p>
                      </div>
                      <div className="w-12 h-12 bg-red-50 rounded-lg flex items-center justify-center">
                        <TrendingDown className="h-6 w-6 text-red-600" />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* 市場データ表示 */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold text-gray-800">リアルタイム価格</h2>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                      <Activity className="h-5 w-5 text-green-500" />
                    </div>
                  </div>
                  <div className="space-y-3">
                    {marketData.map((market) => (
                      <div key={market.id} className="flex justify-between items-center p-4 bg-gray-50 rounded-lg border border-gray-100 hover:border-gray-200 transition-colors">
                        <div>
                          <div className="font-bold text-lg text-gray-800">{market.currency_symbol}</div>
                          <div className="text-sm text-gray-500">
                            スプレッド: {parseFloat(market.spread).toFixed(market.currency_symbol.includes('JPY') ? 3 : 5)}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm text-red-600 font-medium">
                            売値: {parseFloat(market.bid).toFixed(market.currency_symbol.includes('JPY') ? 3 : 5)}
                          </div>
                          <div className="text-sm text-green-600 font-medium">
                            買値: {parseFloat(market.ask).toFixed(market.currency_symbol.includes('JPY') ? 3 : 5)}
                          </div>
                          <div className="font-bold text-gray-800">
                            中値: {parseFloat(market.mid_price).toFixed(market.currency_symbol.includes('JPY') ? 3 : 5)}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* ポジション一覧 */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                  <h2 className="text-xl font-bold text-gray-800 mb-6">オープンポジション</h2>
                  {positions.length > 0 ? (
                    <div className="space-y-3">
                      {positions.map((position) => (
                        <div key={position.id} className="p-4 bg-gray-50 rounded-lg border border-gray-100">
                          <div className="flex justify-between items-center">
                            <div>
                              <div className="font-bold text-gray-800">{position.currency_symbol}</div>
                              <div className="text-sm text-gray-500">
                                {position.side} {position.size.toLocaleString()}
                              </div>
                              <div className="text-sm text-gray-600">
                                エントリー: {parseFloat(position.entry_price).toFixed(position.currency_symbol.includes('JPY') ? 3 : 5)}
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-sm text-gray-600">
                                現在価格: {position.current_price ? parseFloat(position.current_price).toFixed(position.currency_symbol.includes('JPY') ? 3 : 5) : '-'}
                              </div>
                              <div className={`font-bold ${position.current_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {position.current_pnl >= 0 ? '+' : ''}¥{position.current_pnl.toLocaleString()}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center text-gray-400 py-8 bg-gray-50 rounded-lg">
                      <Target className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                      <p>現在オープンポジションはありません</p>
                    </div>
                  )}
                </div>
              </div>

              {/* TradingView リアルタイムチャート */}
              <div className="col-span-full">
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-6">
                  <div className="flex items-center justify-between">
                    <h2 className="text-xl font-bold text-gray-800">リアルタイムチャート</h2>
                    <div className="flex items-center space-x-3">
                      <label className="text-sm font-medium text-gray-700">通貨ペア:</label>
                      <select 
                        value={selectedSymbol}
                        onChange={(e) => setSelectedSymbol(e.target.value)}
                        className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="USD_JPY">USD/JPY</option>
                        <option value="EUR_JPY">EUR/JPY</option>
                        <option value="GBP_JPY">GBP/JPY</option>
                        <option value="EUR_USD">EUR/USD</option>
                        <option value="GBP_USD">GBP/USD</option>
                        <option value="AUD_USD">AUD/USD</option>
                      </select>
                    </div>
                  </div>
                </div>
                <TradingViewChart 
                  symbol={selectedSymbol} 
                  marketData={marketData}
                />
              </div>
            </div>
          )}

          {/* 他のメニュー項目のプレースホルダー */}
          {activeMenu === 'positions' && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
              <Target className="h-16 w-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-gray-800 mb-2">ポジション管理</h3>
              <p className="text-gray-500">ポジション管理機能は開発中です</p>
            </div>
          )}

          {activeMenu === 'strategies' && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
              <PieChart className="h-16 w-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-gray-800 mb-2">取引戦略</h3>
              <p className="text-gray-500">戦略管理機能は開発中です</p>
            </div>
          )}

          {activeMenu === 'reports' && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
              <FileText className="h-16 w-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-gray-800 mb-2">レポート</h3>
              <p className="text-gray-500">レポート機能は開発中です</p>
            </div>
          )}

          {activeMenu === 'settings' && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
              <Settings className="h-16 w-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-gray-800 mb-2">設定</h3>
              <p className="text-gray-500">設定機能は開発中です</p>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
