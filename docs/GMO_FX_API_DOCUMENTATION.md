# GMO Coin FX API Documentation

## 概要
GMOコインのAPIは、認証不要のPublic APIと、APIキーによる認証が必要なPrivate APIを提供しています。
クライアントからAPIへの全てのリクエストはHTTPS通信です。

**Python 3.12.0 にて動作確認したサンプルコードをRequest exampleに記載しています。**

---

## エンドポイント

- **Public API**: `https://forex-api.coin.z.com/public`
- **Public WebSocket API**: `wss://forex-api.coin.z.com/ws/public`
- **Private API**: `https://forex-api.coin.z.com/private`
- **Private WebSocket API**: `wss://forex-api.coin.z.com/ws/private`

### バージョン
現在バージョン: **v1**

---

## 制限

### Public WebSocket APIの制限
- 同一IPからのリクエスト(subscribe, unsubscribe)は、1秒間1回を上限とします。

### Private APIの制限
- 制限はシステム負荷状況によって一時的に変更する場合があります。
- 会員ページにてIP制限機能を有効にすると、API呼出ができるIPアドレスを制限することができます。
- APIキー発行時に指定した機能のみをAPIで呼び出すことができます。
- 同一アカウントからGETのAPI呼出は、1秒間に6回が上限です。
- 同一アカウントからPOSTのAPI呼出は、1秒間に1回が上限です。

### Private WebSocket APIの制限
- 同一IPからのリクエスト(subscribe, unsubscribe)は、1秒間1回を上限とします。
- 会員ページにてIP制限機能を有効にすると、API呼出ができるIPアドレスを制限することができます。
- APIキー発行時に指定した機能のみをsubscribeすることができます。

### その他
下記のいずれかの理由により、APIのご利用を制限させていただく場合があります。
- 当社システム全体が高負荷となった場合に、自動で流量制限を実施させていただくため
- お客さまによるAPIのご利用方法が、当社システムへ負荷をかけている可能性があると当社が判断したため
- システムに負荷をかける目的での発注を繰り返していると当社が判断したため

---

## 口座開設・APIキー作成

### 口座開設
外国為替FX口座をお持ちでない場合、無料口座開設が必要です。

### APIキー作成
外国為替FX口座の開設完了後、会員ページから外国為替FXのAPIキーが作成できます。
- APIキーを生成する際、機能ごとにパーミッションを設定することができます。
- APIキー作成後はトライアル期間として30日間API手数料無料でご利用いただけます。

---

## 認証

### Public API
認証は不要です。

### Private API

Private APIではAPIキーとAPIシークレットを使用してHTTPヘッダに下記の認証情報を含める必要があります。

- **API-KEY**: 会員ページで発行したアクセスキー
- **API-TIMESTAMP**: リクエスト時のUnix Timestamp（ミリ秒）
- **API-SIGN**: 署名（後述する方法でリクエストごとに生成）

#### 署名の生成

署名は、リクエスト時のUnix Timestamp（ミリ秒）、HTTPメソッド、リクエストのパス、リクエストボディを文字列として連結したものを、APIシークレットキーを使ってHMAC-SHA256形式で署名することで作成できます。

**注意点:**
- GETリクエストの場合、リクエストボディは空文字列とすること
- リクエストのパスは`/v1`で始まり、`/private`で始まらないこと

#### サンプルコード

```python
import requests
import json
import hmac
import hashlib
import time
from datetime import datetime

apiKey    = 'YOUR_API_KEY'
secretKey = 'YOUR_SECRET_KEY'

timestamp = '{0}000'.format(int(time.mktime(datetime.now().timetuple())))
method    = 'POST'
endPoint  = 'https://END_POINT_URL'
path      = '/v1/PATH'
reqBody   = {}

text = timestamp + method + path + json.dumps(reqBody)
sign = hmac.new(bytes(secretKey.encode('ascii')), bytes(text.encode('ascii')), hashlib.sha256).hexdigest()
parameters = {}

headers = {
    "API-KEY": apiKey,
    "API-TIMESTAMP": timestamp,
    "API-SIGN": sign
}

res = requests.get(endPoint + path, headers=headers, params=parameters)
print (res.json())
```

### Private WebSocket API

Private WebSocket APIではPrivate APIのアクセストークンの取得を使用してアクセストークンを取得します。このPrivate APIの認証方法は他のPrivate APIと同様です。

