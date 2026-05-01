#!/usr/bin/env python3
"""
KINMAQ Story Generator
ストーリー画像（空き状況）を生成するシンプルなWebアプリ

起動方法:
  python3 app.py

ブラウザで開く:
  http://localhost:5100         （このPC）
  http://[このPCのIP]:5100      （同じWi-Fi内の他の端末）
"""

import json
import os
import threading
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template_string, request, send_file

# ──────────────────────────────────────────────
# 設定読み込み
# ──────────────────────────────────────────────

BASE = Path(__file__).parent
CONFIG_PATH = BASE / "config.json"
TEMPLATE_PATH = BASE / "template.html"
OUTPUT_DIR = BASE / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
CLINIC_NAME = config.get("clinic_name", "")
BRAND       = config.get("brand", "KINMAQ")
BRAND_SUB   = config.get("brand_sub", "Next整体")
PORT        = int(os.environ.get("PORT", config.get("port", 5100)))

WEEKDAY_JA = ["月", "火", "水", "木", "金", "土", "日"]

app = Flask(__name__)

# ──────────────────────────────────────────────
# メインUI（1ページ完結）
# ──────────────────────────────────────────────

UI_HTML = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ brand }} ストーリー生成 — {{ clinic_name }}</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;900&family=Montserrat:wght@700;900&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --navy: #0D1B2A; --gold: #C8A96E; --gold-dk: #A8893E;
    --bg: #F4F5F7; --white: #fff; --border: #E2E5EA;
    --text: #1A2433; --text-sub: #6B7280; --radius: 12px;
  }
  body { font-family: 'Noto Sans JP', sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }

  /* ヘッダー */
  header {
    background: var(--navy); padding: 16px 24px;
    display: flex; align-items: center; gap: 12px;
    position: sticky; top: 0; z-index: 10;
  }
  .brand { font-family: 'Montserrat', sans-serif; font-weight: 900; font-size: 20px; color: var(--gold); letter-spacing: 0.14em; }
  .clinic { font-size: 12px; color: rgba(255,255,255,0.5); letter-spacing: 0.08em; margin-top: 2px; }

  /* レイアウト */
  .layout { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; padding: 24px; max-width: 960px; margin: 0 auto; }
  @media (max-width: 680px) { .layout { grid-template-columns: 1fr; } }

  /* カード */
  .card { background: var(--white); border-radius: var(--radius); padding: 24px; box-shadow: 0 1px 4px rgba(0,0,0,0.07); }
  .card-title { font-size: 14px; font-weight: 700; margin-bottom: 6px; display: flex; align-items: center; gap: 8px; }
  .card-title .icon { font-size: 18px; }
  .card-desc { font-size: 12px; color: var(--text-sub); margin-bottom: 18px; }

  /* 院名入力 */
  .clinic-input-wrap { display: flex; align-items: center; gap: 10px; margin-bottom: 0; }
  .clinic-input {
    flex: 1; font-family: 'Noto Sans JP', sans-serif; font-size: 15px; font-weight: 700;
    padding: 10px 14px; border: 2px solid var(--border); border-radius: 8px;
    outline: none; color: var(--text); background: var(--bg); transition: border-color 0.15s;
  }
  .clinic-input:focus { border-color: var(--gold); background: #fff; }

  /* スロット行 */
  .slot-row {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 12px; border: 1.5px solid var(--border);
    border-radius: 10px; background: var(--bg); margin-bottom: 8px;
  }
  .slot-time-input {
    font-family: 'Montserrat', sans-serif; font-size: 20px; font-weight: 700;
    width: 90px; border: none; background: transparent; outline: none; color: var(--text);
  }
  .slot-time-input:focus { background: #fff; border-radius: 6px; padding: 2px 6px; }
  .status-group { display: flex; gap: 6px; flex: 1; flex-wrap: wrap; }
  .status-btn {
    padding: 5px 12px; border-radius: 20px; border: 1.5px solid var(--border);
    font-size: 11px; font-weight: 700; cursor: pointer; background: #fff;
    color: var(--text-sub); transition: all 0.15s; font-family: inherit;
  }
  .status-btn.active-ok  { background: #E8F8EE; border-color: #27AE60; color: #1E8A47; }
  .status-btn.active-few { background: #FEF3E2; border-color: #E67E22; color: #C06010; }
  .status-btn.active-full{ background: #F0F2F5; border-color: #AAB4BE; color: #6B7280; }
  .del-btn {
    width: 28px; height: 28px; border-radius: 50%; border: none;
    background: #F0F2F5; color: #9CA3AF; cursor: pointer; font-size: 16px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; transition: background 0.15s;
  }
  .del-btn:hover { background: #FFE4E4; color: #E53E3E; }

  /* ボタン */
  .btn { display: flex; align-items: center; justify-content: center; gap: 8px;
    padding: 12px 20px; border-radius: 8px; border: none; cursor: pointer;
    font-family: inherit; font-weight: 700; font-size: 13px; transition: all 0.15s; }
  .btn-outline { background: #fff; border: 1.5px solid var(--border); color: var(--text); width: 100%; margin-top: 4px; }
  .btn-outline:hover { border-color: var(--gold); color: var(--gold-dk); }
  .btn-primary { background: var(--navy); color: var(--gold); width: 100%; font-size: 15px; padding: 16px; margin-top: 8px; }
  .btn-primary:hover { background: #1a2e45; }
  .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
  .btn-dl { background: var(--gold); color: var(--navy); flex: 1; font-size: 14px; padding: 14px; text-decoration: none; }
  .btn-dl:hover { background: var(--gold-dk); }
  .btn-regen { background: #fff; border: 1.5px solid var(--border); color: var(--text); padding: 14px 18px; }
  .btn-regen:hover { border-color: var(--gold); }

  /* プレビュー */
  .preview-wrap { position: sticky; top: 84px; }
  .preview-header { display: flex; justify-content: space-between; align-items: center;
    font-family: 'Montserrat', sans-serif; font-size: 10px; font-weight: 700;
    letter-spacing: 0.14em; color: var(--text-sub); margin-bottom: 10px; }
  .preview-body { background: #E8E8E8; border-radius: 10px; overflow: hidden;
    aspect-ratio: 9/16; display: flex; align-items: center; justify-content: center; }
  .preview-body img { width: 100%; height: 100%; object-fit: contain; }
  .ph { text-align: center; color: #9CA3AF; }
  .ph-icon { font-size: 40px; margin-bottom: 10px; }
  .ph-text { font-size: 12px; }
  .actions { display: flex; gap: 10px; margin-top: 12px; }

  /* トースト */
  .toast {
    position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%) translateY(80px);
    background: var(--navy); color: #fff; padding: 12px 24px; border-radius: 100px;
    font-size: 13px; font-weight: 600; transition: transform 0.3s; z-index: 100;
  }
  .toast.show { transform: translateX(-50%) translateY(0); }
</style>
</head>
<body>

<header>
  <div>
    <div class="brand">{{ brand }}</div>
    <div class="clinic">{{ brand_sub }} {{ clinic_name }}</div>
  </div>
</header>

<div class="layout">

  <!-- 左: 設定 -->
  <div>
    <div class="card">
      <div class="card-title"><span class="icon">🏥</span> 院名</div>
      <div class="card-desc">画像に表示される院名を入力してください。</div>
      <div class="clinic-input-wrap">
        <input class="clinic-input" id="clinic-name-input" type="text"
               value="{{ clinic_name }}" placeholder="例：伊勢崎宮子院">
      </div>
    </div>

    <div class="card" style="margin-top:16px">
      <div class="card-title"><span class="icon">⏰</span> 時間枠の設定</div>
      <div class="card-desc">時刻を入力し、各枠の空き状況を選んでください。</div>
      <div id="slot-list"></div>
      <button class="btn btn-outline" onclick="addSlot()">＋ 時間枠を追加</button>
    </div>

    <div class="card" style="margin-top:16px">
      <div class="card-title"><span class="icon">🎨</span> 画像を生成</div>
      <div class="card-desc">1080×1920px のストーリー画像を生成します。</div>
      <button class="btn btn-primary" id="gen-btn" onclick="generate()">
        ストーリー画像を生成する
      </button>
    </div>
  </div>

  <!-- 右: プレビュー -->
  <div class="preview-wrap">
    <div class="preview-header">
      <span>PREVIEW</span>
      <span>1080 × 1920</span>
    </div>
    <div class="preview-body" id="preview-body">
      <div class="ph">
        <div class="ph-icon">📱</div>
        <div class="ph-text">生成するとここに表示</div>
      </div>
    </div>
    <div class="actions" id="actions" style="display:none">
      <a id="dl-btn" href="#" class="btn btn-dl" download>⬇ 画像を保存</a>
      <button class="btn btn-regen" onclick="generate()">再生成</button>
    </div>
  </div>

</div>

<div class="toast" id="toast"></div>

<script>
let slots = [
  {time:'10:00', status:'available'},
  {time:'11:00', status:'available'},
  {time:'13:00', status:'available'},
  {time:'15:00', status:'available'},
];

const STATUS = {
  available: {label:'◎ 空きあり', cls:'active-ok'},
  few:       {label:'△ 残り僅か', cls:'active-few'},
  full:      {label:'× 満席',    cls:'active-full'},
};

function renderSlots() {
  const list = document.getElementById('slot-list');
  list.innerHTML = slots.map((s, i) => `
    <div class="slot-row">
      <input class="slot-time-input" type="text" value="${s.time}"
             oninput="slots[${i}].time=this.value">
      <div class="status-group">
        ${Object.entries(STATUS).map(([k,v]) => `
          <button class="status-btn ${s.status===k?v.cls:''}"
                  onclick="setStatus(${i},'${k}')">${v.label}</button>
        `).join('')}
      </div>
      <button class="del-btn" onclick="removeSlot(${i})">×</button>
    </div>
  `).join('');
}

function setStatus(i, status) {
  slots[i].status = status;
  renderSlots();
}

function addSlot() {
  const last = slots[slots.length-1]?.time || '09:00';
  const [h] = last.split(':').map(Number);
  slots.push({time: `${String(h+1).padStart(2,'0')}:00`, status:'available'});
  renderSlots();
}

function removeSlot(i) {
  if (slots.length <= 1) { showToast('最低1枠は必要です'); return; }
  slots.splice(i, 1);
  renderSlots();
}

async function generate() {
  const btn = document.getElementById('gen-btn');
  btn.disabled = true;
  btn.textContent = '生成中…';
  document.getElementById('actions').style.display = 'none';
  document.getElementById('preview-body').innerHTML =
    '<div class="ph"><div class="ph-icon" style="animation:spin 1s linear infinite">⏳</div></div>';

  try {
    const clinicName = document.getElementById('clinic-name-input').value.trim();
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({slots, clinic_name: clinicName})
    });
    const data = await res.json();
    if (data.ok) {
      document.getElementById('preview-body').innerHTML =
        `<img src="/output/${data.filename}?t=${Date.now()}" alt="story">`;
      const dl = document.getElementById('dl-btn');
      dl.href = `/download/${data.filename}`;
      dl.download = data.filename;
      document.getElementById('actions').style.display = 'flex';
      showToast('✓ 生成完了！「画像を保存」でダウンロードしてください');
    } else {
      showToast('エラー: ' + data.error);
      resetPreview();
    }
  } catch(e) {
    showToast('生成に失敗しました');
    resetPreview();
  } finally {
    btn.disabled = false;
    btn.textContent = 'ストーリー画像を生成する';
  }
}

function resetPreview() {
  document.getElementById('preview-body').innerHTML =
    '<div class="ph"><div class="ph-icon">📱</div><div class="ph-text">生成するとここに表示</div></div>';
}

let _toast;
function showToast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(_toast);
  _toast = setTimeout(() => el.classList.remove('show'), 3000);
}

renderSlots();
</script>
</body>
</html>"""


# ──────────────────────────────────────────────
# ルート
# ──────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(
        UI_HTML,
        brand=BRAND,
        brand_sub=BRAND_SUB,
        clinic_name=CLINIC_NAME,
    )


@app.route("/api/generate", methods=["POST"])
def api_generate():
    try:
        from playwright.sync_api import sync_playwright

        body        = request.get_json()
        slots       = body.get("slots", [])
        clinic_name = body.get("clinic_name", CLINIC_NAME) or CLINIC_NAME
        now         = datetime.now()

        # 空き数カウント
        available_count = sum(1 for s in slots if s["status"] == "available")

        # スロットHTML生成
        def slot_html(s):
            st = s["status"]
            time_val = s["time"]
            if st == "available":
                label = "空きあり"
                dot   = ""
            elif st == "few":
                label = "残り僅か"
                dot   = ""
            else:
                label = "満席"
                dot   = ""
            return f"""
      <div class="slot-card {st}">
        <div class="slot-time">{time_val}</div>
        <div class="slot-middle"></div>
        <div class="slot-status">
          <div class="slot-status-dot"></div>
          {label}
        </div>
      </div>"""

        slots_html = "\n".join(slot_html(s) for s in slots)

        # テンプレート読み込み・変数埋め込み
        html = TEMPLATE_PATH.read_text(encoding="utf-8")
        replacements = {
            "{{BRAND}}":           BRAND,
            "{{BRAND_SUB}}":       BRAND_SUB,
            "{{CLINIC_NAME}}":     clinic_name,
            "{{DAY}}":             str(now.day).zfill(2),
            "{{MONTH_YEAR}}":      f"{now.month:02d} / {now.year}",
            "{{WEEKDAY}}":         WEEKDAY_JA[now.weekday()] + "曜日",
            "{{AVAILABLE_COUNT}}": str(available_count),
            "{{SLOTS}}":           slots_html,
        }
        for k, v in replacements.items():
            html = html.replace(k, v)

        # 一時HTMLを書き出し
        tmp_html = OUTPUT_DIR / "_tmp_story.html"
        tmp_html.write_text(html, encoding="utf-8")

        # Playwright でスクリーンショット
        filename = f"story_{now.strftime('%Y%m%d_%H%M%S')}.png"
        out_png  = OUTPUT_DIR / filename

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page    = browser.new_page(viewport={"width": 1080, "height": 1920})
            page.goto(f"file://{tmp_html.absolute()}", wait_until="networkidle")
            page.wait_for_timeout(1500)
            page.screenshot(path=str(out_png), full_page=False)
            browser.close()

        tmp_html.unlink(missing_ok=True)
        return jsonify({"ok": True, "filename": filename})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/output/<filename>")
def serve_output(filename):
    path = OUTPUT_DIR / filename
    if not path.exists():
        return "not found", 404
    return send_file(path, mimetype="image/png")


@app.route("/download/<filename>")
def download(filename):
    path = OUTPUT_DIR / filename
    if not path.exists():
        return "not found", 404
    return send_file(path, as_attachment=True, download_name=filename)


# ──────────────────────────────────────────────
# 起動
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import socket
    try:
        ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        ip = "確認できませんでした"

    print(f"\n{'='*44}")
    print(f"  KINMAQ Story Generator")
    print(f"  院名: {CLINIC_NAME}")
    print(f"{'='*44}")
    print(f"  このPC:         http://localhost:{PORT}")
    print(f"  同じWi-Fiから: http://{ip}:{PORT}")
    print(f"{'='*44}\n")

    app.run(host="0.0.0.0", port=PORT, debug=False)
