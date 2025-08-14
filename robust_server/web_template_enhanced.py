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
        
        /* Queue Display */
        .queue-info {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 10px;
            margin: 10px 0;
        }
        
        /* Loading Spinner */
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #007bff;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            animation: spin 2s linear infinite;
            display: inline-block;
            margin-right: 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Tooltips */
        .tooltip {
            position: relative;
            cursor: help;
        }
        .tooltip:hover::after {
            content: attr(title);
            position: absolute;
            bottom: 125%;
            left: 50%;
            transform: translateX(-50%);
            background: #333;
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 12px;
            white-space: nowrap;
            z-index: 1000;
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
                    <button class="btn btn-danger" onclick="clearQueue()">🗑️ Queue leeren</button>
                </div>
                <div class="config-section">
                    <div class="config-title">⚙️ Druckeinstellungen</div>
                    <div class="offset-controls">
                        <div class="offset-control">
                            <label>X-Offset (px)</label>
                            <input type="number" id="xOffset" value="40" min="0" max="100" step="1" 
                                   class="tooltip" title="Horizontale Verschiebung des Drucks (0-100 Pixel)">
                        </div>
                        <div class="offset-control">
                            <label>Y-Offset (px)</label>
                            <input type="number" id="yOffset" value="0" min="-50" max="50" step="1"
                                   class="tooltip" title="Vertikale Verschiebung des Drucks (-50 bis +50 Pixel)">
                        </div>
                        <div class="offset-control">
                            <label>Dither Threshold</label>
                            <input type="number" id="ditherThreshold" value="128" min="0" max="255" step="1"
                                   class="tooltip" title="Schwellenwert für Schwarz-Weiß-Konvertierung (0-255)">
                        </div>
                    </div>
                    <div style="margin-top: 15px;">
                        <label><input type="checkbox" id="enableDitherGlobal" checked> Floyd-Steinberg Dithering aktivieren</label>
                        <label><input type="checkbox" id="autoConnectGlobal" checked> Auto-Reconnect aktivieren</label>
                    </div>
                    <button class="btn" onclick="saveSettings()">💾 Einstellungen speichern</button>
                    <button class="btn btn-warning" onclick="testOffsets()">📐 Offsets testen</button>
                </div>
            </div>
            
            <!-- Statistics -->
            <h3>📊 Statistiken</h3>
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-value" id="totalJobs">0</div>
                    <div class="stat-label">Gesamt</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="successJobs">0</div>
                    <div class="stat-label">Erfolgreich</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="failedJobs">0</div>
                    <div class="stat-label">Fehlgeschlagen</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="queueSize">0</div>
                    <div class="stat-label">Queue</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="textJobs">0</div>
                    <div class="stat-label">Text</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="imageJobs">0</div>
                    <div class="stat-label">Bilder</div>
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
                    <option value="14">Sehr Klein (14px)</option>
                    <option value="18">Klein (18px)</option>
                    <option value="22" selected>Normal (22px)</option>
                    <option value="26">Groß (26px)</option>
                    <option value="30">Extra Groß (30px)</option>
                </select>
                <br>
                <button class="btn" onclick="printText(false)">🖨️ Sofort drucken</button>
                <button class="btn btn-success" onclick="printText(true)">📤 In Queue</button>
                <button class="btn btn-warning" onclick="testLabel()">🧪 Test Label</button>
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
        
        <!-- Calibration & Debug -->
        <div class="grid-3">
            <div class="card">
                <h2>📐 Kalibrierung</h2>
                <select id="calibrationPattern">
                    <option value="grid">Gitter-Muster</option>
                    <option value="lines">Linien-Muster</option>
                    <option value="full" selected>Vollständiger Test</option>
                </select>
                <div class="grid" style="margin: 10px 0;">
                    <div>
                        <label>Breite (px):</label>
                        <input type="number" id="calibWidth" value="320" min="50" max="400">
                    </div>
                    <div>
                        <label>Höhe (px):</label>
                        <input type="number" id="calibHeight" value="240" min="50" max="300">
                    </div>
                </div>
                <button class="btn" onclick="printCalibration()">🎯 Kalibrierung drucken</button>
                <button class="btn btn-warning" onclick="quickCalibration()">⚡ Quick Test</button>
            </div>
            
            <div class="card">
                <h2>🛠️ Debug & Test</h2>
                <button class="btn" onclick="testConnection()">🔧 Test Bluetooth</button>
                <button class="btn" onclick="initPrinter()">🔄 Init Drucker</button>
                <button class="btn" onclick="sendHeartbeat()">💓 Heartbeat</button>
                <div id="debugInfo" class="debug"></div>
            </div>
            
            <div class="card">
                <h2>📋 Print Queue</h2>
                <div id="queueInfo" class="queue-info"></div>
                <button class="btn" onclick="getQueueStatus()">🔄 Queue Status</button>
                <button class="btn btn-danger" onclick="clearQueue()">🗑️ Leeren</button>
            </div>
        </div>
        
        <div id="status"></div>
    </div>

    <script>
        let currentImageData = null;
        let currentSettings = {};
        
        // Initial load
        window.onload = function() {
            checkConnection();
            getQueueStatus();
            setInterval(updateStats, 30000); // Update stats every 30 seconds
        };
        
        function checkConnection() {
            showStatus('🔍 Prüfe Verbindung...', 'info');
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
            const statusDetails = data.connected ? 
                `Letzter Heartbeat: ${data.last_heartbeat ? new Date(data.last_heartbeat * 1000).toLocaleTimeString() : 'Nie'}` :
                `Verbindungsversuche: ${data.connection_attempts || 0}`;
                
            document.getElementById('connectionStatus').innerHTML = `
                <div class="${data.connected ? 'success' : 'error'}">
                    <span class="status-indicator ${statusClass}"></span>
                    ${statusText}<br>
                    <small>${statusDetails}</small>
                </div>
            `;
        }
        
        function updateSettings(settings) {
            currentSettings = settings;
            document.getElementById('xOffset').value = settings.x_offset || 40;
            document.getElementById('yOffset').value = settings.y_offset || 0;
            document.getElementById('ditherThreshold').value = settings.dither_threshold || 128;
            document.getElementById('enableDitherGlobal').checked = settings.dither_enabled !== false;
            document.getElementById('autoConnectGlobal').checked = settings.auto_connect !== false;
        }
        
        function updateStats(stats) {
            document.getElementById('totalJobs').textContent = stats.total_jobs || 0;
            document.getElementById('successJobs').textContent = stats.successful_jobs || 0;
            document.getElementById('failedJobs').textContent = stats.failed_jobs || 0;
            document.getElementById('textJobs').textContent = stats.text_jobs || 0;
            document.getElementById('imageJobs').textContent = stats.images_processed || 0;
        }
        
        function saveSettings() {
            const settings = {
                x_offset: parseInt(document.getElementById('xOffset').value),
                y_offset: parseInt(document.getElementById('yOffset').value),
                dither_threshold: parseInt(document.getElementById('ditherThreshold').value),
                dither_enabled: document.getElementById('enableDitherGlobal').checked,
                auto_connect: document.getElementById('autoConnectGlobal').checked,
                fit_to_label_default: document.getElementById('fitToLabel').checked,
                maintain_aspect_default: document.getElementById('maintainAspect').checked
            };
            
            showStatus('💾 Speichere Einstellungen...', 'info');
            
            fetch('/api/settings', { 
                method: 'POST', 
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(settings)
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus('✅ Einstellungen gespeichert!', 'success');
                        updateSettings(data.settings);
                        updatePreview(); // Vorschau aktualisieren
                    } else {
                        showStatus('❌ Fehler beim Speichern: ' + (data.error || ''), 'error');
                    }
                })
                .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
        }
        
        function uploadAndPreview() {
            const fileInput = document.getElementById('imageFile');
            const file = fileInput.files[0];
            
            if (!file) {
                resetPreview();
                return;
            }
            
            // Datei-Validierung
            const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/bmp', 'image/gif', 'image/webp'];
            if (!allowedTypes.includes(file.type)) {
                showStatus('❌ Nicht unterstütztes Bildformat!', 'error');
                resetPreview();
                return;
            }
            
            if (file.size > 10 * 1024 * 1024) { // 10MB
                showStatus('❌ Datei zu groß! Maximum: 10MB', 'error');
                resetPreview();
                return;
            }
            
            generatePreview();
        }
        
        function generatePreview() {
            const fileInput = document.getElementById('imageFile');
            const file = fileInput.files[0];
            
            if (!file) return;
            
            const formData = new FormData();
            formData.append('image', file);
            formData.append('fit_to_label', document.getElementById('fitToLabel').checked);
            formData.append('maintain_aspect', document.getElementById('maintainAspect').checked);
            formData.append('enable_dither', document.getElementById('enableDither').checked);
            
            showStatus('🔄 Erstelle Vorschau...', 'info');
            document.getElementById('previewPlaceholder').innerHTML = '<div class="spinner"></div>Verarbeite Bild...';
            
            fetch('/api/preview-image', { method: 'POST', body: formData })
                .then(response => response.json())
                .then(data => {                        showStatus('❌ Init fehlgeschlagen: ' + (data.error || ''), 'error');
                    }
                })
                .catch(error => showStatus('❌ Init-Fehler: ' + error, 'error'));
        }
        
        function sendHeartbeat() {
            showStatus('💓 Sende Heartbeat...', 'info');
            fetch('/api/test-connection', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus('✅ Heartbeat erfolgreich!', 'success');
                        checkConnection(); // Status aktualisieren
                    } else {
                        showStatus('❌ Heartbeat fehlgeschlagen', 'error');
                    }
                })
                .catch(error => showStatus('❌ Heartbeat-Fehler: ' + error, 'error'));
        }
        
        function updateStats() {
            // Stats automatisch aktualisieren
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    if (data.stats) {
                        updateStats(data.stats);
                    }
                })
                .catch(error => console.error('Stats update error:', error));
        }
        
        function showStatus(message, type) {
            const statusDiv = document.getElementById('status');
            statusDiv.innerHTML = '<div class="status ' + type + '">' + message + '</div>';
            setTimeout(() => statusDiv.innerHTML = '', 8000);
        }
        
        // Auto-updates
        setInterval(() => {
            getQueueStatus();
            updateStats();
        }, 15000); // Alle 15 Sekunden
        
        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.key === 'Enter') {
                // Ctrl+Enter für Text drucken
                printText(false);
            } else if (e.ctrlKey && e.shiftKey && e.key === 'Enter') {
                // Ctrl+Shift+Enter für Text in Queue
                printText(true);
            } else if (e.key === 'F5') {
                e.preventDefault();
                checkConnection();
            }
        });
    </script>
</body>
</html>
'''