**接続方法:**
Private WebSocket APIのエンドポイント + アクセストークン
例: `wss://forex-api.coin.z.com/ws/private/v1/xxxxxxxxxxxxxxxxxxxx`

---

## Public API

### 外国為替FXステータス

外国為替FXの稼動状態を取得します。

**Request:**
```
GET /public/v1/status
```

**Parameters:** 無し

**Response:**
```json
{
  "status": 0,
  "data": {
    "status": "OPEN"
  },
  "responsetime": "2019-03-19T02:15:06.001Z"
}
```

| Property Name | Value  | Description                                        |
|---------------|--------|----------------------------------------------------|
| status        | string | 外国為替FXステータス: MAINTENANCE CLOSE OPEN         |

---

### 最新レート

全銘柄分の最新レートを取得します。

**Request:**
```
GET /public/v1/ticker
```

**Parameters:** 無し

**Response:**
```json
{
  "status": 0,
  "data": [
    {
      "ask": "137.644",
      "bid": "137.632",
      "symbol": "USD_JPY",
      "timestamp": "2018-03-30T12:34:56.789671Z",
      "status": "OPEN"
    },
    {
      "symbol": "EUR_JPY",
      "ask": "149.221",
      "bid": "149.181",
      "timestamp": "2023-05-19T02:51:24.516493Z",
      "status": "OPEN"
    }
  ],
  "responsetime": "2019-03-19T02:15:06.014Z"
}
```

| Property Name | Value  | Description                                |
|---------------|--------|--------------------------------------------|
| symbol        | string | 取扱銘柄                                    |
| ask           | string | 現在の買値                                  |
| bid           | string | 現在の売値                                  |
| timestamp     | string | 現在レートのタイムスタンプ                   |
| status        | string | 外国為替FXステータス: CLOSE OPEN             |

---

### KLine情報の取得

指定した銘柄の四本値を取得します。

**Request:**
```
GET /public/v1/klines
```

**Parameters:**

| Parameter  | Type   | Required | Available Values                                                                 |
|------------|--------|----------|----------------------------------------------------------------------------------|
| symbol     | string | Required | 取扱銘柄                                                                          |
| priceType  | string | Required | BID ASKを指定                                                                     |
| interval   | string | Required | 1min 5min 10min 15min 30min 1hour 4hour 8hour 12hour 1day 1week 1month          |
| date       | string | Required | YYYYMMDD YYYY                                                                    |

**Response:**
```json
{
  "status": 0,
  "data": [
    {
        "openTime":"1618588800000",
        "open":"141.365",
        "high":"141.368",
        "low":"141.360",
        "close":"141.362"
    },
    {
        "openTime":"1618588860000",
        "open":"141.362",
        "high":"141.369",
        "low":"141.361",
        "close":"141.365"
    }
  ],
  "responsetime": "2023-07-08T22:28:07.980Z"
}
```

| Property Name | Value  | Description                           |
|---------------|--------|---------------------------------------|
| openTime      | string | 開始時刻のunixタイムスタンプ(ミリ秒)    |
| open          | string | 始値                                  |
| high          | string | 高値                                  |
| low           | string | 安値                                  |
| close         | string | 終値                                  |

---

### 取引ルール

取引ルールを取得します。

**Request:**
```
GET /public/v1/symbols
```

**Parameters:** 無し

**Response:**
```json
{
  "status": 0,
  "data": [
    {
      "symbol": "USD_JPY",
      "minOpenOrderSize": "10000",
      "maxOrderSize": "500000",
      "sizeStep": "1",
      "tickSize": "0.001"
    }
  ],
  "responsetime": "2022-12-15T19:22:23.792Z"
}
```

| Property Name      | Value  | Description            |
|--------------------|--------|------------------------|
| symbol             | string | 取扱銘柄                |
| minOpenOrderSize   | string | 新規最小注文数量/回     |
| maxOrderSize       | string | 最大注文数量/回         |
| sizeStep           | string | 最小注文単位/回         |
| tickSize           | string | 注文価格の呼値          |

---

## Public WebSocket API

サーバーから1分に1回クライアントへpingを送り、3回連続でクライアントからの応答(pong)が無かった場合は、自動的に切断されます。

### 最新レート

指定した銘柄の最新レートを受信します。
subscribe後、最新レートが配信されます。

**Parameters:**

| Property Name | Type   | Required | Available Values         |
|---------------|--------|----------|--------------------------|
| command       | string | Required | subscribe unsubscribe    |
| channel       | string | Required | ticker                   |
| symbol        | string | Required | 取扱銘柄                  |

