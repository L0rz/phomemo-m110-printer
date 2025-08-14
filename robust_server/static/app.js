/*
JavaScript für Phomemo M110 Robust Server Web Interface
*/

let statusUpdateInterval;

function checkConnection() {
    showStatus('🔍 Prüfe Verbindung...', 'info');
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            updateConnectionDisplay(data);
            updateStats(data.stats);
        })
        .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
}

function updateConnectionDisplay(data) {
    const statusMap = {
        'connected': { icon: '✅', text: 'Verbunden', class: 'status-connected' },
        'connecting': { icon: '🔄', text: 'Verbinde...', class: 'status-connecting' },
        'reconnecting': { icon: '🔃', text: 'Reconnecting...', class: 'status-connecting' },
        'disconnected': { icon: '❌', text: 'Getrennt', class: 'status-disconnected' },
        'failed': { icon: '💀', text: 'Fehlgeschlagen', class: 'status-failed' }
    };
    
    const status = statusMap[data.status] || statusMap['disconnected'];
    
    const html = `
        <div class="status ${data.connected ? 'success' : 'error'}">
            <span class="status-indicator ${status.class}"></span>
            <strong>${status.icon} ${status.text}</strong><br>
            MAC: ${data.mac}<br>
            Device: ${data.device}<br>
            Connection Attempts: ${data.connection_attempts}<br>
            Last Success: ${data.last_successful ? new Date(data.last_successful).toLocaleString() : 'Never'}<br>
            Last Heartbeat: ${data.last_heartbeat ? new Date(data.last_heartbeat).toLocaleString() : 'Never'}<br>
            RFCOMM Process: ${data.rfcomm_process_running ? '✅ Running' : '❌ Stopped'}
        </div>
    `;
    
    document.getElementById('connectionStatus').innerHTML = html;
    document.getElementById('queueSize').textContent = data.queue_size;
}

function updateStats(stats) {
    if (stats) {
        document.getElementById('totalJobs').textContent = stats.total_jobs;
        document.getElementById('successJobs').textContent = stats.successful_jobs;
        document.getElementById('failedJobs').textContent = stats.failed_jobs;
    }
}

function forceReconnect() {
    showStatus('🔄 Force Reconnect...', 'info');
    fetch('/api/force-reconnect', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showStatus('✅ Reconnect erfolgreich!', 'success');
                setTimeout(checkConnection, 1000);
            } else {
                showStatus('❌ Reconnect fehlgeschlagen: ' + (data.error || ''), 'error');
            }
        })
        .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
}

function clearQueue() {
    if (confirm('Alle Jobs in der Queue löschen?')) {
        fetch('/api/clear-queue', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                showStatus('🗑️ Queue geleert', 'info');
                checkConnection();
            })
            .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
    }
}

function manualConnect() {
    showStatus('🔧 Manual Bluetooth Connect...', 'info');
    fetch('/api/manual-connect', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showStatus('✅ Manual connect erfolgreich!', 'success');
                document.getElementById('debugInfo').innerHTML = 
                    `Manual Connect: SUCCESS<br>` +
                    `Heartbeat: ${data.heartbeat_ok ? 'OK' : 'FAILED'}<br>` +
                    `Device Exists: ${data.device_exists}<br>` +
                    `Process Running: ${data.process_running}<br>` +
                    `Timestamp: ${new Date().toLocaleTimeString()}`;
                setTimeout(checkConnection, 1000);
            } else {
                showStatus('❌ Manual connect fehlgeschlagen: ' + (data.error || ''), 'error');
                document.getElementById('debugInfo').innerHTML = 
                    `Manual Connect: FAILED<br>` +
                    `Error: ${data.error}<br>` +
                    `Device Exists: ${data.device_exists || 'unknown'}<br>` +
                    `Process Running: ${data.process_running || 'unknown'}<br>` +
                    `Timestamp: ${new Date().toLocaleTimeString()}`;
            }
        })
        .catch(error => showStatus('❌ Manual connect error: ' + error, 'error'));
}

