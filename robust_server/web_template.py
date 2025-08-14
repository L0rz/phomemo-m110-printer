"""
Web Interface Template für Phomemo M110 Robust Server
"""

WEB_INTERFACE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Phomemo M110 Drucker - Robust</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1000px; margin: 0 auto; }
        .card { background: white; padding: 20px; margin: 20px 0; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        .btn:hover { background: #0056b3; }
        .btn-success { background: #28a745; }
        .btn-success:hover { background: #1e7e34; }
        .btn-warning { background: #ffc107; color: #212529; }
        .btn-warning:hover { background: #e0a800; }
        .btn-danger { background: #dc3545; }
        .btn-danger:hover { background: #c82333; }
        textarea, input, select { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
        .status { padding: 15px; margin: 10px 0; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }
        @media (max-width: 768px) { .grid, .grid-3 { grid-template-columns: 1fr; } }
        .debug { background: #f8f9fa; border: 1px solid #dee2e6; padding: 10px; margin: 10px 0; border-radius: 5px; font-family: monospace; font-size: 12px; }
        .stats { display: flex; justify-content: space-around; text-align: center; }
        .stat-item { flex: 1; }
        .stat-value { font-size: 24px; font-weight: bold; color: #007bff; }
        .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
        .status-connected { background: #28a745; }
        .status-connecting { background: #ffc107; }
        .status-disconnected { background: #dc3545; }
        .status-failed { background: #6c757d; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🖨️ Phomemo M110 Drucker (Robust)</h1>
        
        <div class="card">
            <h2>🔗 Verbindungsstatus</h2>
            <div class="grid">
                <div>
                    <div id="connectionStatus"></div>
                    <button class="btn btn-success" onclick="checkConnection()">🔍 Status prüfen</button>
                    <button class="btn btn-warning" onclick="forceReconnect()">🔄 Force Reconnect</button>
                    <button class="btn btn-danger" onclick="clearQueue()">🗑️ Queue leeren</button>
                    <button class="btn" onclick="manualConnect()">🔧 Manual Connect</button>
                </div>
                <div>
                    <h3>📊 Statistiken</h3>
                    <div class="stats">
                        <div class="stat-item">
                            <div class="stat-value" id="totalJobs">0</div>
                            <div>Total Jobs</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value" id="successJobs">0</div>
                            <div>Erfolgreich</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value" id="failedJobs">0</div>
                            <div>Fehlgeschlagen</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value" id="queueSize">0</div>
                            <div>Queue</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="grid-3">
            <div class="card">
                <h2>📝 Text drucken</h2>
                <textarea id="textInput" rows="4" placeholder="Text eingeben...">PHOMEMO M110\\nRobust Connection\\n✓ Auto-Reconnect\\nZeit: $TIME$</textarea>
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
            
            <div class="card">
                <h2>🛠️ Debug & Test</h2>
                <button class="btn" onclick="testConnection()">🔧 Test Bluetooth</button>
                <button class="btn" onclick="initPrinter()">🔄 Init Drucker</button>
                <button class="btn" onclick="sendHeartbeat()">💓 Heartbeat</button>
                <div id="debugInfo" class="debug"></div>
            </div>
            
            <div class="card">
                <h2>📋 Print Queue</h2>
                <div id="queueInfo" class="debug"></div>
                <button class="btn" onclick="getQueueStatus()">🔄 Queue Status</button>
            </div>
        </div>
        
        <div class="card">
            <h2>📐 Kalibrierung & Ausrichtung</h2>
            <div class="grid">
                <div>
                    <h3>⚙️ Offset-Einstellungen</h3>
                    <label>X-Offset (Pixel):</label>
                    <input type="number" id="offsetX" value="0" min="-20" max="20" step="1">
                    
                    <label>Y-Offset (Pixel):</label>
                    <input type="number" id="offsetY" value="0" min="-20" max="20" step="1">
                    
                    <label>Rahmendicke (Pixel):</label>
                    <input type="number" id="borderThickness" value="2" min="1" max="5" step="1">
                </div>
                <div>
                    <h3>🎯 Kalibrierungs-Tests</h3>
                    <div class="grid">
                        <button class="btn" onclick="printCalibration('border')">🔲 Rahmen-Test</button>
                        <button class="btn" onclick="printCalibration('grid')">📐 Gitter-Test</button>
                        <button class="btn" onclick="printCalibration('rulers')">📏 Lineal-Test</button>
                        <button class="btn" onclick="printCalibration('corners')">📍 Ecken-Test</button>
                    </div>
                    <button class="btn btn-warning" onclick="printCalibration('series')" style="width: 100%; margin-top: 10px;">📊 Offset-Serie</button>
                </div>
            </div>
            <div id="calibrationInfo" class="debug" style="margin-top: 10px;"></div>
        </div>
        
        <div id="status"></div>
    </div>

    <script src="/static/app.js"></script>
</body>
</html>
'''