**Response:**
```json
{
  "symbol": "USD_JPY",
  "ask": "140.534",
  "bid": "140.502",
  "timestamp": "2018-03-30T12:34:56.789984Z",
  "status": "OPEN"
}
```

| Property Name | Value  | Description                                |
|---------------|--------|--------------------------------------------|
| symbol        | string | 取扱銘柄                                    |
| ask           | string | 現在の買値                                  |
| bid           | string | 現在の売値                                  |
| timestamp     | string | 現在レートのタイムスタンプ                   |
| status        | string | 外国為替FXステータス: CLOSE OPEN             |

**注意:** unsubscribeでリクエストした場合のResponseはありません。

---

## Private API

### 資産残高を取得

資産残高を取得します。

**Request:**
```
GET /private/v1/account/assets
```

**Parameters:** 無し

**Response:**
```json
{
  "status": 0,
  "data": [
    {
      "equity": "120947776",
      "availableAmount": "89717102",
      "balance": "116884885",
      "estimatedTradeFee": "766.5",
      "margin": "31227908",
      "marginRatio": "406.3",
      "positionLossGain": "3884065.046",
      "totalSwap": "178825.439",
      "transferableAmount": "85654212"
    }
  ],
  "responsetime": "2019-03-19T02:15:06.055Z"
}
```

| Property Name        | Value  | Description      |
|----------------------|--------|------------------|
| equity               | string | 時価評価総額      |
| availableAmount      | string | 取引余力          |
| balance              | string | 現金残高          |
| estimatedTradeFee    | string | 見込み手数料      |
| margin               | string | 拘束証拠金        |
| marginRatio          | string | 証拠金維持率      |
| positionLossGain     | string | 評価損益          |
| totalSwap            | string | 未決済スワップ    |
| transferableAmount   | string | 振替余力          |

---

### 注文情報取得

指定した注文IDの注文情報を取得します。
rootOrderId、orderId いずれか1つが必須です。2つ同時には設定できません。

**Request:**
```
GET /private/v1/orders
```

**Parameters:**

| Parameter    | Type   | Required | Available Values                              |
|--------------|--------|----------|-----------------------------------------------|
| rootOrderId  | number | *        | rootOrderId orderId いずれか1つが必須           |
| orderId      | number | *        | rootOrderId orderId いずれか1つが必須           |

※カンマ区切りで最大10件まで指定可能

**Response:**
```json
{
  "status": 0,
  "data": {
    "list": [
      {
        "rootOrderId": 223456789,
        "clientOrderId": "sygngz1234",
        "orderId": 223456789,
        "symbol": "USD_JPY",
        "side": "BUY",
        "orderType": "NORMAL",
        "executionType": "LIMIT",
        "settleType": "OPEN",
        "size": "10000",
        "price": "140",
        "status": "EXECUTED",
        "expiry" : "20201113",
        "timestamp": "2020-10-14T20:18:59.343Z"
      }
    ]
  },
  "responsetime": "2019-03-19T02:15:06.059Z"
}
```

---

### 有効注文一覧

有効注文一覧を取得します。

**Request:**
```
GET /private/v1/activeOrders
```

**Parameters:**

| Parameter | Type   | Required | Available Values                           |
|-----------|--------|----------|--------------------------------------------|
| symbol    | string | Optional | 取扱銘柄                                    |
| prevId    | number | Optional | 注文IDを指定                                |
| count     | number | Optional | 取得件数: 指定しない場合は100(最大値)       |

---

### 約定情報取得

約定情報を取得します。
orderId、executionId いずれか1つが必須です。2つ同時には設定できません。

**Request:**
```
GET /private/v1/executions
```

**Parameters:**

| Parameter    | Type   | Required | Available Values                                |
|--------------|--------|----------|-------------------------------------------------|
| orderId      | number | *        | orderId executionId いずれか1つが必須            |
| executionId  | string | *        | orderId executionId いずれか1つが必須            |

※executionIdのみカンマ区切りで最大10件まで指定可能

---

### 最新の約定一覧

最新約定一覧を取得します。
直近1日分から最新100件の約定情報を返します。

**Request:**
```
GET /private/v1/latestExecutions
```

**Parameters:**

| Parameter | Type   | Required | Available Values                      |
|-----------|--------|----------|---------------------------------------|
| symbol    | string | Required | 取扱銘柄                               |
| count     | number | Optional | 取得件数: 指定しない場合は100(最大値)  |

---

### 建玉一覧を取得