function printText(useQueue = false) {
    const text = document.getElementById('textInput').value;
    const fontSize = document.getElementById('fontSize').value;
    
    if (!text.trim()) {
        showStatus('❌ Bitte Text eingeben!', 'error');
        return;
    }
    
    // Replace $TIME$ placeholder
    const finalText = text.replace('$TIME$', new Date().toLocaleTimeString());
    
    const formData = new FormData();
    formData.append('text', finalText);
    formData.append('font_size', fontSize);
    formData.append('use_queue', useQueue);
    
    const action = useQueue ? 'zur Queue hinzufügen' : 'drucken';
    showStatus(`🖨️ ${action}...`, 'info');
    
    fetch('/api/print-text', { method: 'POST', body: formData })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const msg = useQueue ? 
                    `✅ Job ${data.job_id} zur Queue hinzugefügt!` : 
                    '✅ Text gedruckt!';
                showStatus(msg, 'success');
                setTimeout(checkConnection, 500);
            } else {
                showStatus('❌ Fehler: ' + (data.error || 'Unbekannter Fehler'), 'error');
            }
        })
        .catch(error => showStatus('❌ Fehler: ' + error, 'error'));
}

function testLabel() {
    document.getElementById('textInput').value = 
        'PHOMEMO M110\\nRobust Server\\n' + 
        new Date().toLocaleDateString() + '\\n' +
        new Date().toLocaleTimeString() + '\\n' +
        '✓ Test erfolgreich';
    printText(false);
}

function testConnection() {
    showStatus('🔧 Teste Bluetooth-Verbindung...', 'info');
    fetch('/api/test-connection', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            document.getElementById('debugInfo').innerHTML = 
                `Test Result: ${data.success}<br>` +
                `Message: ${data.message || ''}<br>` +
                `Error: ${data.error || 'None'}<br>` +
                `Response Time: ${data.response_time || 'N/A'}ms<br>` +
                `Timestamp: ${new Date().toLocaleTimeString()}`;
            
            if (data.success) {
                showStatus('✅ Bluetooth-Test erfolgreich!', 'success');
            } else {
                showStatus('❌ Bluetooth-Test fehlgeschlagen', 'error');
            }
        })
        .catch(error => showStatus('❌ Test-Fehler: ' + error, 'error'));
}

function initPrinter() {
    showStatus('🔄 Initialisiere Drucker...', 'info');
    fetch('/api/init-printer', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showStatus('✅ Drucker initialisiert!', 'success');
            } else {
                showStatus('❌ Init fehlgeschlagen: ' + (data.error || ''), 'error');
            }
        })
        .catch(error => showStatus('❌ Init-Fehler: ' + error, 'error'));
}

function sendHeartbeat() {
    showStatus('💓 Sende Heartbeat...', 'info');
    fetch('/api/heartbeat', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showStatus('✅ Heartbeat OK!', 'success');
                document.getElementById('debugInfo').innerHTML = 
                    `Heartbeat: OK<br>Response Time: ${data.response_time}ms<br>Timestamp: ${new Date().toLocaleTimeString()}`;
            } else {
                showStatus('❌ Heartbeat fehlgeschlagen', 'error');
            }
        })
        .catch(error => showStatus('❌ Heartbeat-Fehler: ' + error, 'error'));
}

function getQueueStatus() {
    fetch('/api/queue-status')
        .then(response => response.json())
        .then(data => {
            let html = `Queue Size: ${data.size}<br>Processor Running: ${data.running}<br><br>`;
            
            if (data.recent_jobs && data.recent_jobs.length > 0) {
                html += 'Recent Jobs:<br>';
                data.recent_jobs.forEach(job => {
                    const time = new Date(job.timestamp * 1000).toLocaleTimeString();
                    html += `${time} - ${job.job_type} (${job.status})<br>`;
                });
            } else {
                html += 'No recent jobs';
            }
            
            document.getElementById('queueInfo').innerHTML = html;
        })
        .catch(error => {
            document.getElementById('queueInfo').innerHTML = 'Error loading queue status';
        });
}

