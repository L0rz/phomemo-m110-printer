"""
Phomemo M110 Web Interface — Clean Edition
"""

WEB_INTERFACE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Phomemo M110</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root {
            --bg: #f0f2f5; --card: #fff; --text: #1a1a2e; --text2: #555;
            --border: #e0e0e0; --accent: #4361ee; --accent2: #3a0ca3;
            --success: #06d6a0; --error: #ef476f; --warn: #ffd166;
            --radius: 12px; --shadow: 0 2px 12px rgba(0,0,0,.08);
        }
        [data-theme="dark"] {
            --bg: #0f0f1a; --card: #1a1a2e; --text: #e0e0e0; --text2: #999;
            --border: #2a2a3e; --shadow: 0 2px 12px rgba(0,0,0,.3);
        }
        * { margin: 0; padding: 0; box-sizing: border-box; transition: background .2s, color .2s; }
        body { font-family: -apple-system, 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }
        .wrap { max-width: 800px; margin: 0 auto; padding: 16px; }

        /* Header */
        .header { display: flex; align-items: center; justify-content: space-between; padding: 16px 0; }
        .header h1 { font-size: 1.4em; }
        .header-right { display: flex; gap: 8px; align-items: center; }
        .status-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
        .status-dot.on { background: var(--success); box-shadow: 0 0 6px var(--success); }
        .status-dot.off { background: var(--error); }
        .icon-btn { background: none; border: 1px solid var(--border); color: var(--text); width: 36px; height: 36px;
            border-radius: 50%; cursor: pointer; font-size: 16px; display: flex; align-items: center; justify-content: center; }
        .icon-btn:hover { background: var(--accent); color: #fff; border-color: var(--accent); }

        /* Cards */
        .card { background: var(--card); border-radius: var(--radius); box-shadow: var(--shadow);
            border: 1px solid var(--border); margin-bottom: 16px; overflow: hidden; }
        .card-header { padding: 14px 18px; font-weight: 600; font-size: .95em; display: flex;
            align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border); }
        .card-body { padding: 18px; }

        /* Tabs */
        .tabs { display: flex; border-bottom: 2px solid var(--border); margin-bottom: 16px; }
        .tab { padding: 10px 20px; cursor: pointer; font-weight: 500; color: var(--text2);
            border-bottom: 2px solid transparent; margin-bottom: -2px; }
        .tab.active { color: var(--accent); border-bottom-color: var(--accent); }
        .tab:hover { color: var(--accent); }
        .tab-content { display: none; }
        .tab-content.active { display: block; }

        /* Form */
        textarea { width: 100%; padding: 12px; border: 1px solid var(--border); border-radius: 8px;
            font-family: inherit; font-size: 14px; resize: vertical; background: var(--bg); color: var(--text); }
        textarea:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px rgba(67,97,238,.15); }
        select, input[type="number"] { padding: 8px 12px; border: 1px solid var(--border); border-radius: 8px;
            background: var(--bg); color: var(--text); font-size: 14px; }
        input[type="file"] { font-size: 14px; }

        /* Buttons */
        .btn { padding: 10px 20px; border: none; border-radius: 8px; font-weight: 600; cursor: pointer;
            font-size: 14px; display: inline-flex; align-items: center; gap: 6px; }
        .btn-primary { background: var(--accent); color: #fff; }
        .btn-primary:hover { background: var(--accent2); }
        .btn-outline { background: none; border: 1px solid var(--border); color: var(--text); }
        .btn-outline:hover { border-color: var(--accent); color: var(--accent); }
        .btn-sm { padding: 6px 12px; font-size: 12px; }
        .btn:disabled { opacity: .5; cursor: not-allowed; }
        .btn-row { display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; }

        /* Preview */
        .preview-box { border: 2px dashed var(--border); border-radius: 8px; padding: 24px;
            text-align: center; color: var(--text2); font-size: 14px; min-height: 120px;
            display: flex; flex-direction: column; align-items: center; justify-content: center; }
        .preview-box img { max-width: 100%; max-height: 240px; image-rendering: pixelated;
            border-radius: 4px; border: 1px solid var(--border); background: #fff; }
        .preview-info { font-size: 12px; color: var(--text2); margin-top: 8px; }

        /* Collapsible settings */
        .collapsible { cursor: pointer; user-select: none; }
        .collapsible::after { content: '▸'; margin-left: 8px; font-size: 12px; }
        .collapsible.open::after { content: '▾'; }
        .collapse-body { display: none; padding: 14px 0 0; }
        .collapse-body.open { display: block; }
        .setting-row { display: flex; gap: 16px; align-items: center; flex-wrap: wrap; margin-bottom: 10px; }
        .setting-row label { font-size: 13px; color: var(--text2); min-width: 100px; }
        .setting-row input[type="range"] { flex: 1; max-width: 200px; }

        /* Image options */
        .img-opts { display: flex; gap: 16px; flex-wrap: wrap; margin: 12px 0; }
        .img-opts label { font-size: 13px; display: flex; align-items: center; gap: 4px; }

        /* Toast */
        .toast { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
            padding: 10px 24px; border-radius: 8px; font-size: 14px; font-weight: 500;
            box-shadow: 0 4px 16px rgba(0,0,0,.15); z-index: 100; opacity: 0;
            transition: opacity .3s; pointer-events: none; }
        .toast.show { opacity: 1; }
        .toast.success { background: var(--success); color: #000; }
        .toast.error { background: var(--error); color: #fff; }
        .toast.info { background: var(--accent); color: #fff; }

        /* Grid helpers */
        .row { display: flex; gap: 12px; flex-wrap: wrap; }
        .row > * { flex: 1; min-width: 140px; }

        /* Responsive */
        @media (max-width: 600px) {
            .wrap { padding: 8px; }
            .tabs { overflow-x: auto; }
            .tab { padding: 8px 14px; font-size: 14px; white-space: nowrap; }
        }
    </style>
</head>
<body>
<div class="wrap">
    <!-- Header -->
    <div class="header">
        <h1>🖨️ Phomemo M110</h1>
        <div class="header-right">
            <span class="status-dot off" id="statusDot" title="Nicht verbunden"></span>
            <span id="queueBadge" style="display:none;background:var(--warn);color:#000;font-size:11px;font-weight:700;padding:2px 8px;border-radius:10px;cursor:pointer" onclick="switchTab('settings')" title="Jobs in Queue"></span>
            <button class="icon-btn" onclick="reconnect()" title="Reconnect">🔄</button>
            <button class="icon-btn" onclick="toggleTheme()" id="themeBtn" title="Theme">🌙</button>
        </div>
    </div>

    <!-- Tabs -->
    <div class="tabs">
        <div class="tab active" onclick="switchTab('text')">📝 Text</div>
        <div class="tab" onclick="switchTab('image')">🖼️ Bild</div>
        <div class="tab" onclick="switchTab('settings')">⚙️ Einstellungen</div>
    </div>

    <!-- TEXT TAB -->
    <div class="tab-content active" id="tab-text">
        <div class="card">
            <div class="card-body">
                <textarea id="textInput" rows="5" placeholder="Text eingeben... Markdown: **fett**, # Überschrift&#10;QR: #qr#https://example.com#qr#&#10;Barcode: #bar#12345#bar#" oninput="debouncedTextPreview()"></textarea>
                <div class="row" style="margin-top:12px">
                    <div>
                        <label style="font-size:13px;color:var(--text2)">Schriftgröße</label>
                        <select id="fontSize" onchange="updateTextPreview()" style="width:100%">
                            <option value="18">Klein (18)</option>
                            <option value="22" selected>Normal (22)</option>
                            <option value="26">Groß (26)</option>
                            <option value="30">XL (30)</option>
                        </select>
                    </div>
                    <div>
                        <label style="font-size:13px;color:var(--text2)">Ausrichtung</label>
                        <select id="textAlignment" onchange="updateTextPreview()" style="width:100%">
                            <option value="left">Links</option>
                            <option value="center" selected>Zentriert</option>
                            <option value="right">Rechts</option>
                        </select>
                    </div>
                </div>
                <div class="preview-box" id="textPreview" style="margin-top:14px">
                    <div id="textPreviewPlaceholder">Vorschau erscheint beim Tippen</div>
                    <img id="textPreviewImage" style="display:none">
                    <div id="textInfo" class="preview-info" style="display:none"></div>
                </div>
                <div class="btn-row">
                    <button class="btn btn-primary" onclick="printText(false)">🖨️ Drucken</button>
                    <button class="btn btn-outline" onclick="printText(true)">📤 In Queue</button>
                </div>
            </div>
        </div>
    </div>

    <!-- IMAGE TAB -->
    <div class="tab-content" id="tab-image">
        <div class="card">
            <div class="card-body">
                <input type="file" id="imageFile" accept="image/*" onchange="uploadAndPreview()">
                <div class="preview-box" id="imagePreview" style="margin-top:14px">
                    <div id="previewPlaceholder">📁 Bild auswählen für Vorschau</div>
                    <img id="previewImage" style="display:none">
                    <div id="imageInfo" class="preview-info" style="display:none"></div>
                </div>
                <div class="img-opts">
                    <label><input type="checkbox" id="fitToLabel" checked onchange="updatePreview()"> An Label anpassen</label>
                    <label><input type="checkbox" id="maintainAspect" checked onchange="updatePreview()"> Seitenverhältnis</label>
                    <label><input type="checkbox" id="enableDither" checked onchange="updatePreview()"> Dithering</label>
                </div>
                <div class="row" style="margin-bottom:12px">
                    <div>
                        <label style="font-size:13px;color:var(--text2)">Skalierung</label>
                        <select id="scalingMode" onchange="updatePreview()" style="width:100%">
                            <option value="fit_aspect">Einpassen</option>
                            <option value="stretch_full">Strecken</option>
                            <option value="crop_center">Zuschneiden</option>
                            <option value="pad_center">Zentriert + Rand</option>
                        </select>
                    </div>
                    <div>
                        <label style="font-size:13px;color:var(--text2)">Dither Preset</label>
                        <select id="ditherPreset" onchange="applyDitherPreset()" style="width:100%">
                            <option value="normal">Normal</option>
                            <option value="soft">Weich</option>
                            <option value="sharp">Scharf</option>
                            <option value="high_contrast">Kontrast</option>
                        </select>
                    </div>
                </div>
                <div class="btn-row">
                    <button class="btn btn-primary" onclick="printImage(false)" id="printImageBtn" disabled>🖨️ Drucken</button>
                    <button class="btn btn-outline" onclick="printImage(true)" id="queueImageBtn" disabled>📤 In Queue</button>
                </div>
            </div>
        </div>
    </div>

    <!-- SETTINGS TAB -->
    <div class="tab-content" id="tab-settings">
        <div class="card">
            <div class="card-header">Druckeinstellungen</div>
            <div class="card-body">
                <div class="setting-row">
                    <label>X-Offset (px)</label>
                    <input type="number" id="xOffset" value="0" min="0" max="100" step="1" style="width:80px">
                </div>
                <div class="setting-row">
                    <label>Y-Offset (px)</label>
                    <input type="number" id="yOffset" value="0" min="-50" max="50" step="1" style="width:80px">
                </div>
                <div class="setting-row">
                    <label>Dither Threshold</label>
                    <input type="range" id="ditherThreshold" value="128" min="0" max="255" step="1" oninput="this.nextElementSibling.textContent=this.value">
                    <span style="font-weight:600;min-width:30px">128</span>
                </div>
                <div class="setting-row">
                    <label>Dither Stärke</label>
                    <input type="range" id="ditherStrength" value="1.0" min="0.1" max="2.0" step="0.1" oninput="this.nextElementSibling.textContent=this.value">
                    <span style="font-weight:600;min-width:30px">1.0</span>
                </div>
                <div class="setting-row">
                    <label>Kontrast</label>
                    <input type="range" id="contrastBoost" value="1.0" min="0.5" max="2.0" step="0.1" oninput="this.nextElementSibling.textContent=this.value">
                    <span style="font-weight:600;min-width:30px">1.0</span>
                </div>
                <div class="setting-row">
                    <label><input type="checkbox" id="enableDitherGlobal" checked> Dithering global</label>
                </div>
                <div class="btn-row">
                    <button class="btn btn-primary" onclick="saveSettings()">💾 Speichern</button>
                    <button class="btn btn-outline" onclick="testOffsets()">📐 Offsets testen</button>
                </div>
            </div>
        </div>
        <div class="card">
            <div class="card-header">Verbindung</div>
            <div class="card-body">
                <div id="connDetails" style="font-size:13px;color:var(--text2)">Lade...</div>
                <div id="queueInfo" style="display:none;margin:10px 0;padding:10px;background:var(--bg);border-radius:8px;font-size:13px">
                    📋 <strong>Queue:</strong> <span id="queueCount">0</span> Jobs wartend
                </div>
                <div class="btn-row">
                    <button class="btn btn-outline" onclick="checkConnection()">🔍 Status</button>
                    <button class="btn btn-outline" onclick="reconnect()">🔄 Reconnect</button>
                    <button class="btn btn-outline" onclick="manualConnect()">🔧 Manual</button>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Toast -->
<div class="toast" id="toast"></div>

<script>
let currentImageData = null;
let textPreviewTimeout;

// === THEME ===
function initTheme() {
    const saved = localStorage.getItem('phomemo-theme');
    const dark = saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme:dark)').matches);
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
    document.getElementById('themeBtn').textContent = dark ? '☀️' : '🌙';
}
function toggleTheme() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const t = isDark ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', t);
    localStorage.setItem('phomemo-theme', t);
    document.getElementById('themeBtn').textContent = t === 'dark' ? '☀️' : '🌙';
}

// === TABS ===
function switchTab(name) {
    document.querySelectorAll('.tab').forEach((t,i) => t.classList.toggle('active', t.textContent.includes(
        name === 'text' ? 'Text' : name === 'image' ? 'Bild' : 'Einstellungen')));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.getElementById('tab-' + name).classList.add('active');
}

// === TOAST ===
function toast(msg, type='info') {
    const t = document.getElementById('toast');
    t.textContent = msg; t.className = 'toast ' + type + ' show';
    setTimeout(() => t.classList.remove('show'), 3000);
}

// === CONNECTION ===
function checkConnection() {
    fetch('/api/status').then(r=>r.json()).then(d => {
        const dot = document.getElementById('statusDot');
        dot.className = 'status-dot ' + (d.connected ? 'on' : 'off');
        dot.title = d.connected ? 'Verbunden' : 'Getrennt';
        updateSettingsFromData(d.settings || {});
        const det = document.getElementById('connDetails');
        const qSize = d.queue_size || 0;
        const badge = document.getElementById('queueBadge');
        const qInfo = document.getElementById('queueInfo');
        if (qSize > 0) {
            badge.textContent = '📋 ' + qSize;
            badge.style.display = '';
            qInfo.style.display = '';
            document.getElementById('queueCount').textContent = qSize;
        } else {
            badge.style.display = 'none';
            qInfo.style.display = 'none';
        }
        if (d.connected) {
            det.innerHTML = '✅ Verbunden<br>MAC: ' + d.mac + '<br>Heartbeat: ' +
                (d.last_heartbeat ? new Date(d.last_heartbeat*1000).toLocaleTimeString() : '—') +
                '<br>Jobs: ' + (d.stats?.successful_jobs||0) + ' ✓ / ' + (d.stats?.failed_jobs||0) + ' ✗';
        } else {
            det.innerHTML = '❌ Nicht verbunden<br>Status: ' + (d.status||'unbekannt');
        }
    }).catch(e => toast('Verbindungsfehler', 'error'));
}
function reconnect() {
    toast('Reconnect...', 'info');
    fetch('/api/force-reconnect', {method:'POST'}).then(r=>r.json()).then(d => {
        toast(d.success ? '✅ Verbunden!' : '❌ Fehlgeschlagen', d.success ? 'success' : 'error');
        checkConnection();
    }).catch(() => toast('Fehler', 'error'));
}
function manualConnect() {
    toast('Verbinde...', 'info');
    fetch('/api/manual-connect', {method:'POST'}).then(r=>r.json()).then(d => {
        toast(d.success ? '✅ Verbunden!' : '❌ Fehlgeschlagen', d.success ? 'success' : 'error');
        checkConnection();
    }).catch(() => toast('Fehler', 'error'));
}

// === SETTINGS ===
function updateSettingsFromData(s) {
    if (s.x_offset !== undefined) document.getElementById('xOffset').value = s.x_offset;
    if (s.y_offset !== undefined) document.getElementById('yOffset').value = s.y_offset;
    if (s.dither_threshold !== undefined) {
        const el = document.getElementById('ditherThreshold'); el.value = s.dither_threshold;
        el.nextElementSibling.textContent = s.dither_threshold;
    }
    if (s.dither_strength !== undefined) {
        const el = document.getElementById('ditherStrength'); el.value = s.dither_strength;
        el.nextElementSibling.textContent = s.dither_strength;
    }
    if (s.contrast_boost !== undefined) {
        const el = document.getElementById('contrastBoost'); el.value = s.contrast_boost;
        el.nextElementSibling.textContent = s.contrast_boost;
    }
    if (s.dither_enabled !== undefined) document.getElementById('enableDitherGlobal').checked = s.dither_enabled;
}
function saveSettings() {
    const s = {
        x_offset: parseInt(document.getElementById('xOffset').value),
        y_offset: parseInt(document.getElementById('yOffset').value),
        dither_threshold: parseInt(document.getElementById('ditherThreshold').value),
        dither_enabled: document.getElementById('enableDitherGlobal').checked,
        dither_strength: parseFloat(document.getElementById('ditherStrength').value),
        contrast_boost: parseFloat(document.getElementById('contrastBoost').value)
    };
    fetch('/api/settings', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(s)})
        .then(r=>r.json()).then(d => toast(d.success ? '✅ Gespeichert!' : '❌ Fehler', d.success ? 'success' : 'error'))
        .catch(() => toast('Fehler', 'error'));
}
function testOffsets() {
    toast('Teste Offsets...', 'info');
    fetch('/api/test-offsets', {method:'POST'}).then(r=>r.json())
        .then(d => toast(d.success ? '✅ Gedruckt!' : '❌ Fehler', d.success ? 'success' : 'error'))
        .catch(() => toast('Fehler', 'error'));
}

// === TEXT ===
function updateTextPreview() {
    const text = document.getElementById('textInput').value;
    if (!text.trim()) {
        document.getElementById('textPreviewPlaceholder').style.display = '';
        document.getElementById('textPreviewImage').style.display = 'none';
        document.getElementById('textInfo').style.display = 'none';
        return;
    }
    const fd = new FormData();
    fd.append('text', text);
    fd.append('font_size', document.getElementById('fontSize').value);
    fd.append('alignment', document.getElementById('textAlignment').value);
    const endpoint = (text.includes('#qr#') || text.includes('#bar#')) ? '/api/preview-text-with-codes' : '/api/preview-text';
    fetch(endpoint, {method:'POST', body:fd}).then(r=>r.json()).then(d => {
        if (d.success) {
            document.getElementById('textPreviewPlaceholder').style.display = 'none';
            const img = document.getElementById('textPreviewImage');
            img.src = 'data:image/png;base64,' + d.preview_base64;
            img.style.display = 'block';
            document.getElementById('textInfo').textContent = d.info.width + '×' + d.info.height + 'px | ' + d.info.font_size + 'px ' + d.info.alignment;
            document.getElementById('textInfo').style.display = '';
        }
    }).catch(() => {});
}
function debouncedTextPreview() {
    clearTimeout(textPreviewTimeout);
    textPreviewTimeout = setTimeout(updateTextPreview, 300);
}
function printText(queue) {
    const text = document.getElementById('textInput').value;
    if (!text.trim()) { toast('Kein Text!', 'error'); return; }
    const fd = new FormData();
    fd.append('text', text.replace('$TIME$', new Date().toLocaleTimeString()));
    fd.append('font_size', document.getElementById('fontSize').value);
    fd.append('alignment', document.getElementById('textAlignment').value);
    fd.append('immediate', queue ? 'false' : 'true');
    const endpoint = (text.includes('#qr#') || text.includes('#bar#')) ? '/api/print-text-with-codes' : '/api/print-text';
    toast('Drucke...', 'info');
    fetch(endpoint, {method:'POST', body:fd}).then(r=>r.json())
        .then(d => toast(d.success ? '✅ Gedruckt!' : '❌ ' + (d.error||d.message||'Fehler'), d.success ? 'success' : 'error'))
        .catch(() => toast('Druckfehler', 'error'));
}

// === IMAGE ===
function uploadAndPreview() {
    const file = document.getElementById('imageFile').files[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('image', file);
    fd.append('fit_to_label', document.getElementById('fitToLabel').checked);
    fd.append('maintain_aspect', document.getElementById('maintainAspect').checked);
    fd.append('enable_dither', document.getElementById('enableDither').checked);
    fd.append('scaling_mode', document.getElementById('scalingMode').value);
    toast('Erstelle Vorschau...', 'info');
    fetch('/api/preview-image', {method:'POST', body:fd}).then(r=>r.json()).then(d => {
        if (d.success) {
            document.getElementById('previewPlaceholder').style.display = 'none';
            const img = document.getElementById('previewImage');
            img.src = 'data:image/png;base64,' + d.preview_base64;
            img.style.display = 'block';
            document.getElementById('imageInfo').textContent =
                d.info.original_width + '×' + d.info.original_height + ' → ' +
                d.info.processed_width + '×' + d.info.processed_height + 'px';
            document.getElementById('imageInfo').style.display = '';
            document.getElementById('printImageBtn').disabled = false;
            document.getElementById('queueImageBtn').disabled = false;
            currentImageData = file;
            toast('✅ Vorschau fertig', 'success');
        } else { toast('❌ ' + (d.error||''), 'error'); }
    }).catch(e => toast('Fehler: ' + e, 'error'));
}
function updatePreview() { if (currentImageData) { document.getElementById('imageFile').files = new DataTransfer().files; currentImageData && uploadAndPreview(); } }
function applyDitherPreset() {
    const p = document.getElementById('ditherPreset').value;
    const presets = { soft:[100,.5], normal:[128,1], sharp:[150,1.5], high_contrast:[180,2] };
    if (presets[p]) {
        document.getElementById('ditherThreshold').value = presets[p][0];
        document.getElementById('ditherThreshold').nextElementSibling.textContent = presets[p][0];
        document.getElementById('ditherStrength').value = presets[p][1];
        document.getElementById('ditherStrength').nextElementSibling.textContent = presets[p][1];
    }
    if (currentImageData) uploadAndPreview();
}
function printImage(queue) {
    if (!currentImageData) { toast('Kein Bild!', 'error'); return; }
    const fd = new FormData();
    fd.append('image', currentImageData);
    fd.append('immediate', queue ? 'false' : 'true');
    fd.append('fit_to_label', document.getElementById('fitToLabel').checked);
    fd.append('maintain_aspect', document.getElementById('maintainAspect').checked);
    fd.append('enable_dither', document.getElementById('enableDither').checked);
    fd.append('scaling_mode', document.getElementById('scalingMode').value);
    toast('Drucke Bild...', 'info');
    fetch('/api/print-image', {method:'POST', body:fd}).then(r=>r.json())
        .then(d => toast(d.success ? '✅ Gedruckt!' : '❌ ' + (d.error||''), d.success ? 'success' : 'error'))
        .catch(() => toast('Druckfehler', 'error'));
}

// === INIT ===
initTheme();
checkConnection();
setInterval(checkConnection, 10000);
</script>
</body>
</html>
'''
