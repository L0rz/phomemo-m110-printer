"""
Erweitertes Web Interface Template für Phomemo M110
Mit Bildvorschau, X-Offset-Konfiguration und erweiterten Features
"""

WEB_INTERFACE_ENHANCED = '''
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
                        <div class="offset-control">
                            <label>Dither Threshold</label>
                            <input type="number" id="ditherThreshold" value="128" min="0" max="255" step="1">
                        </div>
                    </div>
                    <div style="margin-top: 15px;">
                        <label><input type="checkbox" id="enableDitherGlobal" checked> Floyd-Steinberg Dithering aktivieren</label>
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
                <textarea id="textInput" rows="4" placeholder="Text eingeben...">PHOMEMO M110\\nEnhanced Edition\\nX-Offset: 40px\\n✓ Bildvorschau\\nZeit: $TIME$</textarea>
                <select id="fontSize">
                    <option value="18">Klein (18px)</option>
                    <option value="22" selected>Normal (22px)</option>
                    <option value="26">Groß (26px)</option>
                </select>
                <br>
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
                        <label><input type="checkbox" id="enableDither" checked onchange="updatePreview()"> Dithering aktivieren</label>
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
        
        function checkConnection() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    const status = data.connected ? 
                        '<div class="success">✅ Drucker verbunden</div>' : 
                        '<div class="error">❌ Drucker nicht verbunden</div>';
                    document.getElementById('connectionStatus').innerHTML = status;
                })
                .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
        }
        
        function saveSettings() {
            const settings = {
                x_offset: parseInt(document.getElementById('xOffset').value),
                y_offset: parseInt(document.getElementById('yOffset').value),
                dither_threshold: parseInt(document.getElementById('ditherThreshold').value),
                dither_enabled: document.getElementById('enableDitherGlobal').checked
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
        
        function uploadAndPreview() {
            const fileInput = document.getElementById('imageFile');
            const file = fileInput.files[0];
            
            if (!file) return;
            
            const formData = new FormData();
            formData.append('image', file);
            formData.append('fit_to_label', document.getElementById('fitToLabel').checked);
            formData.append('maintain_aspect', document.getElementById('maintainAspect').checked);
            formData.append('enable_dither', document.getElementById('enableDither').checked);
            
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
                            `Original: ${data.info.original_width} × ${data.info.original_height} px<br>` +
                            `Verarbeitet: ${data.info.processed_width} × ${data.info.processed_height} px<br>` +
                            `X-Offset: ${data.info.x_offset} px, Y-Offset: ${data.info.y_offset} px`;
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
            
            if (!text.trim()) {
                showStatus('❌ Bitte Text eingeben!', 'error');
                return;
            }
            
            const finalText = text.replace('$TIME$', new Date().toLocaleTimeString());
            
            const formData = new FormData();
            formData.append('text', finalText);
            formData.append('font_size', fontSize);
            formData.append('immediate', useQueue ? 'false' : 'true');
            
            showStatus('🖨️ Drucke Text...', 'info');
            
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
        
        function printImage(useQueue) {
            if (!currentImageData) {
                showStatus('❌ Kein Bild ausgewählt!', 'error');
                return;
            }
            
            const formData = new FormData();
            formData.append('image', currentImageData);
            formData.append('immediate', useQueue ? 'false' : 'true');
            formData.append('fit_to_label', document.getElementById('fitToLabel').checked);
            formData.append('maintain_aspect', document.getElementById('maintainAspect').checked);
            formData.append('enable_dither', document.getElementById('enableDither').checked);
            
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
        
        // Auto-load
        window.onload = checkConnection;
    </script>
</body>
</html>
'''
