"""
TFQE戦略API View
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from .gmo_client import GMOFXClient
from .tfqe_strategy import detect_tfqe_signal
from datetime import datetime
import logging
import pandas as pd

logger = logging.getLogger(__name__)

# キャッシュキー
CACHE_KEY_H1 = 'tfqe_h1_data'
CACHE_KEY_M15 = 'tfqe_m15_data'
# キャッシュ有効期限（秒）
CACHE_TIMEOUT_H1 = 3600  # 1時間足は1時間キャッシュ
CACHE_TIMEOUT_M15 = 900  # 15分足は15分キャッシュ


class TFQESignalView(APIView):
    """
    TFQE戦略のエントリーシグナルを返すAPI

    GET /api/analysis/tfqe-signal/
    """

    def get_cached_data(self, cache_key, interval, days, price_type='ASK'):
        """
        キャッシュからデータ取得、期限切れなら最新データのみ追加取得
        """
        from datetime import datetime, timedelta

        # キャッシュ確認
        cached_data = cache.get(cache_key)
        client = GMOFXClient()

        if cached_data is not None:
            df_cached = pd.read_json(cached_data, orient='index')

            # 最新データの時刻を確認
            last_timestamp = df_cached.index[-1]
            now = datetime.now()

            # 次の足の時刻を計算
            if interval == '1hour':
                next_candle = last_timestamp + timedelta(hours=1)
            elif interval == '15min':
                next_candle = last_timestamp + timedelta(minutes=15)
            elif interval == '5min':
                next_candle = last_timestamp + timedelta(minutes=5)
            else:
                next_candle = last_timestamp + timedelta(hours=1)

            # まだ次の足が確定していない
            if now < next_candle:
                logger.info(f"キャッシュヒット（最新）: {cache_key}")
                return df_cached

            # 新しい足が出ている、最新1日分だけ取得して追加
            logger.info(f"キャッシュ更新（差分取得）: {cache_key}")
            today_str = now.strftime("%Y%m%d")

            try:
                new_klines = client.get_klines(
                    symbol='USD_JPY',
                    interval=interval,
                    date=today_str,
                    price_type=price_type
                )

                if new_klines:
                    # 新しいデータをDataFrameに変換
                    df_new = pd.DataFrame(new_klines)
                    df_new['openTime'] = pd.to_datetime(df_new['openTime'])
                    df_new.set_index('openTime', inplace=True)
                    df_new = df_new[['Open', 'High', 'Low', 'Close', 'Volume']]
                    df_new = df_new.apply(pd.to_numeric, errors='coerce')

                    # 既存データと結合（重複は後者を優先）
                    df_combined = pd.concat([df_cached, df_new])
                    df_combined = df_combined[~df_combined.index.duplicated(keep='last')]
                    df_combined = df_combined.sort_index()

                    # 古いデータを削除（必要な期間だけ保持）
                    cutoff_date = now - timedelta(days=days)
                    df_combined = df_combined[df_combined.index >= cutoff_date]

                    # 更新したデータをキャッシュ
                    cache.set(cache_key, df_combined.to_json(orient='index'), None)  # 無期限
                    logger.info(f"キャッシュ更新完了: {cache_key} (新規: {len(df_new)}本)")
                    return df_combined
                else:
                    # 新データなし、既存を返す
                    return df_cached
            except Exception as e:
                logger.warning(f"差分取得失敗、キャッシュ使用: {e}")
                return df_cached

        # キャッシュなし、全データ取得
        logger.info(f"キャッシュなし、全データ取得: {cache_key}")
        df = client.get_klines_multi_days(
            symbol='USD_JPY',
            interval=interval,
            days=days,
            price_type=price_type
        )

        if not df.empty:
            cache.set(cache_key, df.to_json(orient='index'), None)  # 無期限キャッシュ
            logger.info(f"キャッシュ保存: {cache_key} ({len(df)}本)")

        return df

    def get(self, request):
        """
        TFQE戦略シグナル取得
        """
        try:
            # 1時間足データ取得（キャッシュ利用）
            logger.info("1時間足データ取得開始")
            df_h1 = self.get_cached_data(CACHE_KEY_H1, '1hour', 365)

            if df_h1.empty:
                return Response({
                    'error': '1時間足データ取得失敗'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 15分足データ取得（キャッシュ利用）
            logger.info("15分足データ取得開始")
            df_m15 = self.get_cached_data(CACHE_KEY_M15, '15min', 90)

            if df_m15.empty:
                # 15分足がなければ5分足で代用
                logger.info("15分足なし、5分足で代用")
                df_m15 = self.get_cached_data('tfqe_5min_data', '5min', 90)

            if df_m15.empty:
                return Response({
                    'error': '15分足データ取得失敗'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # シグナル検出
            current_hour = datetime.now().hour
            signal = detect_tfqe_signal(df_h1, df_m15, current_hour)

            # メタ情報追加
            signal['timestamp'] = datetime.now().isoformat()
            signal['data_info'] = {
                'h1_bars': len(df_h1),
                'm15_bars': len(df_m15),
                'latest_h1': df_h1.index[-1].isoformat() if not df_h1.empty else None,
                'latest_m15': df_m15.index[-1].isoformat() if not df_m15.empty else None
            }

            return Response(signal, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"TFQE シグナル取得エラー: {e}", exc_info=True)
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
