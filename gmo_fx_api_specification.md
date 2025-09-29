# GMOコイン外国為替FX API仕様書

## 概要

GMOコインのAPIは、認証不要のPublic APIと、APIキーによる認証が必要なPrivate APIを提供しています。

### 対応環境
- Python 3.12.0にて動作確認済み
- 全リクエストはHTTPS通信

## エンドポイント

### Public API
- REST API: `https://forex-api.coin.z.com/public`
- WebSocket API: `wss://forex-api.coin.z.com/ws/public`

### Private API
- REST API: `https://forex-api.coin.z.com/private`
- WebSocket API: `wss://forex-api.coin.z.com/ws/private`

### バージョン
現在バージョン: v1

## 制限

### Public WebSocket APIの制限
- 同一IPからのリクエスト(subscribe, unsubscribe)は、1秒間1回が上限

### Private APIの制限
- 同一アカウントからGETのAPI呼出は、1秒間に6回が上限
- 同一アカウントからPOSTのAPI呼出は、1秒間に1回が上限
- APIキー発行時に指定した機能のみをAPIで呼び出すことが可能
- IP制限機能を有効にすると、API呼出ができるIPアドレスを制限可能

### Private WebSocket APIの制限
- 同一IPからのリクエスト(subscribe, unsubscribe)は、1秒間1回が上限
- IP制限機能を有効にすると、API呼出ができるIPアドレスを制限可能
- APIキー発行時に指定した機能のみをsubscribe可能

## 認証

### Private API認証方法

HTTPヘッダに下記の認証情報を含める必要があります：

- **API-KEY**: 会員ページで発行したアクセスキー
- **API-TIMESTAMP**: リクエスト時のUnix Timestamp（ミリ秒）
- **API-SIGN**: HMAC-SHA256形式で生成した署名

#### 署名の生成方法

```python
import hmac
import hashlib
import json

# 署名の生成
timestamp = '{0}000'.format(int(time.mktime(datetime.now().timetuple())))
text = timestamp + method + path + json.dumps(reqBody)
sign = hmac.new(bytes(secretKey.encode('ascii')),
                bytes(text.encode('ascii')),
                hashlib.sha256).hexdigest()
```

注意事項：
- GETリクエストの場合、リクエストボディは空文字列とする
- リクエストのパスは/v1で始まり、/privateで始まらない

## Public API一覧

### 1. 外国為替FXステータス
```
GET /public/v1/status
```
**レスポンス:**
- `status`: MAINTENANCE | CLOSE | OPEN

### 2. 最新レート
```
GET /public/v1/ticker
```
**レスポンス:**
- `symbol`: 取扱銘柄
- `ask`: 現在の買値
- `bid`: 現在の売値
- `timestamp`: 現在レートのタイムスタンプ
- `status`: CLOSE | OPEN

### 3. KLine情報の取得
```
GET /public/v1/klines
```
**パラメータ:**
- `symbol`: 取扱銘柄（必須）
- `priceType`: BID | ASK（必須）
- `interval`: 1min | 5min | 10min | 15min | 30min | 1hour | 4hour | 8hour | 12hour | 1day | 1week | 1month（必須）
- `date`: YYYYMMDD | YYYY形式（必須）

### 4. 取引ルール
```
GET /public/v1/symbols
```
**レスポンス:**
- `symbol`: 取扱銘柄
- `minOpenOrderSize`: 新規最小注文数量/回
- `maxOrderSize`: 最大注文数量/回
- `sizeStep`: 最小注文単位/回
- `tickSize`: 注文価格の呼値

## Private API一覧

### アカウント関連

#### 資産残高を取得
```
GET /private/v1/account/assets
```
**レスポンス:**
- `equity`: 時価評価総額
- `availableAmount`: 取引余力
- `balance`: 現金残高
- `estimatedTradeFee`: 見込み手数料
- `margin`: 拘束証拠金
- `marginRatio`: 証拠金維持率
- `positionLossGain`: 評価損益
- `totalSwap`: 未決済スワップ
- `transferableAmount`: 振替余力