有効建玉一覧を取得します。

**Request:**
```
GET /private/v1/openPositions
```

**Parameters:**

| Parameter | Type   | Required | Available Values                           |
|-----------|--------|----------|--------------------------------------------|
| symbol    | string | Optional | 取扱銘柄                                    |
| prevId    | number | Optional | 建玉IDを指定                                |
| count     | number | Optional | 取得件数: 指定しない場合は100(最大値)       |

---

### 建玉サマリーを取得

建玉サマリーを取得します。
指定した銘柄の建玉サマリーを売買区分(買/売)ごとに取得できます。
symbolパラメータ指定無しの場合は、保有している全銘柄の建玉サマリーを売買区分(買/売)ごとに取得します。

**Request:**
```
GET /private/v1/positionSummary
```

**Parameters:**

| Parameter | Type   | Required | Available Values                                    |
|-----------|--------|----------|-----------------------------------------------------|
| symbol    | string | Optional | 指定しない場合は全銘柄分の建玉サマリーを返却         |

---

### スピード注文

スピード注文をします。

**Request:**
```
POST /private/v1/speedOrder
```

**Parameters:**

| Parameter     | Type   | Required | Available Values                                        |
|---------------|--------|----------|---------------------------------------------------------|
| symbol        | string | Required | 取扱銘柄                                                 |
| side          | string | Required | BUY SELL                                                |
| clientOrderId | string | Optional | 顧客注文ID ※36文字以内の半角英数字の組合わせのみ使用可能 |
| size          | string | Required | 注文数量                                                 |
| lowerBound    | string | Optional | 成立下限価格 ※side:SELLの場合に指定可能                  |
| upperBound    | string | Optional | 成立上限価格 ※side:BUYの場合に指定可能                   |
| isHedgeable   | bool   | Optional | 両建てなし: false(デフォルト) 両建てあり:true             |

---

### 注文

新規注文をします。

**Request:**
```
POST /private/v1/order
```

**Parameters:**

| Parameter     | Type   | Required             | Available Values                                        |
|---------------|--------|----------------------|---------------------------------------------------------|
| symbol        | string | Required             | 取扱銘柄                                                 |
| side          | string | Required             | BUY SELL                                                |
| size          | string | Required             | 注文数量                                                 |
| clientOrderId | string | Optional             | 顧客注文ID ※36文字以内の半角英数字の組合わせのみ使用可能 |
| executionType | string | Required             | MARKET LIMIT STOP OCO                                   |
| limitPrice    | string | *executionTypeによる | 指値注文レート ※LIMIT OCO の場合は必須                   |
| stopPrice     | string | *executionTypeによる | 逆指値注文レート ※STOP OCO の場合は必須                  |
| lowerBound    | string | Optional             | 成立下限価格                                             |
| upperBound    | string | Optional             | 成立上限価格                                             |

---

### IFD注文

IFD注文をします。

**Request:**
```
POST /private/v1/ifdOrder
```

**Parameters:**

| Parameter          | Type   | Required | Available Values                                        |
|--------------------|--------|----------|---------------------------------------------------------|
| symbol             | string | Required | 取扱銘柄                                                 |
| clientOrderId      | string | Optional | 顧客注文ID ※36文字以内の半角英数字の組合わせのみ使用可能 |
| firstSide          | string | Required | BUY SELL                                                |
| firstExecutionType | string | Required | LIMIT STOP                                              |
| firstSize          | string | Required | 1次注文数量                                              |
| firstPrice         | string | Required | 1次注文レート                                            |
| secondExecutionType| string | Required | LIMIT STOP                                              |
| secondSize         | string | Required | 2次注文数量                                              |
| secondPrice        | string | Required | 2次注文レート                                            |

---

### IFDOCO注文

IFDOCO注文をします。

**Request:**
```
POST /private/v1/ifoOrder
```

**Parameters:**

| Parameter          | Type   | Required | Available Values                                        |
|--------------------|--------|----------|---------------------------------------------------------|
| symbol             | string | Required | 取扱銘柄                                                 |
| clientOrderId      | string | Optional | 顧客注文ID ※36文字以内の半角英数字の組合わせのみ使用可能 |
| firstSide          | string | Required | BUY SELL                                                |
| firstExecutionType | string | Required | LIMIT STOP                                              |
| firstSize          | string | Required | 1次注文数量                                              |
| firstPrice         | string | Required | 1次注文レート                                            |
| secondSize         | string | Required | 2次注文数量                                              |
| secondLimitPrice   | string | Required | 2次指値注文レート                                        |
| secondStopPrice    | string | Required | 2次逆指値注文レート                                      |

