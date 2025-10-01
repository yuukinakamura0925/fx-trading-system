"""
TFQE戦略（Trend-Follow Quick Exit）実装
強いトレンドに順張り → サクッと勝ち抜け型の実践的手法
"""

import sys
import os
import django

# Django設定
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fx_trading.settings')
django.setup()

from analysis.gmo_client import GMOFXClient
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ema(series, period):
    """EMA計算"""
    return series.ewm(span=period, adjust=False).mean()


def true_range(df):
    """True Range計算"""
    prev_close = df['Close'].shift(1)
    tr = pd.concat([
        (df['High'] - df['Low']),
        (df['High'] - prev_close).abs(),
        (df['Low'] - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr


def atr(df, period=14):
    """ATR計算"""
    tr = true_range(df)
    return tr.ewm(alpha=1/period, adjust=False).mean()


def adx(df, period=14):
    """ADX計算（トレンド強度）"""
    up = df['High'].diff()
    dn = -df['Low'].diff()

    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)

    tr_sum = true_range(df).rolling(period).sum()

    plus_dm_series = pd.Series(plus_dm, index=df.index)
    minus_dm_series = pd.Series(minus_dm, index=df.index)

    pdi = 100 * plus_dm_series.rolling(period).sum() / tr_sum
    mdi = 100 * minus_dm_series.rolling(period).sum() / tr_sum

    dx = (abs(pdi - mdi) / (pdi + mdi).replace(0, np.nan)) * 100
    return dx.rolling(period).mean()


def calculate_tfqe_indicators(df, timeframe):
    """TFQE戦略用のインジケーター計算"""
    if timeframe == '1H':
        # 1時間足：トレンドバイアス判定用
        df['EMA_50'] = ema(df['Close'], 50)
        df['EMA_200'] = ema(df['Close'], 200)
        df['ADX_14'] = adx(df, 14)

    elif timeframe == '15M':
        # 15分足：エントリータイミング検出用
        df['EMA_20'] = ema(df['Close'], 20)
        df['EMA_50'] = ema(df['Close'], 50)
        df['ATR_14'] = atr(df, 14)

        # 包み足（エンゴルフィング）検出
        prev_open = df['Open'].shift(1)
        prev_close = df['Close'].shift(1)
        prev_high = df['High'].shift(1)
        prev_low = df['Low'].shift(1)

        # 陽の包み足（買いシグナル）
        df['Bullish_Engulfing'] = (
            (prev_close < prev_open) &  # 前の足は陰線
            (df['Close'] > df['Open']) &  # 今の足は陽線
            (df['Open'] < prev_close) &  # 今の始値が前の終値より安い
            (df['Close'] > prev_open)  # 今の終値が前の始値より高い
        )

        # 陰の包み足（売りシグナル）
        df['Bearish_Engulfing'] = (
            (prev_close > prev_open) &  # 前の足は陽線
            (df['Close'] < df['Open']) &  # 今の足は陰線
            (df['Open'] > prev_close) &  # 今の始値が前の終値より高い
            (df['Close'] < prev_open)  # 今の終値が前の始値より安い
        )

        # 直近高値/安値ブレイク
        df['High_Break'] = df['Close'] > df['High'].rolling(3).max().shift(1)
        df['Low_Break'] = df['Close'] < df['Low'].rolling(3).min().shift(1)

    return df


def detect_tfqe_signal(df_h1, df_m15):
    """
    TFQE戦略のエントリーシグナル検出

    Args:
        df_h1: 1時間足データ
        df_m15: 15分足データ

    Returns:
        dict: シグナル情報
    """
    if df_h1.empty or df_m15.empty:
        return {'signal': 'NO_DATA', 'reason': 'データ不足'}

    # インジケーター計算
    df_h1 = calculate_tfqe_indicators(df_h1.copy(), '1H')
    df_m15 = calculate_tfqe_indicators(df_m15.copy(), '15M')

    # 最新データ
    latest_h1 = df_h1.iloc[-1]
    latest_m15 = df_m15.iloc[-1]
    prev_m15 = df_m15.iloc[-2] if len(df_m15) >= 2 else None

    # 現在時刻チェック（JST 16:00-24:00のみ）
    current_hour = datetime.now().hour
    if current_hour < 16 or current_hour >= 24:
        return {
            'signal': 'OUT_OF_SESSION',
            'reason': f'取引時間外（現在 {current_hour}時、取引は16-24時のみ）',
            'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    # === H1トレンドバイアス判定 ===
    h1_uptrend = (latest_h1['EMA_50'] > latest_h1['EMA_200']) and (latest_h1['ADX_14'] >= 20)
    h1_downtrend = (latest_h1['EMA_50'] < latest_h1['EMA_200']) and (latest_h1['ADX_14'] >= 20)

    if not h1_uptrend and not h1_downtrend:
        return {
            'signal': 'NO_TREND',
            'reason': f'H1でトレンドなし（ADX: {latest_h1["ADX_14"]:.1f}, EMA50: {latest_h1["EMA_50"]:.3f}, EMA200: {latest_h1["EMA_200"]:.3f}）',
            'h1_data': {
                'ema_50': float(latest_h1['EMA_50']),
                'ema_200': float(latest_h1['EMA_200']),
                'adx': float(latest_h1['ADX_14'])
            }
        }

    # === M15エントリー条件チェック ===
    current_price = latest_m15['Close']
    ema_20 = latest_m15['EMA_20']
    atr = latest_m15['ATR_14']

    # 上昇トレンド時の買いシグナル
    if h1_uptrend:
        # EMA20タッチ（押し目）
        touch_ema = latest_m15['Low'] <= ema_20 * 1.002  # 0.2%バッファ

        # エントリーシグナル：包み足 or 高値ブレイク
        entry_signal = latest_m15['Bullish_Engulfing'] or latest_m15['High_Break']

        if touch_ema and entry_signal:
            # エントリー価格とリスク管理
            entry_price = current_price
            sl_price = max(latest_m15['Low'] - 0.02, entry_price - atr * 0.8)  # SL
            risk = entry_price - sl_price

            if risk <= 0:
                return {'signal': 'INVALID_RISK', 'reason': 'リスク計算エラー'}

            tp1_price = entry_price + 1.0 * risk  # +1R
            tp2_price = entry_price + 2.5 * risk  # トレイル目標

            # リスクリワード比
            rr_ratio = (tp1_price - entry_price) / risk

            return {
                'signal': 'BUY',
                'strategy': 'TFQE順張り（上昇トレンド）',
                'reason': f'H1上昇トレンド + M15 EMA20押し + {"包み足" if latest_m15["Bullish_Engulfing"] else "高値ブレイク"}',
                'confidence': 75,
                'entry': float(entry_price),
                'stop_loss': float(sl_price),
                'take_profit_1': float(tp1_price),
                'take_profit_2': float(tp2_price),
                'risk_pips': float(risk * 100),
                'reward_pips': float((tp1_price - entry_price) * 100),
                'risk_reward': f'1:{rr_ratio:.2f}',
                'position_size': '半分はTP1で利確、残りはEMA20終値割れまで保持',
                'timeout': '90分経過 or 24:00で強制クローズ',
                'h1_bias': {
                    'trend': '上昇',
                    'ema_50': float(latest_h1['EMA_50']),
                    'ema_200': float(latest_h1['EMA_200']),
                    'adx': float(latest_h1['ADX_14'])
                },
                'm15_entry': {
                    'price': float(current_price),
                    'ema_20': float(ema_20),
                    'atr': float(atr),
                    'bullish_engulfing': bool(latest_m15['Bullish_Engulfing']),
                    'high_break': bool(latest_m15['High_Break'])
                }
            }

    # 下降トレンド時の売りシグナル
    if h1_downtrend:
        # EMA20タッチ（戻り）
        touch_ema = latest_m15['High'] >= ema_20 * 0.998  # 0.2%バッファ

        # エントリーシグナル：陰の包み足 or 安値ブレイク
        entry_signal = latest_m15['Bearish_Engulfing'] or latest_m15['Low_Break']

        if touch_ema and entry_signal:
            # エントリー価格とリスク管理
            entry_price = current_price
            sl_price = min(latest_m15['High'] + 0.02, entry_price + atr * 0.8)  # SL
            risk = sl_price - entry_price

            if risk <= 0:
                return {'signal': 'INVALID_RISK', 'reason': 'リスク計算エラー'}

            tp1_price = entry_price - 1.0 * risk  # +1R
            tp2_price = entry_price - 2.5 * risk  # トレイル目標

            # リスクリワード比
            rr_ratio = (entry_price - tp1_price) / risk

            return {
                'signal': 'SELL',
                'strategy': 'TFQE順張り（下降トレンド）',
                'reason': f'H1下降トレンド + M15 EMA20戻り + {"陰包み足" if latest_m15["Bearish_Engulfing"] else "安値ブレイク"}',
                'confidence': 75,
                'entry': float(entry_price),
                'stop_loss': float(sl_price),
                'take_profit_1': float(tp1_price),
                'take_profit_2': float(tp2_price),
                'risk_pips': float(risk * 100),
                'reward_pips': float((entry_price - tp1_price) * 100),
                'risk_reward': f'1:{rr_ratio:.2f}',
                'position_size': '半分はTP1で利確、残りはEMA20終値割れまで保持',
                'timeout': '90分経過 or 24:00で強制クローズ',
                'h1_bias': {
                    'trend': '下降',
                    'ema_50': float(latest_h1['EMA_50']),
                    'ema_200': float(latest_h1['EMA_200']),
                    'adx': float(latest_h1['ADX_14'])
                },
                'm15_entry': {
                    'price': float(current_price),
                    'ema_20': float(ema_20),
                    'atr': float(atr),
                    'bearish_engulfing': bool(latest_m15['Bearish_Engulfing']),
                    'low_break': bool(latest_m15['Low_Break'])
                }
            }

    # エントリー条件を満たさない
    if h1_uptrend:
        return {
            'signal': 'WAITING_PULLBACK',
            'reason': 'H1上昇トレンド中だが、M15でEMA20への押し目待ち',
            'h1_trend': '上昇',
            'm15_status': {
                'price': float(current_price),
                'ema_20': float(ema_20),
                'distance_from_ema': f'{((current_price - ema_20) / ema_20 * 100):.2f}%'
            }
        }
    elif h1_downtrend:
        return {
            'signal': 'WAITING_RALLY',
            'reason': 'H1下降トレンド中だが、M15でEMA20への戻り待ち',
            'h1_trend': '下降',
            'm15_status': {
                'price': float(current_price),
                'ema_20': float(ema_20),
                'distance_from_ema': f'{((current_price - ema_20) / ema_20 * 100):.2f}%'
            }
        }


def main():
    """メイン処理"""
    print("=" * 100)
    print("TFQE戦略（Trend-Follow Quick Exit）- USD/JPY エントリーシグナル判定")
    print("=" * 100)
    print("\n強いトレンドに順張り → サクッと勝ち抜け型の実践的手法\n")

    client = GMOFXClient()

    print("-" * 100)
    print("データ取得中...")
    print("-" * 100 + "\n")

    # 1時間足データ取得（トレンドバイアス判定用）
    print("【1時間足】取得中...", end=" ", flush=True)
    df_h1 = client.get_klines_multi_days(
        symbol='USD_JPY',
        interval='1hour',
        days=365,  # 1年分
        price_type='ASK'
    )

    if not df_h1.empty:
        print(f"{len(df_h1):,} 件 ✓")
    else:
        print("データ取得失敗 ✗")
        return

    # 15分足データ取得（エントリータイミング検出用）
    # GMO APIは15分足をサポートしているか確認（なければ5分足で代用）
    print("【15分足】取得中...", end=" ", flush=True)
    df_m15 = client.get_klines_multi_days(
        symbol='USD_JPY',
        interval='15min',
        days=90,  # 90日分
        price_type='ASK'
    )

    if not df_m15.empty:
        print(f"{len(df_m15):,} 件 ✓")
    else:
        print("15分足データなし、5分足で代用...", end=" ", flush=True)
        df_m15 = client.get_klines_multi_days(
            symbol='USD_JPY',
            interval='5min',
            days=90,
            price_type='ASK'
        )
        if not df_m15.empty:
            print(f"{len(df_m15):,} 件（5分足）✓")
        else:
            print("データ取得失敗 ✗")
            return

    # シグナル検出
    print("\n" + "-" * 100)
    print("TFQE戦略シグナル分析中...")
    print("-" * 100 + "\n")

    signal = detect_tfqe_signal(df_h1, df_m15)

    # 結果表示
    print("=" * 100)
    print("🎯 TFQE戦略 エントリーシグナル")
    print("=" * 100 + "\n")

    print(f"【シグナル】 {signal['signal']}")
    print(f"【理由】 {signal['reason']}")

    if signal['signal'] in ['BUY', 'SELL']:
        print(f"【戦略】 {signal['strategy']}")
        print(f"【信頼度】 {signal['confidence']}%")

        print(f"\n【エントリー】 {signal['entry']:.3f} JPY")
        print(f"【損切り（SL）】 {signal['stop_loss']:.3f} JPY")
        print(f"【利確1（TP1）】 {signal['take_profit_1']:.3f} JPY （半分利確 + 建値移動）")
        print(f"【利確2（TP2）】 {signal['take_profit_2']:.3f} JPY （トレイル目標）")

        print(f"\n【リスク】 {signal['risk_pips']:.1f} pips")
        print(f"【リワード】 {signal['reward_pips']:.1f} pips")
        print(f"【リスクリワード比】 {signal['risk_reward']}")

        print(f"\n【ポジション管理】")
        print(f"  - {signal['position_size']}")
        print(f"  - タイムアウト: {signal['timeout']}")
        print(f"  - 推奨ロット: 口座残高の0.5-1.0%をリスクに")

        print(f"\n【H1トレンドバイアス】")
        print(f"  トレンド: {signal['h1_bias']['trend']}")
        print(f"  EMA50: {signal['h1_bias']['ema_50']:.3f}")
        print(f"  EMA200: {signal['h1_bias']['ema_200']:.3f}")
        print(f"  ADX(14): {signal['h1_bias']['adx']:.1f}")

        print(f"\n【M15エントリー状況】")
        print(f"  現在価格: {signal['m15_entry']['price']:.3f}")
        print(f"  EMA20: {signal['m15_entry']['ema_20']:.3f}")
        print(f"  ATR(14): {signal['m15_entry']['atr']:.4f}")
        if signal['signal'] == 'BUY':
            print(f"  包み足: {'✓' if signal['m15_entry']['bullish_engulfing'] else '✗'}")
            print(f"  高値ブレイク: {'✓' if signal['m15_entry']['high_break'] else '✗'}")
        else:
            print(f"  陰包み足: {'✓' if signal['m15_entry']['bearish_engulfing'] else '✗'}")
            print(f"  安値ブレイク: {'✓' if signal['m15_entry']['low_break'] else '✗'}")

    elif signal['signal'] in ['WAITING_PULLBACK', 'WAITING_RALLY']:
        print(f"\n【H1トレンド】 {signal.get('h1_trend', 'N/A')}")
        print(f"【M15状況】")
        if 'm15_status' in signal:
            print(f"  現在価格: {signal['m15_status']['price']:.3f}")
            print(f"  EMA20: {signal['m15_status']['ema_20']:.3f}")
            print(f"  EMA20からの乖離: {signal['m15_status']['distance_from_ema']}")

    elif signal['signal'] == 'NO_TREND':
        if 'h1_data' in signal:
            print(f"\n【H1データ】")
            print(f"  EMA50: {signal['h1_data']['ema_50']:.3f}")
            print(f"  EMA200: {signal['h1_data']['ema_200']:.3f}")
            print(f"  ADX: {signal['h1_data']['adx']:.1f} （20未満はトレンドなし）")

    elif signal['signal'] == 'OUT_OF_SESSION':
        print(f"\n取引可能時間: 16:00 - 24:00 JST")
        if 'current_time' in signal:
            print(f"現在時刻: {signal['current_time']}")

    print("\n" + "=" * 100)
    print("✅ 分析完了")
    print("=" * 100)


if __name__ == '__main__':
    main()
