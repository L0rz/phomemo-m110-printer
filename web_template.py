"""
Erweitertes Web Interface Template für Phomemo M110
Mit Bildvorschau, X-Offset-Konfiguration und erweiterten Features
"""

WEB_INTERFACE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Phomemo M110 - Enhanced Edition</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .card { background: white; padding: 20px; margin: 20px 0; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; margin-bottom: 10px; }
        .subtitle { text-align: center; color: #666; margin-bottom: 30px; }
        
        /* Buttons */
        .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; transition: background 0.3s; }
        .btn:hover { background: #0056b3; }
        .btn-success { background: #28a745; }
        .btn-success:hover { background: #1e7e34; }
        .btn-warning { background: #ffc107; color: #212529; }
        .btn-warning:hover { background: #e0a800; }
        .btn-danger { background: #dc3545; }
        .btn-danger:hover { background: #c82333; }
        .btn:disabled { background: #6c757d; cursor: not-allowed; }
        
        /* Form Elements */
        textarea, input, select { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        input[type="checkbox"] { width: auto; margin: 5px; }
        input[type="number"] { width: 80px; }
        input[type="file"] { padding: 5px; }
        
        /* Status Messages */
        .status { padding: 15px; margin: 10px 0; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
        
        /* Grid Layout */
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }
        @media (max-width: 768px) { .grid, .grid-3 { grid-template-columns: 1fr; } }
        
        /* Debug Info */
        .debug { background: #f8f9fa; border: 1px solid #dee2e6; padding: 10px; margin: 10px 0; border-radius: 5px; font-family: monospace; font-size: 12px; }
        
        /* ==================== DARK MODE ==================== */
        /* Dark Mode Toggle */
        .theme-toggle {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            cursor: pointer;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
        }
        .theme-toggle:hover {
            background: #0056b3;
            transform: scale(1.1);
        }
        
        /* Smooth transitions for all elements */
        * {
            transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
        }
        
        /* Dark mode styles */
        [data-theme="dark"] {
            color-scheme: dark;
        }
        
        [data-theme="dark"] body {
            background: #121212;
            color: #e0e0e0;
        }
        
        [data-theme="dark"] .card {
            background: #1e1e1e;
            border: 1px solid #333;
            box-shadow: 0 2px 10px rgba(0,0,0,0.5);
        }
        
        [data-theme="dark"] h1 {
            color: #e0e0e0;
        }
        
        [data-theme="dark"] .subtitle {
            color: #b0b0b0;
        }
        
        [data-theme="dark"] textarea,
        [data-theme="dark"] input,
        [data-theme="dark"] select {
            background: #2a2a2a;
            color: #e0e0e0;
            border: 1px solid #444;
        }
        
        [data-theme="dark"] textarea:focus,
        [data-theme="dark"] input:focus,
        [data-theme="dark"] select:focus {
            border-color: #007bff;
            box-shadow: 0 0 0 2px rgba(0,123,255,0.25);
        }
        
        [data-theme="dark"] .debug {
            background: #2a2a2a;
            border: 1px solid #444;
            color: #e0e0e0;
        }
        
        [data-theme="dark"] .config-section {
            background: #2a2a2a;
            border: 1px solid #444;
        }
        
        [data-theme="dark"] .config-title {
            color: #e0e0e0;
        }
        
        [data-theme="dark"] .offset-control label {
            color: #b0b0b0;
        }
        
        [data-theme="dark"] .stat-label {
            color: #b0b0b0;
        }
        
        [data-theme="dark"] .preview-container {
            background: #2a2a2a;
            border: 2px dashed #555;
        }
        
        [data-theme="dark"] .preview-image {
            border: 1px solid #555;
            background: #1a1a1a;
        }
        
        [data-theme="dark"] .image-info {
            background: #2a2a2a;
            border: 1px solid #444;
            color: #e0e0e0;
        }
        
        /* Dark mode status messages */
        [data-theme="dark"] .success {
            background: #1a4d2e;
            color: #4ade80;
            border: 1px solid #166534;
        }
        
        [data-theme="dark"] .error {
            background: #4d1a1a;
            color: #f87171;
            border: 1px solid #991b1b;
        }
        
        [data-theme="dark"] .info {
            background: #1a3a4d;
            color: #60a5fa;
            border: 1px solid #1e40af;
        }
        
        [data-theme="dark"] .warning {
            background: #4d3a1a;
            color: #fbbf24;
            border: 1px solid #b45309;
        }
        
        /* Statistics */
        .stats { display: flex; justify-content: space-around; text-align: center; flex-wrap: wrap; }
        .stat-item { flex: 1; min-width: 80px; margin: 5px; }
        .stat-value { font-size: 20px; font-weight: bold; color: #007bff; }
        .stat-label { font-size: 12px; color: #666; }
        
        /* Connection Status */
        .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
        .status-connected { background: #28a745; }
        .status-connecting { background: #ffc107; }
        .status-disconnected { background: #dc3545; }
        .status-failed { background: #6c757d; }
        
        /* Image Preview */
        .preview-container { 
            border: 2px dashed #ddd; 
            border-radius: 10px; 
            padding: 20px; 
            text-align: center; 
            min-height: 200px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            background: #fafafa;
        }
        .preview-image { 
            max-width: 100%; 
            max-height: 300px; 
            border: 1px solid #ccc; 
            border-radius: 5px;
            image-rendering: pixelated;
            background: white;
        }
        .image-info { 
            background: #e9ecef; 
            padding: 10px; 
            margin: 10px 0; 
            border-radius: 5px; 
            font-size: 12px; 
            text-align: left;
        }
        
        /* Configuration Sections */
        .config-section {
            background: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .config-title {
            font-weight: bold;
            margin-bottom: 10px;
            color: #495057;
        }
        
        /* Offset Controls */
        .offset-controls {
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }
        .offset-control {
            display: flex;
            flex-direction: column;
            align-items: center;
            min-width: 100px;
        }
        .offset-control label {
            font-size: 12px;
            margin-bottom: 5px;
            color: #666;
        }
        .offset-control input {
            width: 70px;
            margin: 5px 0;
            text-align: center;
        }
        
        /* Slider Controls */
        .slider-control {
            display: flex;
            flex-direction: column;
            align-items: center;
            min-width: 150px;
        }
        .slider-control input[type="range"] {
            width: 120px;
            margin: 5px 0;
        }
        .slider-value {
            font-weight: bold;
            color: #007bff;
            font-size: 14px;
        }
        
        /* Custom slider styling */
        input[type="range"] {
            -webkit-appearance: none;
            appearance: none;
            height: 6px;
            border-radius: 3px;
            background: #ddd;
            outline: none;
            opacity: 0.7;
            transition: opacity 0.2s;
        }
        input[type="range"]:hover {
            opacity: 1;
        }
        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #007bff;
            cursor: pointer;
        }
        input[type="range"]::-moz-range-thumb {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #007bff;
            cursor: pointer;
            border: none;
        }
        
        /* Image Options */
        .image-options {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            align-items: center;
            margin: 10px 0;
        }
        .image-options label {
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <!-- Dark Mode Toggle Button -->
    <button class="theme-toggle" onclick="toggleTheme()" title="Theme wechseln">
        🌙
    </button>
    
    <div class="container">
        <h1>🖨️ Phomemo M110 Enhanced</h1>
        <div class="subtitle">Mit Bildvorschau und X-Offset Konfiguration</div>
        
        <!-- Connection Status & Settings -->
        <div class="card">
            <h2>🔗 Verbindung & Konfiguration</h2>
            <div class="grid">
                <div>
                    <h3>Status</h3>
                    <div id="connectionStatus"></div>
                    <button class="btn btn-success" onclick="checkConnection()">🔍 Status prüfen</button>
                    <button class="btn btn-warning" onclick="forceReconnect()">🔄 Force Reconnect</button>
                    <button class="btn" onclick="manualConnect()">🔧 Manual Connect</button>
                </div>
                <div class="config-section">
                    <div class="config-title">⚙️ Druckeinstellungen</div>
                    <div class="offset-controls">
                        <div class="offset-control">
                            <label>X-Offset (px)</label>
                            <input type="number" id="xOffset" value="40" min="0" max="100" step="1">
                        </div>
                        <div class="offset-control">
                            <label>Y-Offset (px)</label>
                            <input type="number" id="yOffset" value="0" min="-50" max="50" step="1">
                        </div>
                        <div class="slider-control">
                            <label>Dither Threshold</label>
                            <input type="range" id="ditherThreshold" value="128" min="0" max="255" step="1" oninput="updateDitherValue()">
                            <div class="slider-value" id="ditherValue">128</div>
                        </div>
                    </div>
                    <div style="margin-top: 15px;">
                        <label><input type="checkbox" id="enableDitherGlobal" checked onchange="toggleDitherControls()"> Floyd-Steinberg Dithering aktivieren</label>
                        <div id="ditherControls" style="margin-top: 10px;">
                            <div class="slider-control" style="display: inline-block; margin-right: 20px;">
                                <label>Dithering-Stärke</label>
                                <input type="range" id="ditherStrength" value="1.0" min="0.1" max="2.0" step="0.1" oninput="updateDitherStrengthValue()">
                                <div class="slider-value" id="ditherStrengthValue">1.0</div>
                            </div>
                            <div class="slider-control" style="display: inline-block;">
                                <label>Kontrast-Verstärkung</label>
                                <input type="range" id="contrastBoost" value="1.0" min="0.5" max="2.0" step="0.1" oninput="updateContrastValue()">
                                <div class="slider-value" id="contrastValue">1.0</div>
                            </div>
                        </div>
                    </div>
                    <button class="btn" onclick="saveSettings()">💾 Einstellungen speichern</button>
                    <button class="btn btn-warning" onclick="testOffsets()">📐 Offsets testen</button>
                </div>
            </div>
        </div>
        
        <!-- Main Content -->
        <div class="grid">
            <!-- Text Printing -->
            <div class="card">
                <h2>📝 Text drucken</h2>
                <textarea id="textInput" rows="4" placeholder="Text eingeben..." oninput="debouncedTextPreview()">PHOMEMO M110
Enhanced Edition
X-Offset: 0px
✓ Bildvorschau
Zeit: $TIME$</textarea>
                
                <div class="grid" style="gap: 10px; margin: 10px 0;">
                    <div>
                        <label>Schriftgröße:</label>
                        <select id="fontSize" onchange="updateTextPreview()">
                            <option value="18">Klein (18px)</option>
                            <option value="22" selected>Normal (22px)</option>
                            <option value="26">Groß (26px)</option>
                            <option value="30">Extra Groß (30px)</option>
                        </select>
                    </div>
                    <div>
                        <label>Textausrichtung:</label>
                        <select id="textAlignment" onchange="updateTextPreview()">
                            <option value="left">📍 Linksbündig</option>
                            <option value="center" selected>📄 Zentriert</option>
                            <option value="right">📍 Rechtsbündig</option>
                        </select>
                    </div>
                </div>
                
                <!-- Text Preview -->
                <div class="preview-container" id="textPreviewContainer" style="margin: 15px 0;">
                    <div id="textPreviewPlaceholder">
                        📝 Text-Vorschau<br>
                        <small>Tippe Text ein, um Vorschau zu sehen</small>
                    </div>
                    <img id="textPreviewImage" class="preview-image" style="display: none;">
                    <div id="textInfo" class="image-info" style="display: none;"></div>
                </div>
                
                <button class="btn" onclick="printText(false)">🖨️ Sofort drucken</button>
                <button class="btn btn-success" onclick="printText(true)">📤 In Queue</button>
            </div>
            
            <!-- Image Printing with Preview -->
            <div class="card">
                <h2>🖼️ Bild drucken mit Vorschau</h2>
                <input type="file" id="imageFile" accept="image/*" onchange="uploadAndPreview()">
                
                <div class="preview-container" id="previewContainer">
                    <div id="previewPlaceholder">
                        📁 Bild auswählen für Schwarz-Weiß-Vorschau<br>
                        <small>Unterstützte Formate: PNG, JPEG, BMP, GIF, WebP</small>
                    </div>
                    <img id="previewImage" class="preview-image" style="display: none;">
                </div>
                
                <div id="imageInfo" class="image-info" style="display: none;"></div>
                
                <div class="config-section">
                    <div class="config-title">🎛️ Bildoptionen</div>
                    <div class="image-options">
                        <label><input type="checkbox" id="fitToLabel" checked onchange="updatePreview()"> An Label anpassen (40×30mm)</label>
                        <label><input type="checkbox" id="maintainAspect" checked onchange="updatePreview()"> Seitenverhältnis beibehalten</label>
                        <label><input type="checkbox" id="enableDither" checked onchange="toggleImageDither()"> Dithering aktivieren</label>
                    </div>
                    
                    <div style="margin-top: 15px;">
                        <label style="display: block; margin-bottom: 10px;"><strong>📐 Skalierungsmodus:</strong></label>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                            <label><input type="radio" name="scalingMode" value="fit_aspect" checked onchange="updatePreview(); updateScalingModeHelp();"> 📏 Seitenverhältnis beibehalten</label>
                            <label><input type="radio" name="scalingMode" value="stretch_full" onchange="updatePreview(); updateScalingModeHelp();"> 🔄 Volle Größe (stretchen)</label>
                            <label><input type="radio" name="scalingMode" value="crop_center" onchange="updatePreview(); updateScalingModeHelp();"> ✂️ Zentriert zuschneiden</label>
                            <label><input type="radio" name="scalingMode" value="pad_center" onchange="updatePreview(); updateScalingModeHelp();"> 🖼️ Zentriert mit Rand</label>
                        </div>
                        <div style="margin-top: 5px; font-size: 12px; color: #666;">
                            <div id="scalingModeHelp">📏 Behält Seitenverhältnis bei, kann Ränder hinterlassen</div>
                        </div>
                    </div>
                    
                    <div id="imageDitherControls" style="margin-top: 15px;">
                        <div class="grid" style="gap: 10px;">
                            <div class="slider-control">
                                <label>🎚️ Dither Threshold</label>
                                <input type="range" id="imageDitherThreshold" value="128" min="0" max="255" step="1" oninput="updateImageDitherValue(); updatePreview();">
                                <div class="slider-value" id="imageDitherValue">128</div>
                            </div>
                            <div class="slider-control">
                                <label>⚡ Dither Stärke</label>
                                <input type="range" id="imageDitherStrength" value="1.0" min="0.1" max="2.0" step="0.1" oninput="updateImageDitherStrengthValue(); updatePreview();">
                                <div class="slider-value" id="imageDitherStrengthValue">1.0</div>
                            </div>
                        </div>
                        <div style="margin-top: 10px;">
                            <button class="btn" onclick="presetDither('soft')" style="font-size: 12px; padding: 5px 10px;">🌙 Weich</button>
                            <button class="btn" onclick="presetDither('normal')" style="font-size: 12px; padding: 5px 10px;">⚖️ Normal</button>
                            <button class="btn" onclick="presetDither('sharp')" style="font-size: 12px; padding: 5px 10px;">🔪 Scharf</button>
                            <button class="btn" onclick="presetDither('high_contrast')" style="font-size: 12px; padding: 5px 10px;">🔥 Kontrast</button>
                        </div>
                    </div>
                </div>
                
                <button class="btn" onclick="printImage(false)" id="printImageBtn" disabled>🖨️ Sofort drucken</button>
                <button class="btn btn-success" onclick="printImage(true)" id="queueImageBtn" disabled>📤 In Queue</button>
            </div>
        </div>
        
        <div id="status"></div>
    </div>

    <script>
        let currentImageData = null;
        
        // ==================== THEME MANAGEMENT ====================
        // Theme initialization
        function initTheme() {
            const savedTheme = localStorage.getItem('phomemo-theme');
            const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
            const theme = savedTheme || (prefersDark ? 'dark' : 'light');
            
            document.documentElement.setAttribute('data-theme', theme);
            updateThemeButton(theme);
        }
        
        // Toggle theme
        function toggleTheme() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('phomemo-theme', newTheme);
            updateThemeButton(newTheme);
            
            // Show feedback
            showStatus(newTheme === 'dark' ? '🌙 Dark Mode aktiviert' : '☀️ Light Mode aktiviert', 'info');
        }
        
        // Update theme button appearance
        function updateThemeButton(theme) {
            const button = document.querySelector('.theme-toggle');
            if (button) {
                button.textContent = theme === 'dark' ? '☀️' : '🌙';
                button.title = theme === 'dark' ? 'Light Mode aktivieren' : 'Dark Mode aktivieren';
            }
        }
        
        // Listen for system theme changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
                if (!localStorage.getItem('phomemo-theme')) {
                    const theme = e.matches ? 'dark' : 'light';
                    document.documentElement.setAttribute('data-theme', theme);
                    updateThemeButton(theme);
                }
            });
        }
        
        // Initialize theme on page load
        document.addEventListener('DOMContentLoaded', initTheme);
        
        function checkConnection() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    updateConnectionStatus(data);
                    updateSettings(data.settings || {});
                    updateStats(data.stats || {});
                })
                .catch(error => showStatus('❌ Verbindungsfehler: ' + error, 'error'));
        }
        
        function updateConnectionStatus(data) {
            const statusClass = data.connected ? 'status-connected' : 'status-disconnected';
            const statusText = data.connected ? '✅ Drucker verbunden' : '❌ Drucker nicht verbunden';
            
            let statusDetails = '';
            if (data.connected) {
                statusDetails = `RFCOMM Prozess: ${data.rfcomm_process_running ? '✅ Läuft' : '❌ Gestoppt'}<br>`;
                statusDetails += `Letzter Heartbeat: ${data.last_heartbeat ? new Date(data.last_heartbeat * 1000).toLocaleTimeString() : 'Nie'}`;
            } else {
                statusDetails = `Verbindungsversuche: ${data.connection_attempts || 0}<br>`;
                statusDetails += `Status: ${data.status || 'unbekannt'}`;
            }
                
            document.getElementById('connectionStatus').innerHTML = `
                <div class="${data.connected ? 'success' : 'error'}">
                    <span class="status-indicator ${statusClass}"></span>
                    ${statusText}<br>
                    <small>${statusDetails}</small>
                </div>
            `;
        }
        
        function updateSettings(settings) {
            document.getElementById('xOffset').value = settings.x_offset || 40;
            document.getElementById('yOffset').value = settings.y_offset || 0;
            document.getElementById('ditherThreshold').value = settings.dither_threshold || 128;
            document.getElementById('enableDitherGlobal').checked = settings.dither_enabled !== false;
            
            // Update slider values
            updateDitherValue();
            updateDitherStrengthValue();
            updateContrastValue();
        }
        
        function updateStats(stats) {
            // Diese Funktion kann erweitert werden wenn Stats angezeigt werden sollen
            if (stats) {
                console.log('Stats updated:', stats);
            }
        }
        
        function saveSettings() {
            const settings = {
                x_offset: parseInt(document.getElementById('xOffset').value),
                y_offset: parseInt(document.getElementById('yOffset').value),
                dither_threshold: parseInt(document.getElementById('ditherThreshold').value),
                dither_enabled: document.getElementById('enableDitherGlobal').checked,
                dither_strength: parseFloat(document.getElementById('ditherStrength').value),
                contrast_boost: parseFloat(document.getElementById('contrastBoost').value)
            };
            
            fetch('/api/settings', { 
                method: 'POST', 
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(settings)
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus('✅ Einstellungen gespeichert!', 'success');
                    } else {
                        showStatus('❌ Fehler beim Speichern: ' + (data.error || ''), 'error');
                    }
                })
                .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
        }
        
        // Schieberegler-Update-Funktionen
        function updateDitherValue() {
            const value = document.getElementById('ditherThreshold').value;
            document.getElementById('ditherValue').textContent = value;
            document.getElementById('imageDitherThreshold').value = value;
            document.getElementById('imageDitherValue').textContent = value;
            updatePreview();
        }
        
        function updateDitherStrengthValue() {
            const value = document.getElementById('ditherStrength').value;
            document.getElementById('ditherStrengthValue').textContent = value;
        }
        
        function updateContrastValue() {
            const value = document.getElementById('contrastBoost').value;
            document.getElementById('contrastValue').textContent = value;
        }
        
        function updateImageDitherValue() {
            const value = document.getElementById('imageDitherThreshold').value;
            document.getElementById('imageDitherValue').textContent = value;
            document.getElementById('ditherThreshold').value = value;
            document.getElementById('ditherValue').textContent = value;
        }
        
        function updateImageDitherStrengthValue() {
            const value = document.getElementById('imageDitherStrength').value;
            document.getElementById('imageDitherStrengthValue').textContent = value;
        }
        
        function toggleDitherControls() {
            const enabled = document.getElementById('enableDitherGlobal').checked;
            const controls = document.getElementById('ditherControls');
            controls.style.display = enabled ? 'block' : 'none';
            
            // Bildbereich auch aktualisieren
            document.getElementById('enableDither').checked = enabled;
            toggleImageDither();
        }
        
        function toggleImageDither() {
            const enabled = document.getElementById('enableDither').checked;
            const controls = document.getElementById('imageDitherControls');
            controls.style.display = enabled ? 'block' : 'none';
            updatePreview();
        }
        
        // Dithering-Presets
        function presetDither(preset) {
            const thresholdSlider = document.getElementById('imageDitherThreshold');
            const strengthSlider = document.getElementById('imageDitherStrength');
            
            switch(preset) {
                case 'soft':
                    thresholdSlider.value = 100;
                    strengthSlider.value = 0.5;
                    break;
                case 'normal':
                    thresholdSlider.value = 128;
                    strengthSlider.value = 1.0;
                    break;
                case 'sharp':
                    thresholdSlider.value = 150;
                    strengthSlider.value = 1.5;
                    break;
                case 'high_contrast':
                    thresholdSlider.value = 180;
                    strengthSlider.value = 2.0;
                    break;
            }
            
            updateImageDitherValue();
            updateImageDitherStrengthValue();
            updatePreview();
            showStatus(`🎨 Preset "${preset}" angewendet`, 'info');
        }
        
        function uploadAndPreview() {
            const fileInput = document.getElementById('imageFile');
            const file = fileInput.files[0];
            
            if (!file) return;
            
            // Aktuellen Skalierungsmodus ermitteln
            const scalingModeRadios = document.getElementsByName('scalingMode');
            let selectedScalingMode = 'fit_aspect'; // Default
            for (let radio of scalingModeRadios) {
                if (radio.checked) {
                    selectedScalingMode = radio.value;
                    break;
                }
            }
            
            const formData = new FormData();
            formData.append('image', file);
            formData.append('fit_to_label', document.getElementById('fitToLabel').checked);
            formData.append('maintain_aspect', document.getElementById('maintainAspect').checked);
            formData.append('enable_dither', document.getElementById('enableDither').checked);
            formData.append('dither_threshold', document.getElementById('imageDitherThreshold').value);
            formData.append('dither_strength', document.getElementById('imageDitherStrength').value);
            formData.append('scaling_mode', selectedScalingMode); // ← DIESER PARAMETER FEHLTE!
            
            showStatus('🔄 Erstelle Vorschau...', 'info');
            
            fetch('/api/preview-image', { method: 'POST', body: formData })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('previewPlaceholder').style.display = 'none';
                        const previewImg = document.getElementById('previewImage');
                        previewImg.src = 'data:image/png;base64,' + data.preview_base64;
                        previewImg.style.display = 'block';
                        
                        document.getElementById('imageInfo').innerHTML = 
                            `📏 <strong>Original:</strong> ${data.info.original_width} × ${data.info.original_height} px<br>` +
                            `📐 <strong>Verarbeitet:</strong> ${data.info.processed_width} × ${data.info.processed_height} px<br>` +
                            `📍 <strong>Offsets:</strong> X=${data.info.x_offset}px, Y=${data.info.y_offset}px<br>` +
                            `🎨 <strong>Dithering:</strong> ${data.info.dither_enabled ? 'Ein' : 'Aus'} (Threshold: ${data.info.dither_threshold})`;
                        document.getElementById('imageInfo').style.display = 'block';
                        
                        document.getElementById('printImageBtn').disabled = false;
                        document.getElementById('queueImageBtn').disabled = false;
                        currentImageData = file;
                        showStatus('✅ Vorschau erstellt!', 'success');
                    } else {
                        showStatus('❌ Vorschau-Fehler: ' + (data.error || ''), 'error');
                    }
                })
                .catch(error => showStatus('❌ Vorschau-Fehler: ' + error, 'error'));
        }
        
        function updatePreview() {
            if (currentImageData) {
                uploadAndPreview();
            }
        }
        
        function printText(useQueue) {
            const text = document.getElementById('textInput').value;
            const fontSize = document.getElementById('fontSize').value;
            const alignment = document.getElementById('textAlignment').value;
            
            if (!text.trim()) {
                showStatus('❌ Bitte Text eingeben!', 'error');
                return;
            }
            
            const finalText = text.replace('$TIME$', new Date().toLocaleTimeString());
            
            const formData = new FormData();
            formData.append('text', finalText);
            formData.append('font_size', fontSize);
            formData.append('alignment', alignment);
            formData.append('immediate', useQueue ? 'false' : 'true');
            
            showStatus(`🖨️ Drucke Text (${alignment})...`, 'info');
            
            fetch('/api/print-text', { method: 'POST', body: formData })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus('✅ Text gedruckt!', 'success');
                    } else {
                        showStatus('❌ Druckfehler: ' + (data.error || ''), 'error');
                    }
                })
                .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
        }
        
        // ==================== TEXT PREVIEW FUNCTIONS ====================
        function updateTextPreview() {
            const text = document.getElementById('textInput').value;
            const fontSize = document.getElementById('fontSize').value;
            const alignment = document.getElementById('textAlignment').value;
            
            // Leeren Text behandeln
            if (!text.trim()) {
                document.getElementById('textPreviewPlaceholder').style.display = 'block';
                document.getElementById('textPreviewImage').style.display = 'none';
                document.getElementById('textInfo').style.display = 'none';
                return;
            }
            
            const formData = new FormData();
            formData.append('text', text);
            formData.append('font_size', fontSize);
            formData.append('alignment', alignment);
            
            fetch('/api/preview-text', { method: 'POST', body: formData })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('textPreviewPlaceholder').style.display = 'none';
                        const previewImg = document.getElementById('textPreviewImage');
                        previewImg.src = 'data:image/png;base64,' + data.preview_base64;
                        previewImg.style.display = 'block';
                        
                        document.getElementById('textInfo').innerHTML = 
                            `📏 <strong>Größe:</strong> ${data.info.width} × ${data.info.height} px<br>` +
                            `📝 <strong>Text:</strong> "${data.info.text}"<br>` +
                            `🔤 <strong>Schrift:</strong> ${data.info.font_size}px, ${data.info.alignment}<br>` +
                            `📍 <strong>Offsets:</strong> X=${data.info.x_offset}px, Y=${data.info.y_offset}px`;
                        document.getElementById('textInfo').style.display = 'block';
                    } else {
                        showStatus('❌ Text-Vorschau Fehler: ' + (data.error || ''), 'error');
                    }
                })
                .catch(error => {
                    console.log('Text preview error:', error);
                    // Fehler still ignorieren für bessere UX
                });
        }
        
        // Debounce-Funktion für bessere Performance
        let textPreviewTimeout;
        function debouncedTextPreview() {
            clearTimeout(textPreviewTimeout);
            textPreviewTimeout = setTimeout(updateTextPreview, 300); // 300ms Delay
        }
        
        function printImage(useQueue) {
            if (!currentImageData) {
                showStatus('❌ Kein Bild ausgewählt!', 'error');
                return;
            }
            
            // Aktuellen Skalierungsmodus ermitteln
            const scalingModeRadios = document.getElementsByName('scalingMode');
            let selectedScalingMode = 'fit_aspect'; // Default
            for (let radio of scalingModeRadios) {
                if (radio.checked) {
                    selectedScalingMode = radio.value;
                    break;
                }
            }
            
            const formData = new FormData();
            formData.append('image', currentImageData);
            formData.append('immediate', useQueue ? 'false' : 'true');
            formData.append('fit_to_label', document.getElementById('fitToLabel').checked);
            formData.append('maintain_aspect', document.getElementById('maintainAspect').checked);
            formData.append('enable_dither', document.getElementById('enableDither').checked);
            formData.append('dither_threshold', document.getElementById('imageDitherThreshold').value);
            formData.append('dither_strength', document.getElementById('imageDitherStrength').value);
            formData.append('scaling_mode', selectedScalingMode); // ← DIESER PARAMETER FEHLTE AUCH HIER!
            
            showStatus('🖨️ Drucke Bild...', 'info');
            
            fetch('/api/print-image', { method: 'POST', body: formData })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus('✅ Bild gedruckt!', 'success');
                    } else {
                        showStatus('❌ Druckfehler: ' + (data.error || ''), 'error');
                    }
                })
                .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
        }
        
        function forceReconnect() {
            showStatus('🔄 Reconnect...', 'info');
            fetch('/api/force-reconnect', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus('✅ Reconnect erfolgreich!', 'success');
                        checkConnection();
                    } else {
                        showStatus('❌ Reconnect fehlgeschlagen', 'error');
                    }
                })
                .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
        }
        
        function manualConnect() {
            showStatus('🔧 Manuelle Verbindung...', 'info');
            fetch('/api/manual-connect', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus('✅ Manuelle Verbindung erfolgreich!', 'success');
                        checkConnection();
                    } else {
                        showStatus('❌ Manuelle Verbindung fehlgeschlagen', 'error');
                    }
                })
                .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
        }
        
        function testOffsets() {
            showStatus('📐 Teste Offsets...', 'info');
            fetch('/api/test-offsets', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus('✅ Offset-Test gedruckt!', 'success');
                    } else {
                        showStatus('❌ Offset-Test fehlgeschlagen', 'error');
                    }
                })
                .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
        }
        
        function showStatus(message, type) {
            const statusDiv = document.getElementById('status');
            statusDiv.innerHTML = '<div class="status ' + type + '">' + message + '</div>';
            setTimeout(() => statusDiv.innerHTML = '', 5000);
        }
        
        // Hilfetext für Skalierungsmodi aktualisieren
        function updateScalingModeHelp() {
            const scalingModeRadios = document.getElementsByName('scalingMode');
            const helpDiv = document.getElementById('scalingModeHelp');
            
            for (let radio of scalingModeRadios) {
                if (radio.checked) {
                    switch(radio.value) {
                        case 'fit_aspect':
                            helpDiv.innerHTML = '📏 Behält Seitenverhältnis bei, kann Ränder hinterlassen';
                            break;
                        case 'stretch_full':
                            helpDiv.innerHTML = '🔄 Streckt Bild auf volle Label-Größe, kann verzerren';
                            break;
                        case 'crop_center':
                            helpDiv.innerHTML = '✂️ Schneidet Bild zentriert zu, füllt Label vollständig';
                            break;
                        case 'pad_center':
                            helpDiv.innerHTML = '🖼️ Zentriert Bild mit weißem Rand, kein Zuschnitt';
                            break;
                        default:
                            helpDiv.innerHTML = '';
                    }
                    break;
                }
            }
        }
        
        // Auto-load
        window.onload = function() {
            checkConnection();
            
            // Dithering-Controls initial ausblenden/anzeigen
            toggleDitherControls();
            toggleImageDither();
            
            // Slider-Werte initial setzen
            updateDitherValue();
            updateDitherStrengthValue();
            updateContrastValue();
            
            // Hilfetext für Skalierungsmodus initial setzen
            updateScalingModeHelp();
            
            // Text-Vorschau initial laden
            setTimeout(updateTextPreview, 500); // Kurze Verzögerung für bessere UX
            updateImageDitherValue();
            updateImageDitherStrengthValue();
        };
    </script>
</body>
</html>
'''