---

### 注文変更

注文変更をします。
orderId、clientOrderIdいずれか1つが必須です。2つ同時には設定できません。

**Request:**
```
POST /private/v1/changeOrder
```

**Parameters:**

| Parameter     | Type   | Required | Available Values                                            |
|---------------|--------|----------|-------------------------------------------------------------|
| orderId       | number | *        | orderId clientOrderId いずれか1つが必須                      |
| clientOrderId | string | *        | orderId clientOrderId いずれか1つが必須                      |
| price         | string | Required | 注文レート                                                   |

---

### OCO注文変更

OCO注文変更をします。
rootOrderId、clientOrderIdいずれか1つが必須です。2つ同時には設定できません。
limitPrice、stopPrice 両方もしくはどちらか1つが必須です。

**Request:**
```
POST /private/v1/changeOcoOrder
```

**Parameters:**

| Parameter     | Type   | Required | Available Values                                                       |
|---------------|--------|----------|------------------------------------------------------------------------|
| rootOrderId   | number | *        | rootOrderId clientOrderId いずれか1つが必須                             |
| clientOrderId | string | *        | rootOrderId clientOrderId いずれか1つが必須                             |
| limitPrice    | string | *        | 指値注文レート ※ limitPrice stopPrice 両方もしくはどちらか1つ必須       |
| stopPrice     | string | *        | 逆指値注文レート ※ limitPrice stopPrice 両方もしくはどちらか1つ必須     |

---

### IFD注文変更

IFD注文変更をします。
rootOrderId、clientOrderIdいずれか1つが必須です。2つ同時には設定できません。
firstPrice、secondPrice 両方もしくはどちらか1つが必須です。

**Request:**
```
POST /private/v1/changeIfdOrder
```

**Parameters:**

| Parameter     | Type   | Required | Available Values                                                         |
|---------------|--------|----------|--------------------------------------------------------------------------|
| rootOrderId   | number | *        | rootOrderId clientOrderId いずれか1つが必須                               |
| clientOrderId | string | *        | rootOrderId clientOrderId いずれか1つが必須                               |
| firstPrice    | string | *        | 1次注文レート ※ firstPrice secondPrice 両方もしくはどちらか1つ必須        |
| secondPrice   | string | *        | 2次注文レート ※ firstPrice secondPrice 両方もしくはどちらか1つ必須        |

---

### IFDOCO注文変更

IFDOCO注文変更をします。
rootOrderId、clientOrderIdいずれか1つが必須です。2つ同時には設定できません。
firstPrice、secondLimitPrice、secondStopPrice の内全てもしくはいずれか1つ以上が必須です。

**Request:**
```
POST /private/v1/changeIfoOrder
```

**Parameters:**

| Parameter        | Type   | Required | Available Values                                                                          |
|------------------|--------|----------|-------------------------------------------------------------------------------------------|
| rootOrderId      | number | *        | rootOrderId clientOrderId いずれか1つが必須                                                |
| clientOrderId    | string | *        | rootOrderId clientOrderId いずれか1つが必須                                                |
| firstPrice       | string | *        | 1次注文レート ※ firstPrice secondLimitPrice secondStopPrice の内全てもしくはいずれか1つ以上必須 |
| secondLimitPrice | string | *        | 2次指値注文レート ※ firstPrice secondLimitPrice secondStopPrice の内全てもしくはいずれか1つ以上必須 |
| secondStopPrice  | string | *        | 2次逆指値注文レート ※ firstPrice secondLimitPrice secondStopPrice の内全てもしくはいずれか1つ以上必須 |

---

### 注文の複数キャンセル

複数の注文を取消します。
rootOrderIds、clientOrderIdsいずれか1つが必須です。2つ同時には設定できません。
最大10件まで注文を取消することができます。

**Request:**
```
POST /private/v1/cancelOrders
```

**Parameters:**

| Parameter      | Type  | Required | Available Values                                                   |
|----------------|-------|----------|---------------------------------------------------------------------|
| rootOrderIds   | array | *        | rootOrderIds clientOrderIds いずれか1つが必須 ※最大10件まで指定可能 |
| clientOrderIds | array | *        | rootOrderIds clientOrderIds いずれか1つが必須 ※最大10件まで指定可能 |

---

### 注文の一括キャンセル

一括で注文(通常注文、特殊注文いずれも)を取消します。

