#!/usr/bin/env python3
"""
マルチタイムフレーム分析のテストスクリプト
5分足・1時間足・4時間足・日足の4つの時間軸で総合的に分析
"""

from analysis.multi_timeframe_analyzer import MultiTimeFrameAnalyzer
import json

def test_multi_timeframe_analysis():
    """マルチタイムフレーム分析のテスト"""

    print("=" * 80)
    print("🕐 マルチタイムフレームFX分析システム")
    print("=" * 80)

    analyzer = MultiTimeFrameAnalyzer()

    # USD/JPYの全時間軸分析
    result = analyzer.analyze_all_timeframes("USDJPY=X")

    if "error" in result:
        print(f"❌ エラー: {result['error']}")
        return

    print(f"\n📊 {result['symbol']} 総合分析結果")
    print(f"⏰ 分析時刻: {result['timestamp']}")

    # 各時間軸の結果表示
    print("\n" + "=" * 60)
    print("📈 時間軸別分析結果")
    print("=" * 60)

    timeframes = result["timeframe_analyses"]

    for timeframe, analysis in timeframes.items():
        if "error" in analysis:
            print(f"❌ {timeframe}: {analysis['error']}")
            continue

        print(f"\n🕐 {analysis['description']}")
        print("-" * 40)

        ta = analysis["analysis"]
        print(f"現在価格: {ta['current_price']:.3f}円")
        print(f"トレンド: {ta['trend']}")
        print(f"シグナル: {ta['signal']} (信頼度: {ta['confidence']:.1f}%)")
        print(f"RSI: {ta['rsi']:.1f}")
        print(f"モメンタム: {ta['momentum']}")
        print(f"ボラティリティ: {ta['volatility']:.2f}%")

        # エントリーポイント表示
        if analysis.get("entry_points"):
            print(f"\n📍 {analysis['trading_style']}エントリーポイント:")
            for entry in analysis["entry_points"]:
                print(f"   • {entry['type']}: {entry['price']:.3f}円")
                print(f"     利確: {entry['take_profit']:.3f}円, 損切: {entry['stop_loss']:.3f}円")
                print(f"     期間: {entry['timeframe']}, 理由: {entry['reason']}")

        # 戦略情報
        strategy = analysis.get("strategy", {})
        if strategy:
            print(f"\n🎯 {strategy['style']}戦略:")
            print(f"   保有期間: {strategy['holding_period']}")
            print(f"   利益目標: {strategy['profit_target']}")
            print(f"   最適セッション: {', '.join(strategy['best_sessions'])}")

    # 統合戦略表示
    print("\n" + "=" * 60)
    print("🎯 統合戦略・総合判断")
    print("=" * 60)

    integrated = result["integrated_strategy"]

    print(f"📊 統合シグナル: {integrated['integrated_signal']}")
    print(f"🎯 総合信頼度: {integrated['confidence']:.1f}%")
    print(f"📈 シグナル一致度: {integrated['signal_alignment']}")
    print(f"⚠️ 総合リスクレベル: {integrated['risk_level']}")

    # 推奨戦略
    if integrated.get("recommended_strategies"):
        print(f"\n🏆 推奨戦略 (上位3つ):")
        for i, strategy in enumerate(integrated["recommended_strategies"], 1):
            print(f"   {i}. {strategy['style']} (信頼度: {strategy['confidence']:.1f}%)")
            print(f"      時間軸: {strategy['timeframe']}, 優先度: {strategy['priority']}")

    # 市場タイミング
    timing = integrated.get("market_timing", {})
    if timing:
        print(f"\n⏰ 市場タイミング分析:")
        print(f"   現在セッション: {timing.get('current_session', 'N/A')}")
        print(f"   活動レベル: {timing.get('activity_level', 'N/A')}")
        print(f"   週のタイミング: {timing.get('week_timing', 'N/A')}")
        print(f"   推奨: {timing.get('recommendation', 'N/A')}")

    # 現在の市場セッション
    market_session = result.get("market_session", {})
    if market_session:
        print(f"\n🌍 現在の市場環境:")
        active_sessions = market_session.get("active_sessions", [])
        print(f"   活動中市場: {', '.join(active_sessions) if active_sessions else 'なし'}")
        print(f"   最適スタイル: {market_session.get('optimal_for', 'N/A')}")

    print("\n" + "=" * 80)
    print("✅ マルチタイムフレーム分析完了!")
    print("=" * 80)

    return result

def test_specific_timeframes():
    """特定時間軸のテスト"""

    print("\n" + "=" * 60)
    print("🔍 時間軸別詳細テスト")
    print("=" * 60)

    analyzer = MultiTimeFrameAnalyzer()

    # 各時間軸を個別テスト
    test_cases = [
        ("5分足スキャルピング", "5m"),
        ("1時間足デイトレード", "1h"),
        ("4時間足ポジション", "4h"),
        ("日足スイング", "1d")
    ]

    for description, timeframe in test_cases:
        print(f"\n📊 {description} テスト")
        print("-" * 30)

        try:
            # 単一時間軸でのデータ取得テスト
            import yfinance as yf

            if timeframe == "5m":
                data = yf.download("USDJPY=X", period="1d", interval="5m", progress=False)
            elif timeframe == "1h":
                data = yf.download("USDJPY=X", period="5d", interval="1h", progress=False)
            elif timeframe == "4h":
                data = yf.download("USDJPY=X", period="1mo", interval="1h", progress=False)  # 4h代替
            else:
                data = yf.download("USDJPY=X", period="3mo", interval="1d", progress=False)

            print(f"✅ データ取得成功: {len(data)}本")
            print(f"   期間: {data.index[0]} ～ {data.index[-1]}")

            if len(data) > 0:
                latest_price = data['Close'].iloc[-1]
                if hasattr(latest_price, 'iloc'):
                    latest_price = latest_price.iloc[0]
                print(f"   最新価格: {float(latest_price):.3f}円")

        except Exception as e:
            print(f"❌ エラー: {e}")

if __name__ == "__main__":
    # メインテスト実行
    result = test_multi_timeframe_analysis()

    # 特定時間軸テスト
    test_specific_timeframes()

    # 結果をJSONファイルに保存
    if result and "error" not in result:
        with open('multi_timeframe_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n💾 分析結果を multi_timeframe_analysis.json に保存しました")

    print(f"\n💡 次のステップ:")
    print(f"   • 各時間軸の戦略を組み合わせたポートフォリオ運用")
    print(f"   • リアルタイムアラート機能の追加")
    print(f"   • バックテスト機能で戦略検証")