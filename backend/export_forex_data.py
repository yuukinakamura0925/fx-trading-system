#!/usr/bin/env python3
"""
為替データをCSVファイルに出力するスクリプト
yfinanceから取得したFXデータをCSV形式で保存する

CSVファイルには日時、始値、高値、安値、終値、出来高が含まれる
複数の通貨ペアを取得して、それぞれ個別のファイルに保存
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
import os

def create_data_directory():
    """データ保存用ディレクトリを作成"""
    data_dir = "forex_data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"📁 ディレクトリ作成: {data_dir}/")
    return data_dir

def export_single_pair(symbol, name, period="3mo", interval="1d", data_dir="forex_data"):
    """
    単一通貨ペアのデータを取得してCSVに出力

    Args:
        symbol (str): Yahoo Financeのシンボル (例: "USDJPY=X")
        name (str): 通貨ペア名 (例: "USD_JPY")
        period (str): 取得期間 (1mo, 3mo, 6mo, 1y, 5y, max)
        interval (str): データ間隔 (1d, 1h, 5m など)
        data_dir (str): 保存先ディレクトリ

    Returns:
        bool: 成功した場合True
    """

    try:
        print(f"\n📊 {name} のデータを取得中...")
        print(f"   期間: {period}, 間隔: {interval}")

        # データ取得
        data = yf.download(
            symbol,
            period=period,
            interval=interval,
            progress=False  # プログレスバーを非表示
        )

        if data.empty:
            print(f"❌ {name}: データが取得できませんでした")
            return False

        # カラム名を整理（マルチインデックスの場合は最初のレベルを使用）
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        # カラム名を日本語でわかりやすくする
        data_renamed = data.copy()
        data_renamed.columns = ['終値', '高値', '安値', '始値', '出来高']

        # 並び順を変更（始値、高値、安値、終値、出来高の順）
        data_ordered = data_renamed[['始値', '高値', '安値', '終値', '出来高']]

        # タイムスタンプを追加
        data_ordered.index.name = '日時'

        # ファイル名を作成（期間と間隔を含む）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{name}_{period}_{interval}_{timestamp}.csv"
        filepath = os.path.join(data_dir, filename)

        # CSVファイルに出力
        data_ordered.to_csv(filepath, encoding='utf-8-sig')  # utf-8-sigでExcelでも文字化けしない

        # 統計情報を計算
        stats = {
            'データ数': len(data),
            '開始日': data.index[0].strftime('%Y-%m-%d'),
            '終了日': data.index[-1].strftime('%Y-%m-%d'),
            '最高値': float(data['High'].max()),
            '最安値': float(data['Low'].min()),
            '平均終値': float(data['Close'].mean()),
            '変動率(%)': ((float(data['Close'].iloc[-1]) - float(data['Close'].iloc[0])) / float(data['Close'].iloc[0])) * 100
        }

        print(f"✅ {name}: 保存完了!")
        print(f"   📄 ファイル: {filename}")
        print(f"   📊 データ数: {stats['データ数']}行")
        print(f"   📅 期間: {stats['開始日']} ～ {stats['終了日']}")
        print(f"   💹 最高値: {stats['最高値']:.2f} 円")
        print(f"   📉 最安値: {stats['最安値']:.2f} 円")
        print(f"   📊 平均終値: {stats['平均終値']:.2f} 円")
        print(f"   📈 期間変動率: {stats['変動率(%)']:+.2f}%")

        # 統計情報もCSVに保存
        stats_filename = f"{name}_stats_{timestamp}.csv"
        stats_filepath = os.path.join(data_dir, stats_filename)
        stats_df = pd.DataFrame([stats])
        stats_df.to_csv(stats_filepath, index=False, encoding='utf-8-sig')
        print(f"   📊 統計ファイル: {stats_filename}")

        return True

    except Exception as e:
        print(f"❌ {name}: エラーが発生しました: {e}")
        return False

def export_multiple_pairs():
    """複数の通貨ペアのデータを一括で取得してCSVに出力"""

    print("=" * 60)
    print("🌍 為替データCSVエクスポート")
    print("=" * 60)

    # データディレクトリ作成
    data_dir = create_data_directory()

    # 取得する通貨ペアの設定
    currency_pairs = [
        {"symbol": "USDJPY=X", "name": "USD_JPY", "desc": "米ドル/円"},
        {"symbol": "EURJPY=X", "name": "EUR_JPY", "desc": "ユーロ/円"},
        {"symbol": "GBPJPY=X", "name": "GBP_JPY", "desc": "英ポンド/円"},
        {"symbol": "AUDJPY=X", "name": "AUD_JPY", "desc": "豪ドル/円"},
        {"symbol": "NZDJPY=X", "name": "NZD_JPY", "desc": "NZドル/円"},
        {"symbol": "CADJPY=X", "name": "CAD_JPY", "desc": "カナダドル/円"},
        {"symbol": "CHFJPY=X", "name": "CHF_JPY", "desc": "スイスフラン/円"},
        {"symbol": "EURUSD=X", "name": "EUR_USD", "desc": "ユーロ/米ドル"},
    ]

    # 各種期間でデータ取得
    periods = [
        {"period": "1mo", "desc": "1ヶ月"},
        {"period": "3mo", "desc": "3ヶ月"},
        {"period": "1y", "desc": "1年"},
    ]

    success_count = 0
    total_count = 0

    # メイン通貨ペア（USD/JPY）の複数期間データを取得
    print("\n📌 主要通貨ペア (USD/JPY) の複数期間データ")
    print("-" * 40)
    for period_info in periods:
        total_count += 1
        if export_single_pair("USDJPY=X", f"USD_JPY", period=period_info["period"], data_dir=data_dir):
            success_count += 1

    # 全通貨ペアの3ヶ月データを取得
    print("\n📌 全通貨ペアの3ヶ月データ")
    print("-" * 40)
    for pair in currency_pairs:
        total_count += 1
        if export_single_pair(pair["symbol"], pair["name"], period="3mo", data_dir=data_dir):
            success_count += 1

    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 エクスポート完了!")
    print("=" * 60)
    print(f"✅ 成功: {success_count}/{total_count} ファイル")
    print(f"📁 保存先: ./{data_dir}/")
    print(f"📝 ファイル形式: CSV (UTF-8 BOM付き)")
    print(f"💡 Excelで開いても文字化けしません")

    # ディレクトリ内のファイルリストを表示
    print("\n📄 作成されたファイル一覧:")
    files = os.listdir(data_dir)
    csv_files = [f for f in files if f.endswith('.csv')]
    for i, file in enumerate(sorted(csv_files), 1):
        size = os.path.getsize(os.path.join(data_dir, file)) / 1024  # KB単位
        print(f"   {i}. {file} ({size:.1f} KB)")

if __name__ == "__main__":
    # メイン実行
    export_multiple_pairs()

    print("\n💡 ヒント:")
    print("   - CSVファイルはExcelやGoogleスプレッドシートで開けます")
    print("   - pandasで読み込む場合: pd.read_csv('ファイル名.csv', index_col='日時', parse_dates=True)")
    print("   - より詳細な期間が必要な場合は period='5y' や period='max' を指定できます")
    print("   - より細かい間隔が必要な場合は interval='1h' や interval='5m' を指定できます")