### 注文関連

#### 注文情報取得
```
GET /private/v1/orders
```
**パラメータ:**
- `rootOrderId`: 親注文ID（※orderIdと排他）
- `orderId`: 注文ID（※rootOrderIdと排他）
※カンマ区切りで最大10件まで指定可能

#### 有効注文一覧
```
GET /private/v1/activeOrders
```
**パラメータ:**
- `symbol`: 取扱銘柄（任意）
- `prevId`: 注文ID（任意）
- `count`: 取得件数（任意、デフォルト100）

#### スピード注文
```
POST /private/v1/speedOrder
```
**パラメータ:**
- `symbol`: 取扱銘柄（必須）
- `side`: BUY | SELL（必須）
- `size`: 注文数量（必須）
- `clientOrderId`: 顧客注文ID（任意）
- `lowerBound`: 成立下限価格（任意、SELL時のみ）
- `upperBound`: 成立上限価格（任意、BUY時のみ）
- `isHedgeable`: 両建て設定（任意、デフォルトfalse）

#### 通常注文
```
POST /private/v1/order
```
**パラメータ:**
- `symbol`: 取扱銘柄（必須）
- `side`: BUY | SELL（必須）
- `size`: 注文数量（必須）
- `executionType`: MARKET | LIMIT | STOP | OCO（必須）
- `limitPrice`: 指値注文レート（LIMIT、OCOの場合必須）
- `stopPrice`: 逆指値注文レート（STOP、OCOの場合必須）
- `clientOrderId`: 顧客注文ID（任意）

#### IFD注文
```
POST /private/v1/ifdOrder
```
**パラメータ:**
- `symbol`: 取扱銘柄（必須）
- `firstSide`: BUY | SELL（必須）
- `firstExecutionType`: LIMIT | STOP（必須）
- `firstSize`: 1次注文数量（必須）
- `firstPrice`: 1次注文レート（必須）
- `secondExecutionType`: LIMIT | STOP（必須）
- `secondSize`: 2次注文数量（必須）
- `secondPrice`: 2次注文レート（必須）
- `clientOrderId`: 顧客注文ID（任意）

#### IFDOCO注文
```
POST /private/v1/ifoOrder
```
**パラメータ:**
- `symbol`: 取扱銘柄（必須）
- `firstSide`: BUY | SELL（必須）
- `firstExecutionType`: LIMIT | STOP（必須）
- `firstSize`: 1次注文数量（必須）
- `firstPrice`: 1次注文レート（必須）
- `secondSize`: 2次注文数量（必須）
- `secondLimitPrice`: 2次指値注文レート（必須）
- `secondStopPrice`: 2次逆指値注文レート（必須）
- `clientOrderId`: 顧客注文ID（任意）

#### 決済注文
```
POST /private/v1/closeOrder
```
**パラメータ:**
- `symbol`: 取扱銘柄（必須）
- `side`: BUY | SELL（必須）
- `executionType`: MARKET | LIMIT | STOP | OCO（必須）
- `size`: 注文数量（※settlePositionと排他）
- `settlePosition`: 建玉指定配列（※sizeと排他、最大10件）
  - `positionId`: 建玉ID
  - `size`: 注文数量

### 注文変更

#### 通常注文変更
```
POST /private/v1/changeOrder
```
**パラメータ:**
- `orderId`: 注文ID（※clientOrderIdと排他）
- `clientOrderId`: 顧客注文ID（※orderIdと排他）
- `price`: 注文レート（必須）

#### OCO注文変更
```
POST /private/v1/changeOcoOrder
```
**パラメータ:**
- `rootOrderId`: 親注文ID（※clientOrderIdと排他）
- `clientOrderId`: 顧客注文ID（※rootOrderIdと排他）
- `limitPrice`: 指値注文レート（※stopPriceと併用可）
- `stopPrice`: 逆指値注文レート（※limitPriceと併用可）