**Request:**
```
POST /private/v1/cancelBulkOrder
```

**Parameters:**

| Parameter  | Type   | Required | Available Values                                         |
|------------|--------|----------|----------------------------------------------------------|
| symbols    | array  | Required | 取扱銘柄                                                  |
| side       | string | Optional | BUY SELL ※指定時のみ指定された売買区分の注文を取消条件に追加 |
| settleType | string | Optional | OPEN CLOSE ※指定時のみ指定された決済区分の注文を取消条件に追加 |

---

### 決済注文

決済注文をします。
size、settlePositionいずれか1つが必須です。2つ同時には設定できません。

**Request:**
```
POST /private/v1/closeOrder
```

**Parameters:**

| Parameter              | Type   | Required             | Available Values                                        |
|------------------------|--------|----------------------|---------------------------------------------------------|
| symbol                 | string | Required             | 取扱銘柄                                                 |
| side                   | string | Required             | BUY SELL                                                |
| executionType          | string | Required             | MARKET LIMIT STOP OCO                                   |
| clientOrderId          | string | Optional             | 顧客注文ID ※36文字以内の半角英数字の組合わせのみ使用可能 |
| size                   | string | *                    | 注文数量 建玉指定なし ※size settlePositionいずれかのみ指定可能 |
| limitPrice             | string | *executionTypeによる | 注文レート ※LIMIT OCO の場合は必須                       |
| stopPrice              | string | *executionTypeによる | 注文レート ※STOP OCO の場合は必須                        |
| lowerBound             | string | Optional             | 成立下限価格                                             |
| upperBound             | string | Optional             | 成立下限価格                                             |
| settlePosition         | array  | *                    | 複数建玉 ※最大10件まで指定可能                            |
| settlePosition.positionId | number | *                | 建玉ID                                                   |
| settlePosition.size    | string | *                    | 注文数量                                                 |

---

## Private WebSocket API

サーバーから1分に1回クライアントへpingを送り、3回連続でクライアントからの応答(pong)が無かった場合は、自動的に切断されます。

### アクセストークンを取得・延長・削除するために専用のPrivate APIを使用します。

#### アクセストークンを取得

Private WebSocket API用のアクセストークンを取得します。

- 有効期限は60分です。
- アクセストークンは最大5個まで発行できます。
- 発行上限を超えた場合、有効期限の近いトークンから順に削除されます。

**Request:**
```
POST /private/v1/ws-auth
```

**Parameters:** 無し

**Response:**
```json
{
  "status": 0,
  "data": "xxxxxxxxxxxxxxxxxxxx",
  "responsetime": "2019-03-19T02:15:06.102Z"
}
```

---

#### アクセストークンを延長

Private WebSocket API用のアクセストークンを延長します。
延長前の残り有効期限に関わらず、新しい有効期限は60分となります。

**Request:**
```
PUT /private/v1/ws-auth
```

**Parameters:**

| Parameter | Type   | Required | Available Values  |
|-----------|--------|----------|-------------------|
| token     | string | Required | アクセストークン   |

---

#### アクセストークンを削除

Private WebSocket API用のアクセストークンを削除します。

**Request:**
```
DELETE /private/v1/ws-auth
```

**Parameters:**

| Parameter | Type   | Required | Available Values  |
|-----------|--------|----------|-------------------|
| token     | string | Required | アクセストークン   |

---

### 約定情報通知

最新の約定情報通知を受信します。
subscribe後、最新の約定情報通知が配信されます。

**Parameters:**

| Property Name | Type   | Required | Available Values         |
|---------------|--------|----------|--------------------------|
| command       | string | Required | subscribe unsubscribe    |
| channel       | string | Required | executionEvents          |

**注意:** unsubscribeでリクエストした場合のResponseはありません。

---

### 注文情報通知

最新の注文情報通知を受信します。
subscribe後、最新の注文情報通知が配信されます。

**Parameters:**

| Property Name | Type   | Required | Available Values         |
|---------------|--------|----------|--------------------------|
| command       | string | Required | subscribe unsubscribe    |
| channel       | string | Required | orderEvents              |

**注意:** unsubscribeでリクエストした場合のResponseはありません。

---

### ポジション情報通知

最新のポジション情報通知を受信します。
subscribe後、最新のポジション情報通知が配信されます。

**Parameters:**

| Property Name | Type   | Required | Available Values         |
|---------------|--------|----------|--------------------------|
| command       | string | Required | subscribe unsubscribe    |
| channel       | string | Required | positionEvents           |

