"""
TFQE戦略（Trend-Follow Quick Exit）ロジック
API viewsから呼び出される関数群
"""

import pandas as pd
import numpy as np


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

        # 陽の包み足（買いシグナル）
        df['Bullish_Engulfing'] = (
            (prev_close < prev_open) &
            (df['Close'] > df['Open']) &
            (df['Open'] < prev_close) &
            (df['Close'] > prev_open)
        )

        # 陰の包み足（売りシグナル）
        df['Bearish_Engulfing'] = (
            (prev_close > prev_open) &
            (df['Close'] < df['Open']) &
            (df['Open'] > prev_close) &
            (df['Close'] < prev_open)
        )

        # 直近高値/安値ブレイク
        df['High_Break'] = df['Close'] > df['High'].rolling(3).max().shift(1)
        df['Low_Break'] = df['Close'] < df['Low'].rolling(3).min().shift(1)

    return df


def detect_tfqe_signal(df_h1, df_m15, current_hour=None):
    """
    TFQE戦略のエントリーシグナル検出

    Args:
        df_h1: 1時間足データ
        df_m15: 15分足データ
        current_hour: 現在の時刻（JST）、Noneの場合は時間チェックスキップ

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

    # 時間チェック（JST 16:00-24:00のみ）
    if current_hour is not None:
        if current_hour < 16 or current_hour >= 24:
            return {
                'signal': 'OUT_OF_SESSION',
                'reason': f'取引時間外（現在 {current_hour}時、取引は16-24時のみ）'
            }

    # === H1トレンドバイアス判定 ===
    h1_uptrend = (latest_h1['EMA_50'] > latest_h1['EMA_200']) and (latest_h1['ADX_14'] >= 20)
    h1_downtrend = (latest_h1['EMA_50'] < latest_h1['EMA_200']) and (latest_h1['ADX_14'] >= 20)

    if not h1_uptrend and not h1_downtrend:
        return {
            'signal': 'NO_TREND',
            'reason': f'H1でトレンドなし（ADX: {latest_h1["ADX_14"]:.1f}）',
            'h1_data': {
                'ema_50': float(latest_h1['EMA_50']),
                'ema_200': float(latest_h1['EMA_200']),
                'adx': float(latest_h1['ADX_14'])
            }
        }

    # === M15エントリー条件チェック ===
    current_price = latest_m15['Close']
    ema_20 = latest_m15['EMA_20']
    atr_val = latest_m15['ATR_14']

    # 上昇トレンド時の買いシグナル
    if h1_uptrend:
        touch_ema = latest_m15['Low'] <= ema_20 * 1.002
        entry_signal = latest_m15['Bullish_Engulfing'] or latest_m15['High_Break']

        if touch_ema and entry_signal:
            entry_price = current_price
            sl_price = max(latest_m15['Low'] - 0.02, entry_price - atr_val * 0.8)
            risk = entry_price - sl_price

            if risk <= 0:
                return {'signal': 'INVALID_RISK', 'reason': 'リスク計算エラー'}

            tp1_price = entry_price + 1.0 * risk
            tp2_price = entry_price + 2.5 * risk

            return {
                'signal': 'BUY',
                'strategy': 'TFQE順張り（上昇）',
                'reason': f'H1上昇 + M15押し目 + {"包み足" if latest_m15["Bullish_Engulfing"] else "高値ブレイク"}',
                'confidence': 75,
                'entry': float(entry_price),
                'stop_loss': float(sl_price),
                'take_profit_1': float(tp1_price),
                'take_profit_2': float(tp2_price),
                'risk_pips': float(risk * 100),
                'reward_pips': float((tp1_price - entry_price) * 100),
                'h1_trend': '上昇',
                'h1_adx': float(latest_h1['ADX_14']),
                'm15_ema20': float(ema_20),
                'm15_atr': float(atr_val)
            }

    # 下降トレンド時の売りシグナル
    if h1_downtrend:
        touch_ema = latest_m15['High'] >= ema_20 * 0.998
        entry_signal = latest_m15['Bearish_Engulfing'] or latest_m15['Low_Break']

        if touch_ema and entry_signal:
            entry_price = current_price
            sl_price = min(latest_m15['High'] + 0.02, entry_price + atr_val * 0.8)
            risk = sl_price - entry_price

            if risk <= 0:
                return {'signal': 'INVALID_RISK', 'reason': 'リスク計算エラー'}

            tp1_price = entry_price - 1.0 * risk
            tp2_price = entry_price - 2.5 * risk

            return {
                'signal': 'SELL',
                'strategy': 'TFQE順張り（下降）',
                'reason': f'H1下降 + M15戻り + {"陰包み" if latest_m15["Bearish_Engulfing"] else "安値ブレイク"}',
                'confidence': 75,
                'entry': float(entry_price),
                'stop_loss': float(sl_price),
                'take_profit_1': float(tp1_price),
                'take_profit_2': float(tp2_price),
                'risk_pips': float(risk * 100),
                'reward_pips': float((entry_price - tp1_price) * 100),
                'h1_trend': '下降',
                'h1_adx': float(latest_h1['ADX_14']),
                'm15_ema20': float(ema_20),
                'm15_atr': float(atr_val)
            }

    # エントリー条件を満たさない
    if h1_uptrend:
        return {
            'signal': 'WAITING_PULLBACK',
            'reason': 'H1上昇中、M15でEMA20押し待ち',
            'h1_trend': '上昇',
            'm15_price': float(current_price),
            'm15_ema20': float(ema_20),
            'distance': f'{((current_price - ema_20) / ema_20 * 100):.2f}%'
        }
    else:
        return {
            'signal': 'WAITING_RALLY',
            'reason': 'H1下降中、M15でEMA20戻り待ち',
            'h1_trend': '下降',
            'm15_price': float(current_price),
            'm15_ema20': float(ema_20),
            'distance': f'{((current_price - ema_20) / ema_20 * 100):.2f}%'
        }