#### IFD注文変更
```
POST /private/v1/changeIfdOrder
```
**パラメータ:**
- `rootOrderId`: 親注文ID（※clientOrderIdと排他）
- `clientOrderId`: 顧客注文ID（※rootOrderIdと排他）
- `firstPrice`: 1次注文レート（※secondPriceと併用可）
- `secondPrice`: 2次注文レート（※firstPriceと併用可）

#### IFDOCO注文変更
```
POST /private/v1/changeIfoOrder
```
**パラメータ:**
- `rootOrderId`: 親注文ID（※clientOrderIdと排他）
- `clientOrderId`: 顧客注文ID（※rootOrderIdと排他）
- `firstPrice`: 1次注文レート（任意）
- `secondLimitPrice`: 2次指値注文レート（任意）
- `secondStopPrice`: 2次逆指値注文レート（任意）

### 注文キャンセル

#### 複数注文キャンセル
```
POST /private/v1/cancelOrders
```
**パラメータ:**
- `rootOrderIds`: 親注文ID配列（※clientOrderIdsと排他、最大10件）
- `clientOrderIds`: 顧客注文ID配列（※rootOrderIdsと排他、最大10件）

#### 一括注文キャンセル
```
POST /private/v1/cancelBulkOrder
```
**パラメータ:**
- `symbols`: 取扱銘柄配列（必須）
- `side`: BUY | SELL（任意）
- `settleType`: OPEN | CLOSE（任意）

### 約定・建玉関連

#### 約定情報取得
```
GET /private/v1/executions
```
**パラメータ:**
- `orderId`: 注文ID（※executionIdと排他）
- `executionId`: 約定ID（※orderIdと排他、カンマ区切りで最大10件）

#### 最新の約定一覧
```
GET /private/v1/latestExecutions
```
**パラメータ:**
- `symbol`: 取扱銘柄（必須）
- `count`: 取得件数（任意、デフォルト100）

#### 建玉一覧を取得
```
GET /private/v1/openPositions
```
**パラメータ:**
- `symbol`: 取扱銘柄（任意）
- `prevId`: 建玉ID（任意）
- `count`: 取得件数（任意、デフォルト100）

#### 建玉サマリーを取得
```
GET /private/v1/positionSummary
```
**パラメータ:**
- `symbol`: 取扱銘柄（任意、指定しない場合は全銘柄）

## WebSocket API

### Public WebSocket API

#### 最新レート購読
```json
{
  "command": "subscribe",
  "channel": "ticker",
  "symbol": "USD_JPY"
}
```

### Private WebSocket API

#### アクセストークン管理
- 取得: `POST /private/v1/ws-auth`
- 延長: `PUT /private/v1/ws-auth`
- 削除: `DELETE /private/v1/ws-auth`

#### チャンネル購読
- `executionEvents`: 約定情報通知
- `orderEvents`: 注文情報通知
- `positionEvents`: ポジション情報通知
- `positionSummaryEvents`: ポジションサマリー情報通知

## 取扱銘柄一覧

| 銘柄コード | 説明 | リリース日 |
|------------|------|------------|
| USD_JPY | 米ドル/日本円 | 2023/04/26 |
| EUR_JPY | ユーロ/日本円 | 2023/04/26 |
| GBP_JPY | 英ポンド/日本円 | 2023/04/26 |
| AUD_JPY | 豪ドル/日本円 | 2023/04/26 |
| NZD_JPY | NZドル/日本円 | 2023/04/26 |
| CAD_JPY | カナダドル/日本円 | 2023/04/26 |
| CHF_JPY | スイスフラン/日本円 | 2023/04/26 |
| TRY_JPY | トルコリラ/日本円 | 2023/08/05 |
| ZAR_JPY | 南アフリカランド/日本円 | 2023/08/05 |
| MXN_JPY | メキシコペソ/日本円 | 2023/08/05 |
| EUR_USD | ユーロ/米ドル | 2023/04/26 |
| GBP_USD | 英ポンド/米ドル | 2023/04/26 |
| AUD_USD | 豪ドル/米ドル | 2023/04/26 |
| NZD_USD | NZドル/米ドル | 2023/04/26 |