**注意:** unsubscribeでリクエストした場合のResponseはありません。

---

### ポジションサマリー情報通知

最新のポジションサマリー情報通知を受信します。
subscribe後、最新のポジションサマリー情報通知が配信されます。

**Parameters:**

| Property Name | Type   | Required | Available Values                                            |
|---------------|--------|----------|-------------------------------------------------------------|
| command       | string | Required | subscribe unsubscribe                                       |
| channel       | string | Required | positionSummaryEvents                                       |
| option        | string | Optional | PERIODIC ※optionが指定された場合、5秒ごとにデータが送信されます |

**注意:** unsubscribeでリクエストした場合のResponseはありません。

---

## リファレンス

### パラメータ

#### symbol: 取扱銘柄名

| Value    | Description           | Release date |
|----------|-----------------------|--------------|
| USD_JPY  | 米ドル/日本円          | 2023/04/26   |
| EUR_JPY  | ユーロ/日本円          | 2023/04/26   |
| GBP_JPY  | 英ポンド/日本円        | 2023/04/26   |
| AUD_JPY  | 豪ドル/日本円          | 2023/04/26   |
| NZD_JPY  | NZドル/日本円          | 2023/04/26   |
| CAD_JPY  | カナダドル/日本円      | 2023/04/26   |
| CHF_JPY  | スイスフラン/日本円    | 2023/04/26   |
| TRY_JPY  | トルコリラ/日本円      | 2023/08/05   |
| ZAR_JPY  | 南アフリカランド/日本円 | 2023/08/05   |
| MXN_JPY  | メキシコペソ/日本円    | 2023/08/05   |
| EUR_USD  | ユーロ/米ドル          | 2023/04/26   |
| GBP_USD  | 英ポンド/米ドル        | 2023/04/26   |
| AUD_USD  | 豪ドル/米ドル          | 2023/04/26   |
| NZD_USD  | NZドル/米ドル          | 2023/04/26   |

#### side: 売買区分

| Value | Description |
|-------|-------------|
| BUY   | 買           |
| SELL  | 売           |

#### executionType: 注文タイプ

| Value  | Description |
|--------|-------------|
| MARKET | 成行         |
| LIMIT  | 指値         |
| STOP   | 逆指値       |

---

### HTTPステータスコード

| Status Code | Description                                                    |
|-------------|----------------------------------------------------------------|
| 200         | 処理が正常終了した場合に返ってくるコードです。                  |
| 404         | URLが不正な場合などに返ってくるコードです。                     |
| 503         | メンテナンス時にWebSocket APIを呼び出した場合に返ってくるコードです。 |

---

### ステータスコード

| Status Code | Description                                |
|-------------|--------------------------------------------|
| 0           | 処理が正常終了した場合に返ってくるコードです。 |

---

### エラーコード

