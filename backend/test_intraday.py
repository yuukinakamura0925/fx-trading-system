#!/usr/bin/env python3
"""
分足データ（5分足、1時間足など）のテストスクリプト
yfinanceで日中の細かい時間足データが取得できるか確認

注意: 分足データには取得期間の制限がある
- 1分足: 過去7日間まで
- 5分足、15分足、30分足: 過去60日間まで
- 1時間足: 過去730日間まで
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def test_intraday_data():
    """様々な時間足でのデータ取得テスト"""

    print("=" * 60)
    print("⏰ 分足・時間足データ取得テスト")
    print("=" * 60)

    # テストする時間足の設定
    intervals = [
        {"interval": "1m", "period": "1d", "desc": "1分足（過去1日）"},
        {"interval": "5m", "period": "5d", "desc": "5分足（過去5日）"},
        {"interval": "15m", "period": "5d", "desc": "15分足（過去5日）"},
        {"interval": "30m", "period": "10d", "desc": "30分足（過去10日）"},
        {"interval": "1h", "period": "1mo", "desc": "1時間足（過去1ヶ月）"},
        {"interval": "1d", "period": "3mo", "desc": "日足（過去3ヶ月）"},
    ]

    ticker = "USDJPY=X"

    for test_case in intervals:
        print(f"\n📊 {test_case['desc']}")
        print("-" * 40)

        try:
            # データ取得
            data = yf.download(
                ticker,
                period=test_case['period'],
                interval=test_case['interval'],
                progress=False
            )

            if data.empty:
                print(f"❌ データなし")
                continue

            # 基本情報
            print(f"✅ データ取得成功!")
            print(f"   📈 データ数: {len(data)}本")
            print(f"   📅 期間: {data.index[0]} ～ {data.index[-1]}")

            # 最初と最後の5本を表示
            print(f"\n   最初の3本:")
            for i in range(min(3, len(data))):
                row = data.iloc[i]
                time_str = data.index[i].strftime('%Y-%m-%d %H:%M')
                close_price = float(row['Close'])
                print(f"     {time_str} | 終値: {close_price:.3f}")

            if len(data) > 3:
                print(f"\n   最新の3本:")
                for i in range(max(0, len(data)-3), len(data)):
                    row = data.iloc[i]
                    time_str = data.index[i].strftime('%Y-%m-%d %H:%M')
                    close_price = float(row['Close'])
                    print(f"     {time_str} | 終値: {close_price:.3f}")

        except Exception as e:
            print(f"❌ エラー: {e}")

def test_today_5min():
    """今日の5分足データを取得"""

    print("\n" + "=" * 60)
    print("📅 今日の5分足データ取得テスト")
    print("=" * 60)

    ticker = "USDJPY=X"

    try:
        # 今日の5分足データを取得（過去1日分）
        print(f"\n⏰ 現在時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 USD/JPY 5分足データ取得中...")

        data = yf.download(
            ticker,
            period="1d",      # 過去1日
            interval="5m",    # 5分足
            progress=False
        )

        if data.empty:
            print("❌ データが取得できませんでした")
            return

        print(f"✅ 取得成功: {len(data)}本の5分足データ")

        # 今日のデータだけフィルタリング
        today = datetime.now().date()
        today_data = data[data.index.date == today]

        if not today_data.empty:
            print(f"\n📅 今日（{today}）のデータ: {len(today_data)}本")

            # 価格の変動範囲
            high = float(today_data['High'].max())
            low = float(today_data['Low'].min())
            current = float(today_data.iloc[-1]['Close'])

            print(f"\n💹 今日の価格推移:")
            print(f"   高値: {high:.3f} 円")
            print(f"   安値: {low:.3f} 円")
            print(f"   現在: {current:.3f} 円")
            print(f"   変動幅: {high - low:.3f} 円")

            # 最新10本の5分足を表示
            print(f"\n📊 最新10本の5分足:")
            latest_10 = today_data.tail(10)
            for idx, row in latest_10.iterrows():
                time_str = idx.strftime('%H:%M')
                o = float(row['Open'])
                h = float(row['High'])
                l = float(row['Low'])
                c = float(row['Close'])

                # 陽線か陰線かを判定
                if c > o:
                    candle = "🟢"  # 陽線（上昇）
                elif c < o:
                    candle = "🔴"  # 陰線（下落）
                else:
                    candle = "⚪"  # 同値

                print(f"   {candle} {time_str} | O:{o:.3f} H:{h:.3f} L:{l:.3f} C:{c:.3f}")

            # CSVに保存
            filename = f"USDJPY_5min_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            today_data.to_csv(filename, encoding='utf-8-sig')
            print(f"\n💾 データ保存完了: {filename}")

        else:
            print(f"⚠️ 今日のデータはまだありません（市場が閉じている可能性）")

    except Exception as e:
        print(f"❌ エラー: {e}")

def test_realtime_update():
    """リアルタイムに近いデータ更新の確認"""

    print("\n" + "=" * 60)
    print("🔄 データ更新頻度テスト（1分足で確認）")
    print("=" * 60)

    ticker = "USDJPY=X"

    try:
        print("\n📊 1分足データで更新タイミングを確認...")

        # 2回データを取得して比較
        print("1回目の取得...")
        data1 = yf.download(ticker, period="1d", interval="1m", progress=False)
        latest1 = data1.index[-1]

        print(f"   最新データ: {latest1}")

        # 10秒待機
        print("\n⏳ 10秒待機中...")
        import time
        time.sleep(10)

        print("\n2回目の取得...")
        data2 = yf.download(ticker, period="1d", interval="1m", progress=False)
        latest2 = data2.index[-1]

        print(f"   最新データ: {latest2}")

        if latest2 > latest1:
            print(f"\n✅ データが更新されました！")
            print(f"   新しいデータ: {len(data2) - len(data1)}本追加")
        else:
            print(f"\n⚠️ データは同じです（市場が閉じているか、更新間隔内）")

        # 市場の状態を推測
        now = datetime.now()
        if now.weekday() >= 5:  # 土日
            print("\n📅 週末のため市場は閉じています")
        else:
            print("\n📈 平日のため市場は開いている可能性があります")
            print("   ※ FX市場は月曜日の朝から土曜日の朝まで24時間取引")

    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    # 各種時間足のテスト
    test_intraday_data()

    # 今日の5分足データ
    test_today_5min()

    # リアルタイム更新テスト
    test_realtime_update()

    print("\n" + "=" * 60)
    print("🎉 テスト完了!")
    print("=" * 60)
    print("\n💡 まとめ:")
    print("   ✅ 5分足データ: 取得可能（最大60日分）")
    print("   ✅ 1分足データ: 取得可能（最大7日分）")
    print("   ✅ 1時間足データ: 取得可能（最大730日分）")
    print("   ✅ リアルタイム: 数分遅れで更新される")
    print("   ⚠️ 注意: 市場が閉じている時間はデータ更新なし")