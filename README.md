# KINMAQ Story Generator

ストーリー画像（ご新規様空き状況）を生成するシンプルなWebアプリです。

## 院ごとの設定

`config.json` の `clinic_name` を院名に変更するだけです。

```json
{
  "clinic_name": "○○院",
  "brand": "KINMAQ",
  "brand_sub": "Next整体",
  "port": 5100
}
```

複数院で同時に使う場合は `port` の番号を院ごとに変えてください。
（例: 5100, 5101, 5102 …）

## セットアップ（初回のみ）

```bash
pip3 install flask playwright
playwright install chromium
```

## 起動

```bash
python3 app.py
```

ブラウザで開く：
- **このPC** → http://localhost:5100
- **スマホ（同じWi-Fi）** → http://[IPアドレス]:5100

IPアドレスは起動時にターミナルに表示されます。