| Error Code | Description                                                                                                                                             |
|------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|
| ERR-143    | 規制中のため取引できない場合に返ってきます。                                                                                                             |
| ERR-148    | IFD、IFDOCO注文において新規注文数量より決済注文数量が多い場合に返ってきます。                                                                            |
| ERR-189    | 決済注文において、決済可能保有数量を超えての数量の注文の場合に返ってきます。                                                                             |
| ERR-200    | すでに有効注文があり、注文数量が発注可能な数量を超えている場合に返ってきます。                                                                           |
| ERR-201    | 注文時に取引余力が不足している場合に返ってきます。                                                                                                       |
| ERR-254    | 指定された建玉が存在しない場合に返ってきます。                                                                                                           |
| ERR-414    | 決済注文において指定した銘柄と指定した建玉IDの銘柄が異なっている場合に返ってきます。                                                                     |
| ERR-423    | 決済注文において注文数量が総建玉数量よりも大きい場合、もしくは総有効注文数量との合計が総建玉数量よりも大きい場合に返ってきます。                         |
| ERR-512    | 決済注文において同じ建玉IDを2つ以上指定した場合に返ってきます。                                                                                         |
| ERR-542    | OCO注文変更においてOCO注文以外の親注文IDや顧客注文IDを指定した場合に返ってきます。                                                                       |
| ERR-595    | IFD、IFDOCO注文変更においてIFD、IFDOCO注文以外の親注文IDや顧客注文IDを指定した場合に返ってきます。                                                       |
| ERR-635    | 有効注文の件数が上限に達している場合に返ってきます。                                                                                                     |
| ERR-759    | 建玉の件数が上限に達している場合に新規注文を行うと返ってきます。                                                                                         |
| ERR-760    | 注文変更において変更前と後で注文レートが同じ場合に返ってきます。                                                                                         |
| ERR-761    | 指定可能な注文レートの範囲を超えた場合に返ってきます。                                                                                                   |
| ERR-769    | 注文変更において変更元となる注文の有効期限が切れている場合に返ってきます。                                                                               |
| ERR-786    | 設定した顧客注文IDがご自身の他の有効注文に使用されている場合に返ってきます。                                                                             |
| ERR-5003   | API呼出上限を越えた場合に返ってきます。                                                                                                                  |
| ERR-5008   | リクエストヘッダーに設定されているAPI-TIMESTAMPが公開APIのシステム時刻より遅い場合に返ってきます。                                                       |
| ERR-5009   | リクエストヘッダーに設定されているAPI-TIMESTAMPが公開APIのシステム時刻より早い場合に返ってきます。                                                       |
| ERR-5010   | リクエストヘッダーに指定されているAPI-SIGN（Signature）に不正がある場合に返ってきます。                                                                  |
| ERR-5011   | リクエストヘッダーにAPI-KEYが設定されていない場合に返ってきます。                                                                                        |
| ERR-5012   | API-KEYが認証エラーの場合などに返ってきます。                                                                                                            |
| ERR-5014   | お客様のご確認、ご同意が必要な処理を実行する際に、お客様に未確認・未同意事項がある場合に返ってきます。                                                   |
| ERR-5106   | パラメーターが不正な場合に返ってきます。                                                                                                                 |
| ERR-5114   | 注文レートが呼値の単位を超えている場合に返ってきます。                                                                                                   |
| ERR-5122   | 指定された注文がすでに変更中、取消中、取消済、全量約定、失効のいずれかの状態であるため、注文の変更や取消ができない場合に返ってきます。                   |
| ERR-5123   | 指定された注文番号が存在しない場合に返ってきます。                                                                                                       |
| ERR-5125   | APIの取引規制がかかっている場合に返ってきます。                                                                                                          |
| ERR-5126   | 1回あたりの最大注文数量を超えている場合または最小注文数量を下回っている場合、または最大建玉数量を超過する場合に返ってきます。                             |
| ERR-5130   | 注文情報取得もしくは約定情報取得において指定した注文IDもしくは親注文IDが最大指定数量を超えている場合に返ってきます。                                       |
| ERR-5132   | 約定情報取得において指定した約定IDが最大指定数量を超えている場合に返ってきます。                                                                         |
| ERR-5201   | 定期メンテナンス時にPublic/Private APIを呼び出した場合に返ってきます。                                                                                   |
| ERR-5202   | 緊急メンテナンス時にPublic/Private APIを呼び出した場合に返ってきます。                                                                                   |
| ERR-5204   | リクエスト時に各APIのURLが不正な場合に返ってきます。                                                                                                     |
| ERR-5206   | 注文変更を実行時に注文毎の変更可能回数が上限に達している場合に返ってきます。                                                                             |
| ERR-5207   | リクエストボディに指定されているsymbol、intervalまたはdateが不正な場合に返ってきます。                                                                   |
| ERR-5208   | 約定情報取得において、orderId/executionIdが両方設定された場合に返ってきます。                                                                            |
| ERR-5209   | 注文情報取得において、orderId/rootOrderIdが両方設定された場合に返ってきます。                                                                            |
| ERR-5210   | 注文タイプと limitPrice/stopPriceが一致していない場合に返ってきます。                                                                                    |
| ERR-5211   | 売買区分と一致しない lowerBound/upperBound を指定した場合に返ってきます。                                                                                |
| ERR-5213   | 注文IDもしくは親注文IDと顧客注文IDどちらか一方を指定する箇所でどちらも指定している場合に返ってきます。                                                   |
| ERR-5214   | 決済注文において、建玉IDを指定している場合に注文数量を指定すると返ってきます。                                                                           |
| ERR-5218   | 取引時間外のため注文が行えない場合に返ってきます。                                                                                                       |
| ERR-5219   | 注文変更において通常注文以外の注文IDや顧客注文IDを指定した場合に返ってきます。                                                                           |
| ERR-5220~5229 | IFD/IFDOCO/OCO注文のレート設定が不適切な場合に返ってきます。                                                                                          |

---

**ドキュメント作成日**: 2025-09-30
**対応言語**: Python 3.12.0
**API Version**: v1