function printCalibration(mode) {
    const offsetX = document.getElementById('offsetX').value;
    const offsetY = document.getElementById('offsetY').value;
    const thickness = document.getElementById('borderThickness').value;
    
    const formData = new FormData();
    formData.append('offset_x', offsetX);
    formData.append('offset_y', offsetY);
    
    if (mode === 'border') {
        formData.append('thickness', thickness);
    } else if (mode === 'grid') {
        formData.append('spacing', '5');
    } else if (mode === 'corners') {
        formData.append('corner_size', '15');
    }
    
    const modeNames = {
        'border': 'Rahmen-Test',
        'grid': 'Gitter-Test',
        'rulers': 'Lineal-Test',
        'corners': 'Ecken-Test',
        'series': 'Offset-Serie'
    };
    
    showStatus(`📐 Drucke ${modeNames[mode]}...`, 'info');
    
    fetch(`/api/calibration/${mode}`, { method: 'POST', body: formData })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (mode === 'series') {
                    let resultMsg = `✅ ${data.message} abgeschlossen!<br>`;
                    data.results.forEach(result => {
                        const status = result.success ? '✅' : '❌';
                        resultMsg += `${status} Test ${result.test_number}: ${result.description}<br>`;
                    });
                    document.getElementById('calibrationInfo').innerHTML = resultMsg;
                    showStatus(`✅ ${data.message} erfolgreich!`, 'success');
                } else {
                    showStatus(`✅ ${data.message} gedruckt!`, 'success');
                    document.getElementById('calibrationInfo').innerHTML = 
                        `Letzter Test: ${data.message}<br>Bildgröße: ${data.image_size}<br>Timestamp: ${new Date().toLocaleTimeString()}`;
                }
            } else {
                showStatus(`❌ Kalibrierung fehlgeschlagen: ${data.error || 'Unbekannter Fehler'}`, 'error');
                document.getElementById('calibrationInfo').innerHTML = 
                    `Fehler: ${data.error}<br>Timestamp: ${new Date().toLocaleTimeString()}`;
            }
        })
        .catch(error => {
            showStatus(`❌ Kalibrierungs-Fehler: ${error}`, 'error');
            document.getElementById('calibrationInfo').innerHTML = 
                `Netzwerk-Fehler: ${error}<br>Timestamp: ${new Date().toLocaleTimeString()}`;
        });
}

function loadCalibrationInfo() {
    fetch('/api/calibration/info')
        .then(response => response.json())
        .then(data => {
            if (!data.error) {
                document.getElementById('calibrationInfo').innerHTML = 
                    `Drucker: ${data.printer_width_pixels}px (${data.printer_width_mm}mm)<br>` +
                    `Label: ${data.label_width_px}x${data.label_height_px}px (${data.label_width_mm}x${data.label_height_mm}mm)<br>` +
                    `Auflösung: ${data.pixels_per_mm.toFixed(1)} Pixel/mm<br>` +
                    `Modi: ${data.available_modes.join(', ')}`;
            }
        })
        .catch(error => {
            // Info ist optional, Fehler ignorieren
        });
}

function showStatus(message, type) {
    const statusDiv = document.getElementById('status');
    statusDiv.innerHTML = '<div class="status ' + type + '">' + message + '</div>';
    setTimeout(() => statusDiv.innerHTML = '', 8000);
}

function startStatusUpdates() {
    // Auto-update every 10 seconds
    statusUpdateInterval = setInterval(checkConnection, 10000);
}

function stopStatusUpdates() {
    if (statusUpdateInterval) {
        clearInterval(statusUpdateInterval);
    }
}

// Auto-check connection on load and start updates
window.onload = function() {
    checkConnection();
    getQueueStatus();
    loadCalibrationInfo();
    startStatusUpdates();
};

// Stop updates when page is hidden
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        stopStatusUpdates();
    } else {
        startStatusUpdates();
    }
});
