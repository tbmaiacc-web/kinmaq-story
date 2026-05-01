#!/usr/bin/env python3
"""
KINMAQ Story Generator
ストーリー画像（空き状況）を生成するシンプルなWebアプリ
"""

import json
import os
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template_string, request, send_file

# ──────────────────────────────────────────────
# 設定読み込み
# ──────────────────────────────────────────────

BASE          = Path(__file__).parent
CONFIG_PATH   = BASE / "config.json"
TEMPLATE_PATH = BASE / "template.html"
OUTPUT_DIR    = BASE / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

config    = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
BRAND     = config.get("brand", "KINMAQ")
BRAND_SUB = config.get("brand_sub", "Next整体")
PORT      = int(os.environ.get("PORT", config.get("port", 5100)))

WEEKDAY_JA = ["月", "火", "水", "木", "金", "土", "日"]

# ──────────────────────────────────────────────
# 6院カラースキーム
# ──────────────────────────────────────────────

BRANCHES = [
    {
        "name": "草加院",
        "primary":    "#1E3A2F",   # ディープフォレストグリーン
        "accent":     "#C9B882",   # シャンパンゴールド
        "accent_dk":  "#A89660",
        "page_bg":    "#F4F7F4",
        "border":     "#D8E6D8",
    },
    {
        "name": "イオン八潮南院",
        "primary":    "#2C1F44",   # ディーププラム
        "accent":     "#C8B87A",   # ウォームゴールド
        "accent_dk":  "#A89050",
        "page_bg":    "#F7F5FA",
        "border":     "#E2DCF0",
    },
    {
        "name": "上尾院",
        "primary":    "#3C1D26",   # ボルドー
        "accent":     "#D4957E",   # ローズゴールド
        "accent_dk":  "#B0705A",
        "page_bg":    "#FAF5F5",
        "border":     "#EEE0DC",
    },
    {
        "name": "前橋院",
        "primary":    "#1E2E40",   # ダークスチールブルー
        "accent":     "#C89060",   # アンバーコッパー
        "accent_dk":  "#A87040",
        "page_bg":    "#F5F7FA",
        "border":     "#DDE3EA",
    },
    {
        "name": "伊勢崎宮子院",
        "primary":    "#0D1B2A",   # ネイビー（デフォルト）
        "accent":     "#C8A96E",   # ゴールド
        "accent_dk":  "#A8893E",
        "page_bg":    "#F7F5F1",
        "border":     "#E8E4DE",
    },
    {
        "name": "取手院",
        "primary":    "#1A3836",   # ディープティール
        "accent":     "#88C4B0",   # セージミント
        "accent_dk":  "#5EA090",
        "page_bg":    "#F3F8F7",
        "border":     "#D0E8E2",
    },
]

# JSON文字列としてテンプレートに渡す
BRANCHES_JSON = json.dumps(BRANCHES, ensure_ascii=False)

app = Flask(__name__)

# ──────────────────────────────────────────────
# メインUI（1ページ完結）
# ──────────────────────────────────────────────

