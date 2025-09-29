#!/usr/bin/env python3
"""
yfinanceライブラリのテストスクリプト
USD/JPYの過去為替データを取得して内容を確認する

yfinance: Yahoo Financeから株価・為替データを取得するPythonライブラリ
非公式だが最も使いやすく、無料で利用可能
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def test_usdjpy_data():
    """USD/JPYの過去データを取得してテスト"""

    print("=" * 50)
    print("yfinance テスト: USD/JPY 為替データ取得")
    print("=" * 50)

    try:
        # USD/JPYの過去1ヶ月のデータを取得
        # USDJPY=X: Yahoo FinanceでのUSD/JPY通貨ペアのシンボル
        print("📊 USD/JPY 過去1ヶ月のデータを取得中...")
        ticker = "USDJPY=X"
        data = yf.download(
            ticker,
            period="1mo",      # 期間: 1ヶ月
            interval="1d"      # 間隔: 1日
        )

        if data.empty:
            print("❌ データが取得できませんでした")
            return False

        print(f"✅ データ取得成功! {len(data)}日分のデータ")
        print(f"📅 期間: {data.index[0].date()} ～ {data.index[-1].date()}")

        # データの基本情報を表示
        print("\n📈 データの基本情報:")
        print(f"   - 行数: {len(data)}")
        print(f"   - 列数: {len(data.columns)}")
        print(f"   - 列名: {list(data.columns)}")

        # 最新の価格情報
        latest = data.iloc[-1]
        print(f"\n💱 最新価格情報 ({data.index[-1].date()}):")
        print(f"   - 始値 (Open): {float(latest['Open']):.2f} 円")
        print(f"   - 高値 (High): {float(latest['High']):.2f} 円")
        print(f"   - 安値 (Low): {float(latest['Low']):.2f} 円")
        print(f"   - 終値 (Close): {float(latest['Close']):.2f} 円")
        print(f"   - 出来高 (Volume): {float(latest['Volume'])}")

        # 過去1ヶ月の変動
        first_close = float(data.iloc[0]['Close'])
        last_close = float(data.iloc[-1]['Close'])
        change = last_close - first_close
        change_pct = (change / first_close) * 100

        print(f"\n📊 過去1ヶ月の変動:")
        print(f"   - 開始時価格: {first_close:.2f} 円")
        print(f"   - 最終価格: {last_close:.2f} 円")
        print(f"   - 変動額: {change:+.2f} 円")
        print(f"   - 変動率: {change_pct:+.2f}%")

        # 最高値・最安値
        max_price = float(data['High'].max())
        min_price = float(data['Low'].min())
        max_date = data[data['High'] == data['High'].max()].index[0].date()
        min_date = data[data['Low'] == data['Low'].min()].index[0].date()

        print(f"\n🔝 期間中の最高値・最安値:")
        print(f"   - 最高値: {max_price:.2f} 円 ({max_date})")
        print(f"   - 最安値: {min_price:.2f} 円 ({min_date})")

        # 最初の5日分のデータをサンプル表示
        print(f"\n📋 サンプルデータ (最初の5日):")
        print(data.head().round(2))

        return True

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False

def test_multiple_pairs():
    """複数の通貨ペアのテスト"""

    print("\n" + "=" * 50)
    print("複数通貨ペアのテスト")
    print("=" * 50)

    # テストする通貨ペア
    pairs = {
        "USDJPY=X": "米ドル/円",
        "EURJPY=X": "ユーロ/円",
        "GBPJPY=X": "英ポンド/円",
        "AUDJPY=X": "豪ドル/円"
    }

    for symbol, name in pairs.items():
        try:
            print(f"\n📊 {name} ({symbol}) のデータ取得中...")
            data = yf.download(symbol, period="5d", interval="1d")

            if not data.empty:
                latest_price = float(data.iloc[-1]['Close'])
                print(f"   ✅ 成功: 最新価格 {latest_price:.2f} 円")
            else:
                print(f"   ❌ データなし")

        except Exception as e:
            print(f"   ❌ エラー: {e}")

if __name__ == "__main__":
    # メインテスト実行
    success = test_usdjpy_data()

    if success:
        # 複数通貨ペアのテスト
        test_multiple_pairs()

        print("\n" + "=" * 50)
        print("🎉 yfinance テスト完了!")
        print("✅ Yahoo Financeから無料で為替データが取得できることを確認")
        print("💡 次のステップ: Djangoモデルに保存してチャート表示")
        print("=" * 50)
    else:
        print("\n❌ テスト失敗")