## 主要なエラーコード

| エラーコード | 説明 |
|--------------|------|
| ERR-143 | 規制中のため取引できない |
| ERR-201 | 注文時に取引余力が不足 |
| ERR-254 | 指定された建玉が存在しない |
| ERR-635 | 有効注文の件数が上限に達している |
| ERR-759 | 建玉の件数が上限に達している |
| ERR-5003 | API呼出上限を超えた |
| ERR-5008 | API-TIMESTAMPが公開APIのシステム時刻より遅い |
| ERR-5009 | API-TIMESTAMPが公開APIのシステム時刻より早い |
| ERR-5010 | API-SIGN（Signature）に不正がある |
| ERR-5011 | API-KEYが設定されていない |
| ERR-5012 | API-KEYが認証エラー |
| ERR-5125 | APIの取引規制がかかっている |
| ERR-5126 | 注文数量が制限を超えている |
| ERR-5201 | 定期メンテナンス中 |
| ERR-5202 | 緊急メンテナンス中 |
| ERR-5218 | 取引時間外 |

## サンプルコード

### Private API認証の実装例

```python
import requests
import json
import hmac
import hashlib
import time
from datetime import datetime

class GMOFXClient:
    def __init__(self, api_key, secret_key):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = 'https://forex-api.coin.z.com/private'

    def _create_signature(self, method, path, body={}):
        """署名を生成"""
        timestamp = '{0}000'.format(int(time.mktime(datetime.now().timetuple())))
        text = timestamp + method + path + json.dumps(body)
        sign = hmac.new(
            bytes(self.secret_key.encode('ascii')),
            bytes(text.encode('ascii')),
            hashlib.sha256
        ).hexdigest()

        return {
            "API-KEY": self.api_key,
            "API-TIMESTAMP": timestamp,
            "API-SIGN": sign
        }

    def get_assets(self):
        """資産残高を取得"""
        path = '/v1/account/assets'
        headers = self._create_signature('GET', path)
        response = requests.get(self.base_url + path, headers=headers)
        return response.json()

    def create_order(self, symbol, side, size, execution_type, **kwargs):
        """新規注文"""
        path = '/v1/order'
        body = {
            "symbol": symbol,
            "side": side,
            "size": size,
            "executionType": execution_type
        }
        body.update(kwargs)

        headers = self._create_signature('POST', path, body)
        response = requests.post(
            self.base_url + path,
            headers=headers,
            data=json.dumps(body)
        )
        return response.json()
```

## 注意事項

1. **レート制限**
   - Private API: GET 6回/秒、POST 1回/秒
   - 制限を超えるとERR-5003エラーが返される

2. **認証**
   - API-TIMESTAMPはミリ秒単位のUnix Timestamp
   - 署名はHMAC-SHA256で生成
   - GETリクエストのボディは空文字列

3. **注文制約**
   - 最小注文単位、最大注文数量は銘柄ごとに異なる
   - 取引ルールAPIで確認が必要

4. **WebSocket接続**
   - 1分ごとにpingが送信される
   - 3回連続でpongがない場合は自動切断
   - アクセストークンの有効期限は60分

5. **価格精度**
   - 価格データは小数点5桁（0.00001）
   - 呼値（tickSize）は銘柄により異なる

## 更新履歴

- 2023-12-16: Python 3.12.0対応のサンプルコード更新
- 2023-10-28: バージョンv1リリース
- 2023-08-05: TRY_JPY、ZAR_JPY、MXN_JPY追加
- 2023-04-26: サービス開始