UI_HTML = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ brand }} ストーリー生成</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;900&family=Montserrat:wght@700;900&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --primary: #0D1B2A; --accent: #C8A96E; --accent-dk: #A8893E;
    --bg: #F4F5F7; --white: #fff; --border: #E2E5EA;
    --text: #1A2433; --text-sub: #6B7280; --radius: 12px;
  }
  body { font-family: 'Noto Sans JP', sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }

  /* ヘッダー */
  header {
    background: var(--primary); padding: 16px 24px;
    display: flex; align-items: center; gap: 12px;
    position: sticky; top: 0; z-index: 10;
    transition: background 0.4s ease;
  }
  .hdr-brand { font-family: 'Montserrat', sans-serif; font-weight: 900; font-size: 20px; color: var(--accent); letter-spacing: 0.14em; transition: color 0.4s; }
  .hdr-clinic { font-size: 12px; color: rgba(255,255,255,0.5); letter-spacing: 0.08em; margin-top: 2px; }

  /* レイアウト */
  .layout { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; padding: 24px; max-width: 960px; margin: 0 auto; }
  @media (max-width: 680px) { .layout { grid-template-columns: 1fr; } }

  /* カード */
  .card { background: var(--white); border-radius: var(--radius); padding: 24px; box-shadow: 0 1px 4px rgba(0,0,0,0.07); }
  .card-title { font-size: 14px; font-weight: 700; margin-bottom: 6px; display: flex; align-items: center; gap: 8px; }
  .card-title .icon { font-size: 18px; }
  .card-desc { font-size: 12px; color: var(--text-sub); margin-bottom: 16px; }

  /* 院選択ドロップダウン */
  .branch-select-wrap { position: relative; }
  .branch-select {
    width: 100%; font-family: 'Noto Sans JP', sans-serif; font-size: 15px; font-weight: 700;
    padding: 12px 44px 12px 16px; border: 2px solid var(--border); border-radius: 10px;
    outline: none; color: var(--text); background: var(--bg);
    appearance: none; cursor: pointer;
    transition: border-color 0.15s, background 0.15s;
  }
  .branch-select:focus { border-color: var(--accent); background: #fff; }
  .select-arrow {
    position: absolute; right: 14px; top: 50%; transform: translateY(-50%);
    pointer-events: none; font-size: 12px; color: var(--text-sub);
  }
  /* カラースウォッチプレビュー */
  .color-preview {
    display: flex; gap: 10px; margin-top: 12px; align-items: center;
  }
  .swatch {
    width: 28px; height: 28px; border-radius: 50%;
    border: 2px solid rgba(0,0,0,0.08);
    flex-shrink: 0; transition: background 0.4s;
  }
  .color-label { font-size: 11px; color: var(--text-sub); }

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
  .status-btn.active-ok   { background: #E8F8EE; border-color: #27AE60; color: #1E8A47; }
  .status-btn.active-few  { background: #FEF3E2; border-color: #E67E22; color: #C06010; }
  .status-btn.active-full { background: #F0F2F5; border-color: #AAB4BE; color: #6B7280; }
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
  .btn-outline:hover { border-color: var(--accent); color: var(--accent-dk); }
  .btn-primary {
    background: var(--primary); color: var(--accent);
    width: 100%; font-size: 15px; padding: 16px; margin-top: 8px;
    transition: background 0.4s, color 0.4s;
  }
  .btn-primary:hover { filter: brightness(1.15); }
  .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
  .btn-dl {
    background: var(--accent); color: var(--primary);
    flex: 1; font-size: 14px; padding: 14px; text-decoration: none;
    transition: background 0.4s, color 0.4s;
  }
  .btn-dl:hover { filter: brightness(0.9); }
  .btn-regen { background: #fff; border: 1.5px solid var(--border); color: var(--text); padding: 14px 18px; }
  .btn-regen:hover { border-color: var(--accent); }

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
    background: var(--primary); color: #fff; padding: 12px 24px; border-radius: 100px;
    font-size: 13px; font-weight: 600; transition: transform 0.3s; z-index: 100;
  }
  .toast.show { transform: translateX(-50%) translateY(0); }
</style>
</head>
<body>

<header id="main-header">
  <div>
    <div class="hdr-brand" id="hdr-brand">{{ brand }}</div>
    <div class="hdr-clinic" id="hdr-clinic">{{ brand_sub }} <span id="hdr-clinic-name">伊勢崎宮子院</span></div>
  </div>
</header>

<div class="layout">

  <!-- 左: 設定 -->
  <div>
    <!-- 院選択 -->
    <div class="card">
      <div class="card-title"><span class="icon">🏥</span> 院を選択</div>
      <div class="card-desc">投稿する院を選ぶと、カラーが自動で切り替わります。</div>
      <div class="branch-select-wrap">
        <select class="branch-select" id="branch-select" onchange="onBranchChange()">
          <!-- JSで生成 -->
        </select>
        <span class="select-arrow">▼</span>
      </div>
      <div class="color-preview">
        <div class="swatch" id="swatch-primary"></div>
        <div class="swatch" id="swatch-accent"></div>
        <span class="color-label" id="color-label">カラーテーマ</span>
      </div>
    </div>

    <!-- 時間枠 -->
    <div class="card" style="margin-top:16px">
      <div class="card-title"><span class="icon">⏰</span> 時間枠の設定</div>
      <div class="card-desc">時刻を入力し、各枠の空き状況を選んでください。</div>
      <div id="slot-list"></div>
      <button class="btn btn-outline" onclick="addSlot()">＋ 時間枠を追加</button>
    </div>

    <!-- 生成 -->
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
// ── 院データ ──
const BRANCHES = {{ branches_json | safe }};

let currentBranch = BRANCHES.find(b => b.name === '伊勢崎宮子院') || BRANCHES[0];

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

// ── 初期化 ──
function init() {
  const sel = document.getElementById('branch-select');
  BRANCHES.forEach((b, i) => {
    const opt = document.createElement('option');
    opt.value = i;
    opt.textContent = b.name;
    if (b.name === '伊勢崎宮子院') opt.selected = true;
    sel.appendChild(opt);
  });
  applyTheme(currentBranch);
  renderSlots();
}

// ── 院切替 ──
function onBranchChange() {
  const idx = parseInt(document.getElementById('branch-select').value);
  currentBranch = BRANCHES[idx];
  applyTheme(currentBranch);
  // プレビューをリセット
  resetPreview();
  document.getElementById('actions').style.display = 'none';
}

// ── テーマ適用 ──
function applyTheme(b) {
  const root = document.documentElement;
  root.style.setProperty('--primary',   b.primary);
  root.style.setProperty('--accent',    b.accent);
  root.style.setProperty('--accent-dk', b.accent_dk);

  document.getElementById('hdr-clinic-name').textContent = b.name;
  document.getElementById('hdr-brand').style.color = b.accent;
  document.getElementById('swatch-primary').style.background = b.primary;
  document.getElementById('swatch-accent').style.background  = b.accent;
  document.getElementById('color-label').textContent =
    `${b.primary}  ×  ${b.accent}`;
}

// ── スロット描画 ──
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

function setStatus(i, status) { slots[i].status = status; renderSlots(); }

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

// ── 生成 ──
async function generate() {
  const btn = document.getElementById('gen-btn');
  btn.disabled = true;
  btn.textContent = '生成中…';
  document.getElementById('actions').style.display = 'none';
  document.getElementById('preview-body').innerHTML =
    '<div class="ph"><div class="ph-icon">⏳</div><div class="ph-text">生成中...</div></div>';

  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({
        slots,
        clinic_name:  currentBranch.name,
        primary:      currentBranch.primary,
        accent:       currentBranch.accent,
        accent_dk:    currentBranch.accent_dk,
        page_bg:      currentBranch.page_bg,
        border:       currentBranch.border,
      })
    });
    const data = await res.json();
    if (data.ok) {
      document.getElementById('preview-body').innerHTML =
        `<img src="/output/${data.filename}?t=${Date.now()}" alt="story">`;
      const dl = document.getElementById('dl-btn');
      dl.href     = `/download/${data.filename}`;
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

init();
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
        branches_json=BRANCHES_JSON,
    )


@app.route("/api/generate", methods=["POST"])
def api_generate():
    try:
        from playwright.sync_api import sync_playwright

        body        = request.get_json()
        slots       = body.get("slots", [])
        clinic_name = body.get("clinic_name", "伊勢崎宮子院")
        primary     = body.get("primary",  "#0D1B2A")
        accent      = body.get("accent",   "#C8A96E")
        accent_dk   = body.get("accent_dk","#A8893E")
        page_bg     = body.get("page_bg",  "#F7F5F1")
        border      = body.get("border",   "#E8E4DE")
        now         = datetime.now()

        available_count = sum(1 for s in slots if s["status"] == "available")

        def slot_html(s):
            st       = s["status"]
            time_val = s["time"]
            label    = {"available": "空きあり", "few": "残り僅か", "full": "満席"}.get(st, "")
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
            "{{PRIMARY_COLOR}}":   primary,
            "{{ACCENT_COLOR}}":    accent,
            "{{ACCENT_DK_COLOR}}": accent_dk,
            "{{PAGE_BG}}":         page_bg,
            "{{BORDER_COLOR}}":    border,
        }
        for k, v in replacements.items():
            html = html.replace(k, v)

        tmp_html = OUTPUT_DIR / "_tmp_story.html"
        tmp_html.write_text(html, encoding="utf-8")

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
    print(f"  KINMAQ Story Generator  6院対応")
    print(f"{'='*44}")
    print(f"  http://localhost:{PORT}")
    print(f"  http://{ip}:{PORT}")
    print(f"{'='*44}\n")

    app.run(host="0.0.0.0", port=PORT, debug=False)
